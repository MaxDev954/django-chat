const dashboard = document.getElementById("chat-dashboard") || document.body;
const hiddenInput = document.getElementById('user-id')
const chatWsUrl = dashboard.dataset?.chatUrl || 'default';


let socket = new WebSocket(chatWsUrl);
let users = [];
let currentUserId = hiddenInput.dataset.userId;

let messages = [];

socket.onopen = function (event) {
    console.log('WebSocket connected');
};

socket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    console.log(data);

    switch (data.type) {
        case 'history':
            messages = data.messages || [];
            displayMessages();
            break;

        case 'user_list':
            users = data.users || [];
            displayUsers();
            break;

        case 'user_status':
            handleUserStatus(data);
            break;

        case 'message':
            addMessage(data);
            break;
        case 'error_message':
            showNotification(data.text)
            break;
    }
};

socket.onclose = function (event) {
    console.log('WebSocket disconnected');
};

socket.onerror = function (error) {
    console.error('WebSocket error:', error);
};

function showNotification(message, type = 'error') {
    const notifier = document.getElementById('notifier');
    
    notifier.className = 'notifier';
    
    if (type === 'error') {
        notifier.classList.add('error');
    } else if (type === 'success') {
        notifier.classList.add('success');
    }
    
    notifier.textContent = message;
    
    notifier.classList.add('show');
    
    setTimeout(() => {
        notifier.classList.remove('show');
    }, 3000);
}


function displayUsers() {
    const usersContainer = document.getElementById('users-container');
    usersContainer.innerHTML = '';

    users.forEach(user => {
        const userCard = createUserCard(user);
        usersContainer.appendChild(userCard);
    });

    if (!currentUserId) {
        currentUserId = users[0].id
    }
}

function createUserCard(user) {
    const userCard = document.createElement('div');
    userCard.className = 'user-card';

    const initials = getInitials(user.first_name, user.last_name);

    userCard.innerHTML = `
                <div class="user-avatar" style="background-color: ${user.color || '#FF5E5B'}">${initials}</div>
                <div class="user-info">
                    <h3>${user.first_name} ${user.last_name}</h3>
                    <p>${user.email}</p>
                </div>
            `;

    return userCard;
}

function getInitials(firstName, lastName) {
    return (firstName?.[0] || '') + (lastName?.[0] || '');
}

function displayMessages() {
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';


    messages.forEach(msg => {
        const messageDiv = createMessageElement(msg);
        messagesContainer.appendChild(messageDiv);
    });

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function createMessageElement(msg) {
    const currentUser = msg.user
    const isOwnMessage = msg?.sender === +currentUserId;
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isOwnMessage ? 'own' : ''}`;

    const initials = getInitials(currentUser.first_name, currentUser.last_name);
    const displayName = isOwnMessage ? 'You' : `${currentUser.first_name} ${currentUser.last_name}`;

    messageDiv.innerHTML = `
                <div class="message-avatar" style="background-color: ${currentUser.color || '#FF5E5B'}">${initials}</div>
                <div class="message-content">
                    <div class="message-sender">${displayName}</div>
                    <div class="message-text">${msg.text}</div>
                </div>
            `;

    return messageDiv;
}

function addMessage(data) {
    messages.push(data);

    const user = users.find(u => u.id === data.sender);
    if (user) {
        const messagesContainer = document.getElementById('messages');
        const messageDiv = createMessageElement(data, user);
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

function handleUserStatus(data) {
    if (data.status === 'joined') {
        const existingUser = users.find(u => u.id === data.user.id);
        if (!existingUser) {
            users.push(data.user);
            displayUsers();
        }
    } else if (data.status === 'left') {
        users = users.filter(u => u.id !== data.user.id);
        displayUsers();
    }
}

function sendMessage() {
    const input = document.getElementById('messageInput');
    const text = input.value.trim();

    if (!text || !socket || socket.readyState !== WebSocket.OPEN) return;

    socket.send(JSON.stringify({
        text: text
    }));

    input.value = '';
    input.focus();
}

document.getElementById('messageInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
document.addEventListener('DOMContentLoaded', () => {
    const chatSelect = document.getElementById('chat-select');
    const joinButton = document.getElementById('join');
    const logoutButton = document.getElementById('logout');
    const roomForm = document.getElementById('room');
    const conversationUrl = document.getElementById('conversation').dataset.conversationUrl;

    async function loadConversations() {
        try {
            const response = await fetch('/api/conversation/');
            if (!response.ok) throw new Error('Failed to fetch conversations');
            const conversations = await response.json();

            chatSelect.innerHTML = '<option value="">Select a chat room...</option>';

            conversations.forEach(conv => {
                const option = document.createElement('option');
                option.value = conv.id;
                option.textContent = conv.title || `Room ${conv.id}`;
                chatSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading conversations:', error);
            chatSelect.innerHTML = '<option value="">Error loading rooms</option>';
        }
    }

    roomForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(roomForm);
        const title = formData.get('room');

        try {
            const response = await fetch('/api/conversation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ title }),
            });

            if (response.ok) {
                const data = await response.json()
                const convId = data.id
                await loadConversations(); 
                roomForm.reset(); 
                window.location.href = `/chat/room/${convId}`;
            
            } else {
                const errorData = await response.json();
                alert(`Failed to create room: ${errorData.detail}`);
            }
        } catch (error) {
            console.error('Error creating room:', error);
            alert('Failed to create room. Please try again.');
        }
    });

    joinButton.addEventListener('click', () => {
        const selectedRoom = chatSelect.value;
        if (selectedRoom) {
            window.location.href = `/chat/room/${selectedRoom}/`;
        } else {
            alert('Please select a chat room to join.');
        }
    });

    logoutButton.addEventListener('click', async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('/api/auth/logout/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            });
            if (response.ok) {
                window.location.href = '/login/';
            } else {
                throw new Error('Logout failed');
            }
        } catch (error) {
            console.error('Logout error:', error);
            alert('Failed to logout. Please try again.');
        }
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    loadConversations();
});
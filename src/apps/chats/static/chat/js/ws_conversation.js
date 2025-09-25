const hiddenInput = document.getElementById('conversation')
const wsConversationUrl = hiddenInput.dataset.conversationUrl
let socket = new WebSocket(wsConversationUrl);

socket.onopen = function (e) {
    console.log('ws connection')
};

socket.onmessage = function (event) {
    console.log("message from server:", event.data);
};

socket.onmessage = function (event) {
    console.log("message_resive:", event.data);

    let data = JSON.parse(event.data);

    if (data.conversations) {
        const select = document.getElementById("chat-select");
        const joinButton = document.getElementById("join");
        select.innerHTML = "";
        
        let conversation = data.conversations
        let revseredConversation = conversation.reverse()

        revseredConversation.forEach(conv => {
            const option = document.createElement("option");
            option.value = conv.id;
            option.textContent = conv.name;
            select.appendChild(option);
        });

        if (select && joinButton) {
            if (select.options.length > 0) {
                joinButton.href = `/chat/room/${select.options[0].value}/`;
            } else {
                joinButton.href = "#";
            }
        }

    }
};

socket.onerror = function (error) {
    console.error("Error WebSocket:", error);
};

socket.onclose = function (e) {
    console.log("Connection close", e);
};
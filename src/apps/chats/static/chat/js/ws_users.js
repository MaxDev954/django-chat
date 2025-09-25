const dashboard = document.getElementById("chat-dashboard");
const chatId = dashboard.dataset.chatId;
const HOST = '127.0.0.1:8000';

let socket = new WebSocket(`ws://${HOST}/ws/chat/${chatId}`);
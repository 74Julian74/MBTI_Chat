const socket = io();

document.getElementById('message-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value;
    if (message.trim()) {
        socket.emit('send_message', { message: message });
        messageInput.value = '';
    }
});

socket.on('receive_message', function(data) {
    const messageList = document.getElementById('message-list');
    const messageElement = document.createElement('div');
    messageElement.textContent = data.message;
    messageList.appendChild(messageElement);
});
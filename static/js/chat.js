document.addEventListener('DOMContentLoaded', function() {
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    var roomId = '{{ room_id }}'; // 假設你從後端傳遞了 room_id

    // 當用戶連接時觸發
    socket.on('connect', function() {
        console.log('Connected');
        socket.emit('join', {room: roomId});
    });

    // 當收到消息時觸發
    socket.on('message', function(data) {
        displayMessage(data.message, 'contact-messages');
    });

    // 整合後的發送消息功能
  function sendMessage() {
    var messageInput = document.querySelector('.label1');
    var msg = messageInput.value.trim();
    if (msg !== "") {
      socket.send(msg);
      displayMessage(msg, 'user-messages');
      messageInput.value = '';
    }
  }

    // 為輸入框添加事件監聽器
  document.querySelector('.label1').addEventListener('keypress', function(e) {
  if (e.key === 'Enter') {
    e.preventDefault(); // 防止默認的提交行為
    sendMessage();
  }
  });

    // 如果你有一個發送按鈕，你也可以為它添加事件監聽器
  var sendButton = document.getElementById('send-button'); // 假設你有一個發送按鈕
  if (sendButton) {
    sendButton.addEventListener('click', sendMessage);
  }
    

    // 顯示消息
    function displayMessage(msg, messageType) {
        var messages = document.getElementById('messages');
        var newMessage = document.createElement('div');
        newMessage.className = 'bubble ' + messageType;
        newMessage.innerHTML = `
            <div class="${messageType}">
            <div class="message-content">${msg}</div>
            <div class="timestamp">${formatTimeOnly(new Date())}</div>
          </div>;
        `;
        messages.appendChild(newMessage);
        messages.scrollTop = messages.scrollHeight;
    }

    function formatTimeOnly(date) {
        let hours = date.getHours();
        let minutes = date.getMinutes();
        const ampm = hours >= 12 ? '下午' : '上午';
        hours = hours % 12;
        hours = hours ? hours : 12;
        minutes = minutes < 10 ? '0' + minutes : minutes;
        return `${ampm} ${hours}:${minutes}`;
    }
});
document.addEventListener('DOMContentLoaded', () => {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messageList = document.getElementById('message-list');
    let currentRoomId = null;
    // Socket.IO 設置
    const socket = io();

    // 從 meta 標籤中獲取 CSRF 令牌
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    // 模擬的好友數據
    const friends = [
        { id: 1, name: '爸', lastMessage: '晚' },//, avatar: '/api/placeholder/40/40'
        { id: 2, name: '媽', lastMessage: '早' },//, avatar: '/api/placeholder/40/40'
        { id: 3, name: '謝程安(MaKaBaKa)', lastMessage: 'MAKABAKA' },//, avatar: '/api/placeholder/40/40'
        // 添加更多好友...
    ];

    // 渲染好友列表
    function renderFriendList() {
        friendList.innerHTML = friends.map(friend => `
            <div class="friend-item" data-id="${friend.id}">
                <img src="${friend.avatar}" alt="${friend.name}" class="friend-avatar">
                <div>
                    <div>${friend.name}</div>
                    <small>${friend.lastMessage}</small>
                </div>
            </div>
        `).join('');

        // 添加點擊事件
        friendList.querySelectorAll('.friend-item').forEach(item => {
            item.addEventListener('click', () => switchChat(item.dataset.id));
        });
    }

    // 切換聊天室
    function switchRoom(roomId) {
        currentRoomId = roomId;
        // 加入新房間
        socket.emit('join', {room: roomId});
        // 獲取最近的消息
        fetch(`/get_recent_messages/${roomId}`)
            .then(response => response.json())
            .then(messages => {
                messageList.innerHTML = '';
                messages.forEach(displayMessage);
            });
    }

    // 發送消息
    function sendMessage() {
        const content = messageInput.value.trim();
        if (content && currentRoomId) {
            // 發送消息到後端
            fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken':csrfToken
                },
                body: JSON.stringify({
                    room_id: currentRoomId,
                    content: content,
                    sender_id: 1 // 這裡需要替換為實際的用戶ID
                }),
            }).then(response => response.json())
              .then(data => {
                  if (data.status === 'success') {
                      messageInput.value = '';
                      // 可以在這裡立即在UI上顯示消息，不等待 Socket.IO 的廣播
                      displayMessage({
                          sender_id: 1,
                          content: content,
                          timestamp: getCurrentTime()
                      });
                  }
              });
        }
    }
    
    function formatDateToChinese(date) {
        const today = new Date();
        const yesterday = new Date();
        yesterday.setDate(today.getDate() - 1);
    
        // 檢查是否是今天
        if (date.toDateString() === today.toDateString()) {
            return '今天';
        }
        
        // 檢查是否是昨天
        if (date.toDateString() === yesterday.toDateString()) {
            return '昨天';
        }
    
        // 如果不是今天或昨天，則返回完整的日期格式
        const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
        return date.toLocaleDateString('zh-TW', options);
    }
    

    let lastMessageDate = null;
    function displayMessage(message) {
        const messageDate = new Date(message.timestamp).toDateString(); // 獲取訊息的日期
    
        if (lastMessageDate !== messageDate) {
            const dateSeparator = document.createElement('div');
            dateSeparator.className = 'date-separator';

            // 使用中文日期格式
            const dateFormatted = formatDateToChinese(new Date(message.timestamp));
            dateSeparator.textContent = dateFormatted;

            messageList.appendChild(dateSeparator);
            lastMessageDate = messageDate;
        }

        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.sender_id === 1 ? 'sent' : 'received'}`;
        
        const timeElement = document.createElement('div');
        timeElement.className = 'message-time';
        const messageTime = new Date(message.timestamp);
        timeElement.textContent = formatTimeOnly(messageTime);
        
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
        
        const bubbleElement = document.createElement('div');
        bubbleElement.className = 'message-bubble';
        bubbleElement.textContent = message.content;
        
        contentElement.appendChild(bubbleElement);
        
        messageElement.appendChild(timeElement);
        messageElement.appendChild(contentElement);
        
        messageList.appendChild(messageElement);
        messageList.scrollTop = messageList.scrollHeight;
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
    function getCurrentTime() {
        const now = new Date();
        return now.toISOString();
    }
    // Socket.IO 事件監聽
    socket.on('new_message', displayMessage);

    socket.on('connect', () => {
        console.log('Connected to Socket.IO server');
    });

    socket.on('message', (data) => {
        displayMessage(data.message, 'contact-messages');
    });

    socket.on('load_messages', (messages) => {
        messages.forEach(displayMessage);
    });

    // 事件監聽器
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 初始化
    switchRoom('default_room');
});
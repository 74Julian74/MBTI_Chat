document.addEventListener('DOMContentLoaded', () => {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messageList = document.getElementById('message-list');
    const chatTitle = document.getElementById('chat-title');
    let currentGroupId = null;
    let currentUserId= null;
    let userIdPromise= null;
    
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

    // 更新聊天標題的函數
    function updateChatTitle(name) {
        chatTitle.textContent = name || ''; // 如果没有名字，就设置为空字符串
    }

    // 獲取當前用戶ID的函數
    function fetchCurrentUserId() {
        if (userIdPromise) {
            return userIdPromise;
        }

        userIdPromise = fetch('/get_current_user_id')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch user ID');
                }
                return response.json();
            })
            .then(data => {
                currentUserId = data.user_id;
                console.log('Current User ID:', currentUserId);
                return currentUserId;
            })
            .catch(error => {
                console.error('Error fetching user ID:', error);
                // 重置 promise 以便下次重試
                userIdPromise = null;
                throw error;
            });

        return userIdPromise;
    }

    // 初始化
    function initialize() {
        fetchCurrentUserId()
            .then(() => {
                console.log('User ID fetched successfully');
                switchRoom('default_group'); // 初始化時載入 default_group
                renderFriendList(); // 确保在初始化时渲染好友列表
                startPolling(); // 開始定期輪詢
            })
            .catch(() => console.log('Failed to fetch user ID. User might not be logged in.'));
    }

    // 在頁面加載時調用
    document.addEventListener('DOMContentLoaded', () => {
        fetchCurrentUserId()
            .then(() => console.log('User ID fetched successfully'))
            .catch(() => console.log('Failed to fetch user ID. User might not be logged in.'));
    });

    // 渲染好友列表函數
    function renderFriendList() {
        const friendList = document.getElementById('friend-list');
        friendList.innerHTML = `
            <div class="friend-item" data-id="default_group">
                <div>聊天室</div>
            </div>
        ` + friends.map(friend => `
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
            item.addEventListener('click', () => switchRoom(item.dataset.id));
        });
    }

   // 切換聊天室函數
   function switchRoom(groupId) {
        currentGroupId = groupId;
        loadMessages(groupId);

        if (groupId === 'default_group') {
            updateChatTitle('聊天室');
        } else {
            // 找到對應的朋友名稱
            const friend = friends.find(f => f.id.toString() === groupId.toString());
            if (friend) {
                updateChatTitle(friend.name);
            } else {
                updateChatTitle('聊天室'); // 如果沒找到對應的朋友，顯示 '聊天室'
            }
        }
    }

    // 加載消息
    function loadMessages(groupId) {
        fetch(`/get_recent_messages/${groupId}`)
            .then(response => response.json())
            .then(messages => {
                messageList.innerHTML = '';
                messages.forEach(displayMessage);
            });
    }

    // 發送消息
    function sendMessage() {
        const content = messageInput.value.trim();
        if (!content || !currentGroupId) {
            console.error('無效的消息內容或群組ID');
            return;
        }
    
        fetchCurrentUserId()
            .then(userId => {
                if (!userId) {
                    throw new Error('User ID not available. Please ensure you are logged in.');
                }
                currentUserId = userId;
                const message = {
                    sender_id: currentUserId,
                    content: content,
                    timestamp: new Date().toISOString()
                };

                return fetch('/send_message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        group_id: currentGroupId,
                        content: content,
                        sender_id: userId
                    }),
                });
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('網絡響應不正常');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    messageInput.value = '';
                    const newMessage = {
                        sender_id: currentUserId,
                        content: content,
                        timestamp: new Date().toISOString()
                    };
                    //displayMessage(newMessage);
                    updateLastMessageTimestamp(newMessage.timestamp);
                } else {
                    throw new Error(data.message || '發送消息失敗');
                }
            })
            .catch(error => {
                console.error('Error:', error.message);
                alert(error.message);  // 顯示錯誤給用戶
            });
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
    
    function pollForNewMessages() {
        if (!currentGroupId) return;

        const lastMessageTimestamp = getLastMessageTimestamp();

        fetch(`/get_new_messages/${currentGroupId}?since=${encodeURIComponent(lastMessageTimestamp)}`)
            .then(response => response.json())
            .then(messages => {
                messages.forEach(displayMessage);
                if (messages.length > 0) {
                    const lastTimestamp = messages[messages.length - 1].timestamp;
                    updateLastMessageTimestamp(lastTimestamp);
                }
            })
            .catch(error => console.error('Error polling for new messages:', error));
    }

    const displayedMessageIds = new Set();

    function isMessageDisplayed(message) {
        const messageId = `${message.sender_id}-${message.timestamp}`;
        if (displayedMessageIds.has(messageId)) {
            return true;
        }
        displayedMessageIds.add(messageId);
        return false;
    }

    function getLastMessageTimestamp() {
        const lastMessage = messageList.lastElementChild;
        return lastMessage ? lastMessage.dataset.timestamp : new Date(0).toISOString();
    }

    function updateLastMessageTimestamp(timestamp) {
        lastMessageTimestamp = timestamp;
        if (messageList.lastElementChild) {
            messageList.lastElementChild.dataset.timestamp = timestamp;
        }
    }
    

    function getLocalISOString(date) {
        const offset = date.getTimezoneOffset();
        const localDate = new Date(date.getTime() - (offset*60*1000));
        return localDate.toISOString().split('Z')[0];
    }

    function getLastMessageTimestamp() {
        const lastMessage = messageList.lastElementChild;
        return lastMessage ? lastMessage.dataset.timestamp : getLocalISOString(new Date(0));
    }

    let lastMessageDate = null;
    function displayMessage(message) {
        const messageDate = new Date(message.timestamp).toDateString();
        
        if (isMessageDisplayed(message)) {
            return;
        }
    
        if (lastMessageDate !== messageDate) {
            const dateSeparator = document.createElement('div');
            dateSeparator.className = 'date-separator';
            const dateFormatted = formatDateToChinese(new Date(message.timestamp));
            dateSeparator.textContent = dateFormatted;
            messageList.appendChild(dateSeparator);
            lastMessageDate = messageDate;
        }
    
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.sender_id === currentUserId ? 'sent' : 'received'}`;
        
        const timeElement = document.createElement('div');
        timeElement.className = 'message-time';
        const messageTime = new Date(message.timestamp);
        timeElement.textContent = formatTimeOnly(messageTime);
        
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
        
        const bubbleElement = document.createElement('div');
        bubbleElement.className = 'message-bubble';
        
        // 添加发送者名称
        if (message.sender_id !== currentUserId) {
            const senderNameElement = document.createElement('div');
            senderNameElement.className = 'sender-name';
            senderNameElement.textContent = message.sender_name || 'Unknown'; // 使用sender_name或默认值
            bubbleElement.appendChild(senderNameElement);
        }
        
        const messageTextElement = document.createElement('div');
        messageTextElement.textContent = message.content;
        bubbleElement.appendChild(messageTextElement);
        
        contentElement.appendChild(bubbleElement);
        messageElement.dataset.timestamp = message.timestamp;
        
        // 调整时间元素的位置
        if (message.sender_id === currentUserId) {
            messageElement.appendChild(contentElement);
            messageElement.appendChild(timeElement);
        } else {
            messageElement.appendChild(contentElement);
            contentElement.appendChild(timeElement); // 将时间元素放在内容元素的右侧
        }
        
        messageList.appendChild(messageElement);
        messageList.scrollTop = messageList.scrollHeight;
    }

    // 設置定期輪詢，並添加錯誤處理
    function startPolling() {
        setInterval(() => {
            pollForNewMessages().catch(error => {
                console.error('Polling error:', error);
                // 可以在這裡添加重試邏輯或顯示錯誤消息給用戶
            });
        }, 5000);
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
        displayMessage(data.message);
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
    document.getElementById("replyone").addEventListener("click", function() {
    // 获取第一个建议回复的内容
    const suggestionContent1 = document.querySelector(".suggestion textarea").value;
    // 将第一个建议回复的内容复制到消息输入框中
    document.getElementById("message-input").value = suggestionContent1;
    });

    document.getElementById("relpytwo").addEventListener("click", function() {
        // 获取第二个建议回复的内容
        const suggestionContent2 = document.querySelectorAll(".suggestion textarea")[1].value;
        // 将第二个建议回复的内容复制到消息输入框中
        document.getElementById("message-input").value = suggestionContent2;
    });

    // 初始化
    initialize();
});
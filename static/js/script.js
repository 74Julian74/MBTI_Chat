document.addEventListener('DOMContentLoaded', () => {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const messageList = document.getElementById('message-list');
    const friendList = document.getElementById('friend-list');
    const chatTitle = document.getElementById('chat-title');
    let currentGroupId = null;
    let currentUserId= null;
    let userIdPromise= null;

    const userInfoMap = new Map();
    
    // Socket.IO 設置
    const socket = io();

    // 從 meta 標籤中獲取 CSRF 令牌
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');


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

    function renderFriendList() {
        fetch('/get_friends')
            .then(response => response.json())
            .then(friends => {
                friendList.innerHTML = `
                    <div class="friend-item" data-id="default_group">
                        <img src="/static/image/main2.png" alt="MBTI" class="friend-avatar">
                        <div class="friend-info">
                            <div class="friend-name">交誼廳</div>
                        </div>
                    </div>
                `;
    
                friends.forEach(friend => {
                    const friendElement = document.createElement('div');
                    friendElement.className = 'friend-item';
                    // 生成 GroupID
                    const groupId = `${Math.min(currentUserId, friend.id)}_${Math.max(currentUserId, friend.id)}`;
                    friendElement.dataset.id = groupId;
                    friendElement.innerHTML = `
                        <img src="/uploads/${friend.profile_picture}" alt="${friend.username}" class="friend-avatar">
                        <div class="friend-info">
                            <div class="friend-name">${friend.username}</div>
                        </div>
                    `;
                    friendList.appendChild(friendElement);
                    // 將用戶信息添加到映射中
                    userInfoMap.set(friend.id.toString(), {
                        username: friend.username,
                        avatarUrl: `/uploads/${friend.profile_picture}`
                    });
                });
    
                // 添加點擊事件
                friendList.querySelectorAll('.friend-item').forEach(item => {
                    item.addEventListener('click', () => {
                        const groupId = item.dataset.id;
                        const friendName = item.querySelector('.friend-name').textContent;
                        createOrSwitchChat(groupId, friendName);
                    });
                });
            })
            .catch(error => console.error('Error loading friend list:', error));
    }
    
    function createOrSwitchChat(groupId, friendName) {
        // 首先嘗試切換到現有聊天
        switchRoom(groupId, friendName);
    
        // 如果聊天不存在，則創建新的聊天
        fetch('/create_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                type: 'private',
                other_user_id: groupId.split('_').find(id => id !== currentUserId.toString())
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message === '聊天創建成功' || data.message === '聊天已存在') {
                switchRoom(groupId, friendName);
            } else {
                console.error('Failed to create chat:', data.error);
            }
        })
        .catch(error => console.error('Error creating chat:', error));
    }


    // 初始化
    function initialize() {
        fetchCurrentUserId()
            .then(() => {
                console.log('User ID fetched successfully');
                //switchRoom('default_group', '交誼廳'); // 初始化時載入 default_group
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

    function clearAnalysisContent() {
        //document.getElementById('person-name').textContent = '';
        document.getElementById('person-mbti').textContent = '';
        document.getElementById('person-emotion').textContent = '';
        document.getElementById('emotion-reason').textContent = '';
        document.getElementById('mbti-explanation').innerHTML = '';
        document.getElementById('suggestion-1').value = '';
        document.getElementById('suggestion-2').value = '';
        document.getElementById('analysis-error').textContent = '';
    }

    function switchRoom(groupId, name) {
        currentGroupId = groupId;
        chatTitle.textContent = name;
        loadMessages(groupId);
        // 更新分析部分的名称
        document.getElementById('person-name').textContent = name;
        // 清空分析内容
        clearAnalysisContent();
        // 加入 Socket.IO 房間
        socket.emit('join', { group: groupId });
        window.currentGroupId= groupId;
    }

    // 添加获取当前 groupId 的函数
    window.getCurrentGroupId = function() {
        return currentGroupId;
    };

    // 初始化情感分析按钮
    const analyzeButton = document.getElementById('emotion-analysis-button');
    if (analyzeButton) {
        analyzeButton.addEventListener('click', async function() {
            const analysis = await emotionAnalysis.analyzeEmotion();
            emotionAnalysis.updateAnalysisUI(analysis);
        });
    }

    function loadMessages(groupId) {
        fetch(`/get_recent_messages/${groupId}`)
            .then(response => response.json())
            .then(messages => {
                messageList.innerHTML = '';
                displayedMessageIds.clear();  // 清空已顯示消息的集合
                messages.forEach(displayMessage);
            })
            .catch(error => console.error('Error loading messages:', error));
    }

    //function loadMessages(groupId) {
        // 这里应该从服务器加载消息
        // 为了演示，我们只是清空消息列表
        //messageList.innerHTML = '';
    //}

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
    
    // 添加創建新聊天的函數
    function createNewChat(type, otherUserId = null, groupName = null) {
        const data = { type };
        if (type === 'private') {
            data.other_user_id = otherUserId;
        } else if (type === 'group') {
            data.group_name = groupName;
        }

        fetch('/create_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.message === '聊天創建成功') {
                renderFriendList();  // 重新渲染聊天列表
                switchRoom(result.group_id, type === 'private' ? `與 ${otherUserId} 的私聊` : groupName);
            } else {
                throw new Error(result.message || '創建聊天失敗');
            }
        })
        .catch(error => {
            console.error('Error creating chat:', error);
            alert(error.message);
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

        return fetch(`/get_new_messages/${currentGroupId}?since=${encodeURIComponent(lastMessageTimestamp)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(messages => {
                messages.forEach(displayMessage);
                if (messages.length > 0) {
                    const lastTimestamp = messages[messages.length - 1].timestamp;
                    updateLastMessageTimestamp(lastTimestamp);
                }
            })
            .catch(error => {
                console.error('Error polling for new messages:', error);
            });
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
        
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
    
        if (message.sender_id !== currentUserId) {
            const userInfo = userInfoMap.get(message.sender_id.toString());
            const avatarElement = document.createElement('img');
            avatarElement.className = 'sender-avatar';
            avatarElement.src = userInfo ? userInfo.avatarUrl : '/static/image/default-avatar.png';
            avatarElement.alt = userInfo ? userInfo.username : 'Unknown User';
            contentElement.appendChild(avatarElement);
    
            const senderNameElement = document.createElement('div');
            senderNameElement.className = 'sender-name';
            senderNameElement.textContent = userInfo ? userInfo.username : 'Unknown User';
            contentElement.appendChild(senderNameElement);
        }
        
        const bubbleElement = document.createElement('div');
        bubbleElement.className = 'message-bubble';
        bubbleElement.textContent = message.content;
        contentElement.appendChild(bubbleElement);
    
        const timeElement = document.createElement('div');
        timeElement.className = 'message-time';
        const messageTime = new Date(message.timestamp);
        timeElement.textContent = formatTimeOnly(messageTime);
        contentElement.appendChild(timeElement);
    
        messageElement.appendChild(contentElement);
        messageElement.dataset.timestamp = message.timestamp;
        
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
        }, 1000);
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
    //renderFriendList();
    //switchRoom('default_room', '聊天室');
});

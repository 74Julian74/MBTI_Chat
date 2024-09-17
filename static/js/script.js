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
    const userInfoCache = new Map();
    const displayedMessageIds = new Set();
    
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
                    const groupId = `${Math.min(currentUserId, friend.id)}_${Math.max(currentUserId, friend.id)}`;
                    friendElement.dataset.id = groupId;
    
                    // 確認是否有頭像，否則使用默認頭像
                    const avatarUrl = friend.profile_picture ? `/uploads/${friend.profile_picture}` : '/static/image/default-avatar.png';
    
                    friendElement.innerHTML = `
                        <img src="${avatarUrl}" alt="${friend.username}" class="friend-avatar">
                        <div class="friend-info">
                            <div class="friend-name">${friend.username}</div>
                        </div>
                    `;
                    friendList.appendChild(friendElement);
    
                    // 將用戶信息添加到映射中
                    userInfoMap.set(friend.id.toString(), {
                        username: friend.username,
                        avatarUrl: avatarUrl
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
        loadMessages(groupId).then(() => {
            markAllMessagesAsRead(groupId);
            updateReadStatus(groupId);
        });
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
        return fetch(`/get_recent_messages/${groupId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(messages => {
                messageList.innerHTML = '';
                displayedMessageIds.clear();  // 清空已顯示消息的集合
                messages.forEach(displayMessage);
                return messages;  // 返回消息數組，以便後續處理
            })
            .catch(error => {
                console.error('Error loading messages:', error);
                throw error;  // 重新拋出錯誤，以便調用者可以捕獲
            });
    }
    
    function updateMessageReadStatus(timestamp) {
        const messageElements = document.querySelectorAll(`.message[data-timestamp="${timestamp}"]`);
        messageElements.forEach(element => {
            element.classList.add('read');
            const readStatusElement = element.querySelector('.read-status');
            if (readStatusElement) {
                readStatusElement.textContent = '已讀';
            }
        });
    }

    function updateReadStatus(groupId) {
        const lastMessage = messageList.lastElementChild;
        if (lastMessage) {
            const lastReadTimestamp = lastMessage.dataset.timestamp;
            fetch('/update_read_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    group_id: groupId,
                    last_read_timestamp: lastReadTimestamp
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // 更新所有未讀消息的狀態
                    const unreadMessages = document.querySelectorAll('.message.received:not(.read)');
                    unreadMessages.forEach(msg => {
                        const timestamp = msg.dataset.timestamp;
                        if (timestamp <= lastReadTimestamp) {
                            updateMessageReadStatus(timestamp);
                        }
                    });
                }
            })
            .catch(error => console.error('Error updating read status:', error));
        }
    }

    function markAllMessagesAsRead(groupId) {
        const unreadMessages = document.querySelectorAll('.message.received:not(.read)');
        unreadMessages.forEach(messageElement => {
            const timestamp = messageElement.dataset.timestamp;
            markMessageAsRead(groupId, timestamp);
        });
    }

    function markMessageAsRead(groupId, messageTimestamp) {
        //console.log("Marking message as read:", groupId, messageTimestamp);
        fetch('/mark_as_read', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ group_id: groupId, message_timestamp: messageTimestamp })
        })
        .then(response => response.json())
        .then(data => {
            //console.log("Mark as read response:", data);
            if (data.status === 'success') {
                updateMessageReadStatus(messageTimestamp);
                // 發送 Socket.IO 事件通知其他客戶端
                socket.emit('message_read', { group_id: groupId, timestamp: messageTimestamp });
            }
        })
        .catch(error => console.error("Error marking message as read:", error));
    }

    messageList.addEventListener('scroll', () => {
        if (messageList.scrollTop + messageList.clientHeight >= messageList.scrollHeight - 100) {
            updateReadStatus(currentGroupId);
        }
    });

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
                    timestamp: new Date().toISOString(),
                    is_read: false
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
                    updateReadStatus(currentGroupId);
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
                let newMessagesReceived = false;
                messages.forEach(message => {
                    if (!message.hasOwnProperty('is_read')) {
                        message.is_read = false;
                    }
                    if (!isMessageDisplayed(message)) {
                        displayMessage(message);
                        newMessagesReceived = true;
                        // 如果消息不是由當前用戶發送的，立即標記為已讀
                        if (message.sender_id !== currentUserId) {
                            markMessageAsRead(currentGroupId, message.timestamp);
                        }
                    }
                });
                if (newMessagesReceived) {
                    // 滾動到最新消息
                    messageList.scrollTop = messageList.scrollHeight;
                }
                if (messages.length > 0) {
                    const lastTimestamp = messages[messages.length - 1].timestamp;
                    updateLastMessageTimestamp(lastTimestamp);
                }
            })
            .catch(error => {
                console.error('Error polling for new messages:', error);
            });
    }

    function isMessageDisplayed(message) {
        const messageId = `${message.sender_id}-${message.timestamp}`;
        return displayedMessageIds.has(messageId);
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

    function getUserInfo(userId) {
        if (userInfoCache.has(userId)) {
            return Promise.resolve(userInfoCache.get(userId));
        }
    
        return fetch(`/get_user_info/${userId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch user info');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                userInfoCache.set(userId, data);
                return data;
            })
            .catch(error => {
                console.error('Error fetching user info:', error);
                return {
                    username: 'Unknown User',
                    avatar: '/static/image/default-avatar.png'
                };
            });
    }

    let lastMessageDate = null;
    function displayMessage(message) {
        console.log("Displaying message:", message);
        const messageDate = new Date(message.timestamp).toDateString();
        
        // 檢查消息是否已經顯示
        if (isMessageDisplayed(message)) {
            console.log("Message already displayed, skipping:", message);
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
            const avatarElement = document.createElement('img');
            avatarElement.className = 'sender-avatar';
            avatarElement.src = '/static/image/default-avatar.png'; // 默認頭像
            contentElement.appendChild(avatarElement);
    
            const senderNameElement = document.createElement('div');
            senderNameElement.className = 'sender-name';
            senderNameElement.textContent = 'Loading...';
            contentElement.appendChild(senderNameElement);
    
            // 異步加載用戶信息
            getUserInfo(message.sender_id).then(userInfo => {
                avatarElement.src = userInfo.avatar;
                avatarElement.alt = userInfo.username;
                senderNameElement.textContent = userInfo.username;
            });
        }

        const bubbleWrapper = document.createElement('div');
        bubbleWrapper.className = 'bubble-wrapper';

        const bubbleElement = document.createElement('div');
        bubbleElement.className = 'message-bubble';
        bubbleElement.textContent = message.content;
        bubbleWrapper.appendChild(bubbleElement);

        const readStatusElement = document.createElement('span');
        readStatusElement.className = 'read-status';
        readStatusElement.textContent = message.is_read ? '已讀' : '';
        bubbleWrapper.appendChild(readStatusElement);

        contentElement.appendChild(bubbleWrapper);

        const timeElement = document.createElement('div');
        timeElement.className = 'message-time';
        const messageTime = new Date(message.timestamp);
        timeElement.textContent = formatTimeOnly(messageTime);
        contentElement.appendChild(timeElement);
        
    
        messageElement.appendChild(contentElement);
        messageElement.dataset.timestamp = message.timestamp;
        
        messageList.appendChild(messageElement);
        messageList.scrollTop = messageList.scrollHeight;

        // 將消息標記為已顯示
        const messageId = `${message.sender_id}-${message.timestamp}`;
        displayedMessageIds.add(messageId);
    
        // 如果消息是由當前用戶發送的,且未讀,則設置一個檢查間隔
        if (message.sender_id === currentUserId && !message.is_read) {
            setInterval(() => checkMessageStatus(currentGroupId, message.timestamp), 5000);
        }
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

    function checkMessageStatus(groupId, messageTimestamp) {
        fetch(`/check_message_status?group_id=${groupId}&timestamp=${messageTimestamp}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.is_read) {
                    const messageElement = document.querySelector(`[data-timestamp="${messageTimestamp}"]`);
                    if (messageElement) {
                        const readStatusElement = messageElement.querySelector('.read-status');
                        if (readStatusElement) {
                            readStatusElement.textContent = '已讀';
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error checking message status:', error);
            });
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

    socket.on('messages_read', (data) => {
        if (data.group_id === currentGroupId) {
            data.timestamps.forEach(timestamp => {
                updateMessageReadStatus(timestamp);
            });
        }
    });

    socket.on('message_read', (data) => {
        if (data.group_id === currentGroupId) {
            updateMessageReadStatus(data.timestamp);
        }
    });
    
    socket.on('new_message', (message) => {
        console.log("Received new message:", message);
        if (!message.hasOwnProperty('is_read')) {
            message.is_read = false;  // 如果新消息沒有 is_read 字段，設置為 false
        }
        displayMessage(message);
        if (message.sender_id !== currentUserId) {
            markMessageAsRead(currentGroupId, message.timestamp);
        }
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

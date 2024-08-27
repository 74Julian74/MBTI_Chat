document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const searchId = document.getElementById('search-id').value;
            const searchUsername = document.getElementById('search-username').value;

            fetch('/search_friend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `search_id=${encodeURIComponent(searchId)}&search_username=${encodeURIComponent(searchUsername)}`
            })
            .then(response => response.json())
            .then(users => {
                const resultsContainer = document.getElementById('search-results');
                resultsContainer.innerHTML = '';
                const template = document.getElementById('search-result-template');

                if (users.length === 0) {
                    resultsContainer.textContent = '未找到匹配的用户';
                    return;
                }

                users.forEach(user => {
                    const clone = template.content.cloneNode(true);
                    clone.querySelector('.profile-picture').src = `/uploads/${user.profile_picture}`;
                    clone.querySelector('.user-id').textContent = `ID: ${user.id}`;
                    clone.querySelector('.username').textContent = `用户名: ${user.username}`;
                    clone.querySelector('.add-friend-btn').addEventListener('click', () => sendFriendRequest(user.id));
                    resultsContainer.appendChild(clone);
                });
            })
            .catch(error => {
                console.error('搜索出错:', error);
                alert('搜索时发生错误，请稍后再试');
            });
        });
    } else {
        console.error('搜索表单未找到');
    }
});

function sendFriendRequest(friendId) {
    fetch('/send_friend_request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `friend_id=${friendId}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert('好友请求已发送');
        } else {
            alert('发送好友请求失败：' + data.message);
        }
    })
    .catch(error => {
        console.error('发送好友请求出错:', error);
        alert('发送好友请求时发生错误，请稍后再试');
    });
}
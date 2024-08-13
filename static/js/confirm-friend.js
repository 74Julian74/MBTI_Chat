function loadFriendRequests() {
    fetch('/get_friend_requests')
    .then(response => response.json())
    .then(requests => {
        const requestList = document.getElementById('request-list');
        requestList.innerHTML = '';
        const template = document.getElementById('friend-request-template');

        requests.forEach(request => {
            const clone = template.content.cloneNode(true);
            clone.querySelector('.profile-picture').src = `/uploads/${request.profile_picture}`;
            clone.querySelector('.username').textContent = request.username;
            clone.querySelector('.accept-btn').addEventListener('click', () => respondToRequest(request.id, 'accepted'));
            clone.querySelector('.reject-btn').addEventListener('click', () => respondToRequest(request.id, 'rejected'));
            requestList.appendChild(clone);
        });
    });
}

function respondToRequest(friendId, response) {
    fetch('/respond_friend_request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `friend_id=${friendId}&response=${response}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(response === 'accepted' ? '已接受好友請求' : '已拒絕好友請求');
            loadFriendRequests();
        }
    });
}

loadFriendRequests();
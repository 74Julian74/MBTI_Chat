let countdown;
function startCountdown() {
    let timeLeft = 600; // 10 minutes in seconds
    countdown = setInterval(function() {
        timeLeft--;
        if (timeLeft <= 0) {
            clearInterval(countdown);
            alert("驗證碼已過期，請重新註冊。");
            window.location.reload();
        } else {
            document.getElementById('countdown').textContent = Math.floor(timeLeft / 60) + ":" + (timeLeft % 60).toString().padStart(2, '0');
        }
    }, 1000);
}

document.addEventListener('DOMContentLoaded', function() {
    // ... 之前的代碼 ...

    document.getElementById('register-form').addEventListener('submit', function(e) {
        e.preventDefault();
        fetch('/auth/register', {
            method: 'POST',
            body: new FormData(this),
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('verification-modal').style.display = 'block';
                startCountdown(); // 開始倒計時
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('發生錯誤，請稍後再試。');
        });
    });
});

function submitVerificationCode() {
    const code = document.getElementById('verification-code').value;
    fetch('/auth/verify-email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ verification_code: code })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            window.location.href = data.redirect;
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('驗證過程中發生錯誤，請稍後再試。');
    });
}
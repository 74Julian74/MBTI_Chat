document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('form');
    const emailInput = document.querySelector('input[name="email"]');
    const passwordInput = document.querySelector('input[name="password"]');
    const rememberMeCheckbox = document.querySelector('input[name="remember"]');

    // 檢查本地存儲中是否有保存的登入信息
    const savedEmail = localStorage.getItem('rememberedEmail');
    const savedPassword = localStorage.getItem('rememberedPassword');

    if (savedEmail && savedPassword) {
        emailInput.value = savedEmail;
        passwordInput.value = savedPassword;
        rememberMeCheckbox.checked = true;
    }

    loginForm.addEventListener('submit', function(e) {
        if (rememberMeCheckbox.checked) {
            // 如果勾選了"記住我"，則保存登入信息到本地存儲
            localStorage.setItem('rememberedEmail', emailInput.value);
            localStorage.setItem('rememberedPassword', passwordInput.value);
        } else {
            // 如果沒有勾選"記住我"，則清除本地存儲中的登入信息
            localStorage.removeItem('rememberedEmail');
            localStorage.removeItem('rememberedPassword');
        }

        // 不阻止表單提交，讓後端處理登入邏輯
    });
});
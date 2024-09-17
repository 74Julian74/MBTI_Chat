import random
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 郵件發送配置
send_by = "hsindy071392@gmail.com"
password = "jwsr zkcy jwbz pueo"
mail_host = "smtp.gmail.com"
port = 465

# 全局變數存儲驗證碼及其生成時間
verification_data = {
    "code": None,
    "timestamp": None
}


def code(n=6):
    s = ''
    for i in range(n):
        number = random.randint(0, 9)
        upper_alpha = chr(random.randint(65, 90))
        lower_alpha = chr(random.randint(97, 122))
        char = random.choice([str(number), upper_alpha, lower_alpha])
        s += char
    return s


def send_email(send_to, content, subject="【情感分析聊天對話助手】信箱驗證通知"):
    message = MIMEText(content, "html", "utf-8")  # 修改這行以支持 HTML
    message["From"] = send_by
    message["To"] = send_to
    message["Subject"] = subject
    # 使用第三方服務發送
    try:
        with smtplib.SMTP_SSL(mail_host, port) as smtp:
            smtp.login(send_by, password)
            smtp.sendmail(send_by, send_to, message.as_string())
        logging.info(f"Email sent to {send_to}")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
        raise
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        raise


def send_email_code(send_to):
    verificate_code = code()
    verification_data["code"] = verificate_code
    verification_data["timestamp"] = datetime.now()

    # 修改成你想要的 HTML 樣式
    content = f""" 
    <html> 
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;"> 
        <div style="max-width: 600px; margin: 0 auto; background-color: #333; color: #ffffff; 
        padding: 20px; text-align: center; border-radius: 8px;"> 
            <img src="https://github.com/henry051123/henry/blob/main/main.png?raw=true" alt="MBTI Logo" 
            style="width: 400px; margin-bottom: 20px;"> 

            <h2 style="color: #4CAF50; margin-bottom: 10px;">您的驗證碼為</h2> 
            <h1 style="font-size: 48px; color: #4CAF50; margin: 20px 0;">{verificate_code}</h1> 

            <p style="color: #ffffff; font-size: 16px; margin-bottom: 20px;"> 
                * 為確保資料安全，此驗證碼 10 分鐘內有效。 
            </p> 

            <hr style="border: 1px solid #4CAF50; margin: 20px 0;"> 

            <p style="font-size: 14px; color: #ffffff;"> 
                若您對此驗證要求沒有印象，請立即與我們  
                <a href="mailto:hsindy071392@gmail.com" style="color: #4CAF50; text-decoration: none;">客服聯絡</a>， 
                以防止不法人士冒用您的資料。 
            </p> 

            <p style="font-size: 14px; margin-bottom: 20px; color: #ffffff;"> 
                歡迎使用應用程式，隨時掌握最新優惠內容 
            </p> 

            <hr style="border: 1px solid #4CAF50; margin: 20px 0;"> 

            <p style="font-size: 12px; color: #aaaaaa;"> 
                此信件為系統自動發送，請勿直接回覆。 
            </p> 

            <p style="font-size: 12px; color: #aaaaaa;"> 
                © 2024 情感分析助手 
            </p> 
        </div> 
    </body> 
</html> 

    """

    try:
        send_email(send_to=send_to, content=content)
        return verificate_code
    except Exception as error:
        print("發送驗證碼失敗" + str(error))
        return False


def is_code_valid(input_code):
    # 檢查輸入的驗證碼是否有效
    if verification_data["code"] is None:
        return False, "驗證碼不存在，請重新發送。"

    current_time = datetime.now()
    if current_time - verification_data["timestamp"] > timedelta(minutes=10):
        return False, "驗證碼已過期，請重新發送。"

    if input_code == verification_data["code"]:
        return True, "驗證成功。"
    else:
        return False, "驗證碼不正確。"


if __name__ == '__main__':
    send_to = 'hsindy071392@gmail.com'
    verificate_code = send_email_code(send_to=send_to)
    print(verificate_code)
import random
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

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
    message = MIMEText(content, "plain", "utf-8")
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
    content = str("您的驗證碼是: ") + verificate_code + ".如非本人操作，請忽略本條訊息."
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
    send_to = 'weareone60326@gmail.com'
    verificate_code = send_email_code(send_to=send_to)
    print(verificate_code)
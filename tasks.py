from celery_app import celery
from dbmodels import db, UserMSG
from datetime import datetime

@celery.task(bind=True, max_retries=3)
def save_message_to_db(self, sender_id, room_id, content):
    try:
        new_message = UserMSG(
            SenderID=sender_id,
            GroupID=room_id,
            ChatContent=content,
            TimeStamp=datetime.utcnow()
        )
        db.session.add(new_message)
        db.session.commit()
        print(f"Message saved to DB: {new_message}")  # 添加這行
    except Exception as exc:
        print(f"Error saving to DB: {exc}")  # 添加這行
        raise self.retry(exc=exc)

@celery.task
def send_notification(room_id, message):
    # 實現發送通知的邏輯
    print(f"發送通知到房間 {room_id}: {message}")
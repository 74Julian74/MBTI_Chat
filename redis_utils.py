import redis
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dbmodels import UserMSG, db
from flask import current_app

redis_client = redis.Redis(host='192.168.129.128', port=6379, db=0)

# 數據庫設置
HOSTNAME = "127.0.0.1"
PORT = 3306
USERNAME = "root"
PASSWORD = "Ff29098796"
DATABASE = "user_db"

engine = create_engine(f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4")
Session = sessionmaker(bind=engine)

def save_message_to_cache(group_id, sender_id, content):
    message = {
        'sender_id': sender_id,
        'content': content,
        'timestamp': datetime.now().isoformat(),
        'is_read': False
    }
    redis_client.lpush(f'chat:{group_id}', json.dumps(message))
    redis_client.ltrim(f'chat:{group_id}', 0, 49)  # 只保留最近50條消息
    # 同時保存到數據庫
    save_to_db(group_id, sender_id, content)
    
    print(f"Message saved to cache: {message}")  # 添加這行
    
def save_to_db(group_id, sender_id, content):
    session = Session()
    try:
        new_message = UserMSG(
            GroupID=group_id,
            SenderID=sender_id,
            ChatContentID=content,
            TimeStamp=datetime.now().isoformat(),
            Emotion="Unknown"  # 你可能需要一個函數來分析情緒
        )
        session.add(new_message)
        session.commit()
        print(f"Message saved to database: GroupID={group_id}, SenderID={sender_id}")
    except Exception as e:
        print(f"Error saving message to database: {e}")
        session.rollback()
    finally:
        session.close()

def get_recent_messages(group_id, limit=50):
    # 從 Redis 獲取消息
    redis_messages = redis_client.lrange(f'chat:{group_id}', 0, -1)
    parsed_messages = []
    for message in reversed(redis_messages):
        msg_data = json.loads(message)
        parsed_messages.append({
            'sender_id': msg_data['sender_id'],
            'content': msg_data['content'],
            'timestamp': msg_data['timestamp'],
            'is_read': msg_data.get('is_read', False)
        })
    
    # 只返回限制數量的消息
    return parsed_messages[:limit]

def get_messages_from_db(group_id, limit, earliest_timestamp=None):
    session = Session()
    try:
        messages = session.query(UserMSG).filter_by(GroupID=group_id).order_by(UserMSG.TimeStamp.desc()).limit(limit).all()
        return [{
            'sender_id': msg.SenderID,
            'content': msg.ChatContentID,
            'timestamp': msg.TimeStamp.isoformat()
        } for msg in messages]
    except Exception as e:
        print(f"Error fetching messages from database: {e}")
        return []
    finally:
        session.close()

def mark_message_as_read(group_id, message_timestamp):
    messages = redis_client.lrange(f'chat:{group_id}', 0, -1)
    updated = False
    for i, msg_bytes in enumerate(messages):
        msg = json.loads(msg_bytes)
        if msg['timestamp'] <= message_timestamp and not msg.get('is_read', False):
            msg['is_read'] = True
            redis_client.lset(f'chat:{group_id}', i, json.dumps(msg))
            updated = True
    return updated

# 設置 Redis 過期回調
def setup_redis_expiry_callback():
    def message_expired_callback(key):
        group_id = key.decode().split(':')[1]
        messages = get_messages_from_db(group_id, 50)
        for msg in messages:
            redis_client.lpush(f'chat:{group_id}', json.dumps(msg))
        redis_client.ltrim(f'chat:{group_id}', 0, 49)
    
    redis_client.config_set('notify-keyspace-events', 'Ex')
    pubsub = redis_client.pubsub()
    pubsub.psubscribe(**{'__keyevent@0__:expired': message_expired_callback})
    pubsub.run_in_thread(sleep_time=0.01)    

# 在應用啟動時調用這個函數
setup_redis_expiry_callback()
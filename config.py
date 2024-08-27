import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:Ff29098796@127.0.0.1/user_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Celery 配置
    CELERY_BROKER_URL = 'redis://192.168.129.128:6379/0'
    CELERY_RESULT_BACKEND = 'redis://192.168.129.128:6379/0'

# 添加這行，使得可以直接從 config 導入 CELERY_BROKER_URL
CELERY_BROKER_URL = Config.CELERY_BROKER_URL
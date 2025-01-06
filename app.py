from flask import Flask, request, redirect, url_for, jsonify
from flask import render_template, flash, current_app
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os
import json
import logging
from datetime import timedelta, datetime

# Application extensions
from extensions import db, migrate, bootstrap, csrf, socketio


from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_migrate import Migrate
from form import FormRegister, FormLogin
from werkzeug.security import check_password_hash, generate_password_hash
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from celery_config import Celery
from datetime import datetime
from redis_utils import save_message_to_cache, get_recent_messages, init_redis_callback, cleanup_redis_callback
from config import Config
from celery_config import make_celery
from celery_app import celery
from tasks import save_message_to_db, send_notification
from main import EmotionPredictor
from dbmodels import UserACC
from retry import retry
#csrf= CSRFProtect()

app = Flask(__name__, template_folder='templates', static_folder='static')

app.config['upload_pic'] = os.path.join(app.root_path, 'upload-pic')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = 'Aa12345678'  # 使用一個真正的隨機密鑰
app.config['SESSION_PROTECTION'] = 'basic'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 設置會話持續7天
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)  # 如果使用"記住我"功能
app.config['SESSION_TYPE'] = 'filesystem'

#login_manager= LoginManager()

def create_app():

    HOSTNAME = "127.0.0.1"
    PORT = 3306
    USERNAME = "root"
    PASSWORD = "Ff29098796"
    DATABASE = "user_db"
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key'

    # 初始化扩展
    csrf = CSRFProtect(app)
    db.init_app(app)
    migrate.init_app(app, db)
    bootstrap.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app)

    # 在應用啟動時初始化 Redis 回調
    init_redis_callback()

    # 註冊應用關閉時的清理函數
    @app.teardown_appcontext
    def cleanup_on_shutdown(exception=None):
        cleanup_redis_callback()

    with app.app_context():
        try:
            app.emotion_predictor = EmotionPredictor()
            app.emotion_predictor.load_models()  # 添加這行
            app.logger.info("情緒預測器初始化成功")
        except Exception as e:
            app.logger.error(f"情緒預測器初始化失敗: {e}")
            app.emotion_predictor = None

    @retry(tries=3, delay=2)
    async def init_predictor():
        try:
            predictor = EmotionPredictor()
            app.emotion_predictor = predictor
            app.logger.info("情緒預測器初始化成功")
        except Exception as e:
            app.logger.error(f"情緒預測器初始化失敗: {e}")
            raise

    # 注册蓝图
    from auth import auth_bp
    from chat import chat_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chat_bp, url_prefix='/chat')

    from routes import register_routes
    #register_routes(app)
    register_routes(app, socketio)

    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)

    for rule in app.url_map.iter_rules():
        app.logger.debug(f"Registered route: {rule.endpoint} -> {rule.rule}")

    return app
app = create_app()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login_page'

def check_db_connection():
    try:
        db.session.query("1").from_statement("SELECT 1").all()
        current_app.logger.info("Database connection successful")
    except Exception as e:
        current_app.logger.error(f"Database connection failed: {str(e)}")
    check_db_connection()

@login_manager.user_loader
def load_user(user_id):
    app.logger.debug(f"Attempting to load user with ID: {user_id}")
    try:
        user = UserACC.query.get(int(user_id))
        if user:
            app.logger.debug(f"Successfully loaded user: {user.UserID}")
            return user
        else:
            app.logger.warning(f"No user found with ID: {user_id}")
            return None
    except ValueError:
        app.logger.error(f"Invalid user ID format: {user_id}")
        return None
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(50))
    sender = db.Column(db.String(50))
    content = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return UserACC.query.get(int(user_id))

if __name__=="__main__":  # 如果以主程式執行
    from dbmodels import *
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True) # 立刻啟動伺服器

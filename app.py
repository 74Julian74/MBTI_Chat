from flask import Flask
from extensions import db, migrate, bootstrap, csrf, socketio
from flask_login import LoginManager
import os
from datetime import timedelta
import logging
from flask import current_app
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__, template_folder='templates', static_folder='static')

app.config['upload_pic'] = os.path.join(app.root_path, 'upload-pic')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = 'your_secret_key'  # 使用一個真正的隨機密鑰
app.config['SESSION_PROTECTION'] = 'basic'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 設置會話持續7天
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)  # 如果使用"記住我"功能
app.config['SESSION_TYPE'] = 'filesystem'
def create_app():

    HOSTNAME = "127.0.0.1"
    PORT = 3306
    USERNAME = "root"
    PASSWORD = "juju920713"
    DATABASE = "mbti2"
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key'

    csrf = CSRFProtect(app)
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    bootstrap.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app)


    # 注册蓝图
    from auth import auth_bp
    from chat import chat_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chat_bp, url_prefix='/chat')

    from routes import register_routes
    register_routes(app)

    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)

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

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(UserACC, int(user_id))


if __name__ == "__main__":
    from dbmodels import *
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
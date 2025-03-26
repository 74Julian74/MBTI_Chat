from flask import Flask, render_template
from extensions import db, migrate, bootstrap, csrf, socketio
from flask_login import LoginManager
from dbmodels import UserACC

app = Flask(__name__, template_folder='templates')

app.config['SECRET_KEY'] = 'your_secret_key'  # 使用一個真正的隨機密鑰
app.config['SESSION_PROTECTION'] = 'strong'
def create_app():

    HOSTNAME = "127.0.0.1"
    PORT = 3306
    USERNAME = "root"
    PASSWORD = "juju920713"
    DATABASE = "mbti2"
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key'

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

    return app
app = create_app()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login_page'

@login_manager.user_loader
def load_user(user_id):
    return UserACC.query.get(int(user_id))

if __name__ == "__main__":
    from dbmodels import *
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
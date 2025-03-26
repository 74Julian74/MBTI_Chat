from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
bootstrap = Bootstrap()
csrf = CSRFProtect()
socketio = SocketIO()
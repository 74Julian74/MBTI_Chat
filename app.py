from flask import Flask, request, redirect, url_for
from flask import render_template, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_migrate import Migrate
from form import FormRegister, FormLogin
from werkzeug.security import check_password_hash, generate_password_hash
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__, template_folder='templates')
bootstrap = Bootstrap(app)
csrf = CSRFProtect(app)

# _name_ 代表目前執行的模組

# 下面這塊是連接資料庫
HOSTNAME = "127.0.0.1"
# 改成VM的IP
PORT = 3306
USERNAME = "root"
# 改你自己的資料庫
PASSWORD = "juju920713"
# 改你自己的資料庫
DATABASE = "mbti"
# 改你自己的資料庫
app.config['SQLALCHEMY_DATABASE_URI']=f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"

DATABASE_URI = 'mysql+pymysql://root:juju920713@127.0.0.1/mbti'
engine = create_engine(DATABASE_URI)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)

class UserACC(db.Model):
    __tablename__ = "user_acc"
    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    ProfilePicture = db.Column(db.String(200), nullable=True)
    LastActive = db.Column(db.DateTime, nullable=True)
    MBTI = db.Column(db.String(5), nullable=True)
    RespondType = db.Column(db.String(20), nullable=True)
    BD = db.Column(db.Date, nullable=True)
    AGE = db.Column(db.Integer, nullable=True)
    StarSign = db.Column(db.String(5), nullable=True)

class UserMSG(db.Model):
    __tablename__ = "user_msg"
    GroupID = db.Column(db.Integer, primary_key=True, nullable=False)
    MessageID = db.Column(db.Integer, nullable=False)
    SenderID = db.Column(db.Integer, db.ForeignKey('user_acc.UserID') ,nullable=False)
    ChatContentID = db.Column(db.String(50), nullable=False)
    TimeStamp = db.Column(db.DateTime, nullable=False)
    Emotion = db.Column(db.String(10), nullable=False)


class Relation(db.Model):
    __tablename__ = "relation"
    UserID1 = db.Column(db.Integer, db.ForeignKey('user_acc.UserID'), primary_key=True)
    UserID2 = db.Column(db.Integer, db.ForeignKey('user_acc.UserID'), primary_key=True)
    Status = db.Column(db.Boolean, nullable=False)
    TimeStamp = db.Column(db.DateTime, nullable=False)

    user1 = db.relationship('UserACC', foreign_keys=[UserID1])
    user2 = db.relationship('UserACC', foreign_keys=[UserID2])


class VerifyMSG(db.Model):
    __tablename__ = "verify"
    GroupID1 = db.Column(db.Integer, primary_key=True, nullable=False)
    FilterType = db.Column(db.String(10))
    Enable = db.Column(db.Boolean, nullable=False)


class Chat(db.Model):
    __tablename__ = "chat"
    GroupID = db.Column(db.Integer, primary_key=True, nullable=False)
    GroupName = db.Column(db.String(20), nullable=False)
    CreatorID = db.Column(db.Integer, db.ForeignKey('user_acc.UserID'), nullable=False)
    CreateAt = db.Column(db.DateTime, nullable=False)
    FilterType = db.Column(db.Boolean, nullable=False)


class ChatMember(db.Model):
    __tablename__ = "chat_member"
    GroupID = db.Column(db.Integer, primary_key=True, nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey('user_acc.UserID'), nullable=False)
    Role = db.Column(db.String(10), nullable=False)
    NiceName = db.Column(db.String(10), nullable=False)


class Setting(db.Model):
    __tablename__ = "setting"
    UserID = db.Column(db.Integer, primary_key=True, nullable=False)
    NotificationSound = db.Column(db.Boolean)
    #    Theme = db.Column(db.blob, nullable=False)
    Language = db.Column(db.String(20), nullable=False)


class Notifiation(db.Model):
    __tablename__ = "notification"
    NotificattionID = db.Column(db.Integer, primary_key=True, nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey('user_acc.UserID'), nullable=False)
    NotificationType = db.Column(db.String(10), nullable=False)
    Content = db.Column(db.String(20), nullable=False)
    TimeStamp = db.Column(db.DateTime, nullable=False)
    IsRead = db.Column(db.Boolean, nullable=False)

migrate = Migrate(app, db)
with app.app_context():
    db.create_all()


@app.route("/")
def index():
    return render_template('index.html')

@app.route("/login-page", methods=['GET', 'POST'])
def login_page():
    form = FormLogin()
    if form.validate_on_submit():
        user = UserACC.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                flash('登錄成功！', 'success')
                return redirect(url_for('main_page'))
            else:
                flash('Wrong Email or Password')
                print("Wrong Email or Password")
        else:
            flash('Wrong Email or Password')
    return render_template('login-page.html', title='登陸', form=form)

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = FormRegister()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        pass

        print(f"Attempting to register: {email}")

        existing_user = UserACC.query.filter_by(email=email).first()
        if existing_user:
            flash('該信箱已註冊過', 'error')
            return render_template('register.html', form=form)

        try:
            new_user = UserACC(email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            print(f"User registered successfully: {email}")
            flash('注册成功！', 'success')
            return redirect(url_for('login_page'))

        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {str(e)}")
            flash('註冊失敗。', 'error')
            app.logger.error(f"Registration error: {str(e)}")
            return render_template('register.html', form=form)

    return render_template('register.html', form=form)

@app.route("/main-page")
def main_page():
    return render_template('main-page.html')

@app.route('/chat-room', methods=['GET', 'POST'])
def chat_room():
    return render_template('chat-room.html')

@app.route('/m-b-t-i-classification', methods=['GET'])
def mbticlassification():
    return render_template('m-b-t-i-classification.html')

@app.route('/profile', methods=['GET'])
def profile():
    return render_template('profile.html')

@app.route('/setting', methods=['GET'])
def setting():
    return render_template('setting.html')


@app.route('/sentiment-Analysis', methods=['GET'])
def sentiment_analysis():
    return render_template('sentiment-Analysis.html')


@app.route('/Sentiment_Analysis', methods=['GET'])
def Sentiment_Analysis():
    return 'this is Sentiment_Analysis'

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f"500 error: {str(error)}")
    return "500 Internal Server Error", 500

@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f"404 error: {str(error)}")
    return "404 Not Found", 404

if __name__=="__main__":  # 如果以主程式執行
    app.run(debug=True) # 立刻啟動伺服器


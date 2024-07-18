from flask import Flask, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_migrate import Migrate

# pip install flask_sqlalchemy
# pip install pymysql
app = Flask(__name__)
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

migrate = Migrate(app, db)
# with db.engine.connect() as conn: 測試資料庫,但這個應該沒辦法用
#    rs=conn.execute("select 1")
#    print(rs.fetchone())
@app.route("/")
# 函式的裝飾(Decorator): 已函式為基礎，提供附加的功能
def home():
    # return render_template('主畫面.html檔')
    return "This is home"

class UserACC(db.Model):
    __tablename__ = "user_acc"
    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    ProfilePicture = db.Column(db.String(200))
    LastActive = db.Column(db.DateTime)
    MBTI = db.Column(db.String(5))
    RespondType = db.Column(db.String(20))
    BD = db.Column(db.Date)
    AGE = db.Column(db.Integer)
    StarSign = db.Column(db.String(5))

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

    user1 = db.relationship('User', foreign_keys=[UserID1])
    user2 = db.relationship('User', foreign_keys=[UserID2])


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

@app.route("/login_page", methods=['POST'])
# 代表我們要處理的網站路徑
def login_page():
    user_name = request.form.get('user_name')
    password = request.form.get('password')

    if user_name == '410630734' and password == '12345678':
        return jsonify({'redirect_url': url_for('main_page')})
    else:
        print('Invalid user_name or password')
        return redirect(url_for('/'))

with app.app_context():
    db.create_all()
@app.route("/main_page")
def main_page():
    # return render_template('main_page.html')
    return "this is main page"

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password == confirm_password:
            return redirect(url_for('/'))
    # return render_template('註冊畫面.html')
    return "this is register"

@app.route('/chat_room', methods=['GET'])
def chat_room():
    return 'this is chat room'

@app.route('/MBTIclassification', methods=['GET'])
def MBTIclassification():
    return 'this is MBTI classification'

@app.route('/Profile', methods=['GET'])
def Profile():
    return 'this is Profile'

@app.route('/setting', methods=['GET'])
def setting():
    return 'this is setting'

@app.route('/Sentiment_Analysis', methods=['GET'])
def Sentiment_Analysis():
    return 'this is Sentiment_Analysis'

if __name__=="__main__":  # 如果以主程式執行
    app.run(debug=True) # 立刻啟動伺服器
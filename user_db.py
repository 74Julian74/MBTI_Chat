from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://your_username:your_password@your_host/user_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class UserACC(db.Model):
    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Varchar(20), unique=True, nullable=False)
    email = db.Column(db.Varchar(120), unique=True, nullable=False)
    password = db.Column(db.Varchar(60), nullable=False)
    ProfilePicture = db.column(db.Varchar(120))
    LastActive = db.column(db.DateTime)
    MBTI = db.column(db.Varchar(5))
    RespondType = db.column(db.Varchar(20))
    BD = db.column(db.Date)
    AGE = db.column(db.Integer)
    StarSign = db.column(db.Vanchar(5))


class UserMSG(db.Model):
    GroupID = db.column(db.int, primary_key=True, nullable=False)
    MessageID = db.column(db.int, nullable=False)
    SenderID = db.relationship("UserID", nullable=False)
    ChatContentID = db.column(db.varchar(50), nullable=False)
    TimeStamp = db.column(db.timestamp, nullable=False)
    Emotion = db.column(db.varchar(10), nullable=False)


class Relation(db.Model):
    UserID1 = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    UserID2 = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    Status = db.column(db.boolean, nullable=False)
    TimeStamp = db.column(db.datetime, nullable=False)

    user1 = db.relationship('User', foreign_keys=[UserID1])
    user2 = db.relationship('User', foreign_keys=[UserID2])


class VerifyMSG(db.Model):
    GroupID1 = db.column(db.int, primary_key=True, nullable=False)
    FilterType = db.column(db.varchar(10))
    Enable = db.coumn(db.boolean, nullable=False)


class Chat(db.Model):
    GroupID = db.column(db.int, primary_key=True, nullable=False)
    GroupName = db.column(db.varchar(20), nullable=False)
    CreatorID = db.relationship("UserID", nullable=False)
    CreateAt = db.column(db.datetime, nullable=False)
    FilterType = db.column(db.boolean, nullable=False)


class ChatMember(db.Model):
    GroupID = db.column(db.int, primary_key=True, nullable=False)
    UserID = db.relationship("UserID", nullable=False)
    Role = db.column(db.varchar(10), nullable=False)
    NiceName = db.column(db.varchar(10), nullable=False)


class Setting(db.Model):
    UserID = db.column(db.int, primary_key=True, nullable=False)
    NotificationSound = db.column(db.boolean)
    #    Theme = db.column(db.blob, nullable=False)
    Language = db.column(db.varchar(20), nullable=False)


class Notifiation(db.Model):
    NotificattionID = db.column(db.int, primary_key=True, nullable=False)
    UserID = db.relationship("UserID", nullable=False)
    NotificationType = db.column(db.varchar(10), nullable=False)
    Content = db.column(db.varchar(20), nullable=False)
    TimeStamp = db.column(db.timestamp, nullable=False)
    IsRead = db.column(db.boolean, nullable=False)


with app.app_context():
    db.create_all()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        mbti = request.form.get('mbti')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))

        existing_user = UserACC.query.filter((UserACC.username == username) | (UserACC.email == email)).first()
        if existing_user:
            flash('Username or email already registered', 'error')
            return redirect(url_for('register'))

        new_user = UserACC(username=username, email=email, mbti=mbti)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful', 'success')
        return redirect(url_for('login_page'))

    return render_template('')
if __name__ == '__main__':
    app.run(debug=True)

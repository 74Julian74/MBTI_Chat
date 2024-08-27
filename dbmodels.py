from extensions import db
from flask_login import UserMixin

class UserACC(db.Model, UserMixin):
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
    gender = db.Column(db.String(5), nullable=True)

    def get_id(self):
        return str(self.UserID)

class UserMSG(db.Model):
    __tablename__ = "user_msg"
    MessageID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    GroupID = db.Column(db.String(50), nullable=False, index=True)  # 修改長度為 50
    SenderID = db.Column(db.Integer, db.ForeignKey('user_acc.UserID'), nullable=False)
    ChatContentID = db.Column(db.String(500), nullable=False)  # 修改長度為 500
    TimeStamp = db.Column(db.DateTime, nullable=False)
    Emotion = db.Column(db.String(20), nullable=False)  # 修改長度為 20


class Relation(db.Model):
    __tablename__ = "relation"
    UserID1 = db.Column(db.Integer, db.ForeignKey('user_acc.UserID'), primary_key=True)
    UserID2 = db.Column(db.Integer, db.ForeignKey('user_acc.UserID'), primary_key=True)
    Status = db.Column(db.String(20), nullable=False)
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
    Language = db.Column(db.String(20), nullable=False)

class Notifiation(db.Model):
    __tablename__ = "notification"
    NotificattionID = db.Column(db.Integer, primary_key=True, nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey('user_acc.UserID'), nullable=False)
    NotificationType = db.Column(db.String(10), nullable=False)
    Content = db.Column(db.String(20), nullable=False)
    TimeStamp = db.Column(db.DateTime, nullable=False)
    IsRead = db.Column(db.Boolean, nullable=False)

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, validators, PasswordField, BooleanField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class FormRegister(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(),Length(1, 50),Email()
    ])
    password = PasswordField('PassWord', validators=[DataRequired(),
        Length(8, 255),
        EqualTo('password2', message='PASSWORD NEED MATCH')
    ])
    password2 = PasswordField('Confirm PassWord', validators=[
        validators.DataRequired()
    ])
    submit = SubmitField('註冊')

class FormLogin(FlaskForm):
    email = StringField('EMAIL', validators=[
        DataRequired(message='請輸入EMAIL'),
        Email(message='請輸入有效的電子郵件')
    ])
    password = PasswordField('PASSWORD', validators=[
        DataRequired(message='請輸入PASSWORD'),
        Length(min=8, message='密碼長度至少8個字')
    ])
    remember = BooleanField('保持登陸')
    submit = SubmitField('登陸')
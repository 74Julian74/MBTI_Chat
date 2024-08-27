from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, validators, PasswordField, BooleanField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.file import FileField, FileAllowed

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

class FormProfile(FlaskForm):
    username = StringField('使用者名稱', validators=[
        DataRequired(message='請輸入使用者名稱'),
        Length(max=20, message='使用者名稱不應超過20個字符')
    ])

    mbti = SelectField('人格特質', choices=[
        ('', '請選擇人格'),

        ('INTJ', 'INTJ'), ('INTP', 'INTP'), ('ENTJ', 'ENTJ'), ('ENTP', 'ENTP')
        ,('INFJ', 'INFJ'), ('INFP', 'INFP'), ('ENFJ', 'ENFJ'), ('ENFP', 'ENFP')
        ,('ISTJ', 'ISTJ'), ('ISFJ', 'ISFJ'), ('ESTJ', 'ESTJ'), ('ESFJ', 'ESFJ')
        ,('ISTP', 'ISTP'), ('ISFP', 'ISFP'), ('ESTP', 'ESTP'), ('ESFP', 'ESFP')
    ], validators=[DataRequired(message='請選擇MBTI類型')])

    zodiac = SelectField('星座', choices=[
        ('', '請選擇星座'),
        ('魔羯座', '魔羯座'), ('水瓶座', '水瓶座'), ('雙魚座', '雙魚座'),
        ('牡羊座', '牡羊座'), ('金牛座', '金牛座'), ('雙子座', '雙子座'),
        ('巨蟹座', '巨蟹座'), ('獅子座', '獅子座'), ('處女座', '處女座'),
        ('天秤座', '天秤座'), ('天蠍座', '天蠍座'), ('射手座', '射手座')
    ], validators=[DataRequired(message='請選擇星座')])

    gender = SelectField('性別', choices=[
        ('', '請選擇性別'),
        ('男', '男'),
        ('女', '女'),
        ('其他', '其他')
    ], validators=[DataRequired(message='請選擇性別')])

    birthday = DateField('生日', format='%Y-%m-%d', validators=[
        DataRequired(message='請輸入生日')
    ])

    profile_picture = FileField('個人照片', validators=[
        FileAllowed(['jpg', 'png'], '只允許上傳 jpg 或 png 格式的圖片')
    ])
    submit = SubmitField('確認更改')


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('當前密碼', validators=[
        DataRequired(message='請輸入當前密碼')
    ])

    new_password = PasswordField('新密碼', validators=[
        DataRequired(message='請輸入新密碼'),
        Length(min=8, message='密碼長度至少為8個字符')
    ])

    confirm_password = PasswordField('確認新密碼', validators=[
        DataRequired(message='請再次輸入新密碼'),
        EqualTo('new_password', message='兩次輸入的密碼不一致')
    ])

    submit = SubmitField('確認更改')
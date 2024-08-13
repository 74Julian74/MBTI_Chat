
from flask import Blueprint, flash, redirect, url_for, render_template, request, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user
from extensions import db
from dbmodels import UserACC
from form import FormRegister, FormLogin
import logging
from flask_login import current_user
import os
from form import FormProfile
from werkzeug.utils import secure_filename
from flask_login import login_required
from form import PasswordChangeForm
from sqlalchemy.exc import SQLAlchemyError


auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login-page", methods=['GET', 'POST'])
def login_page():
    form = FormLogin()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = UserACC.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            current_app.logger.info(f"User logged in: {user.UserID}, Email: {user.email}")
            login_user(user, remember=form.remember.data)
            flash('登錄成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('chat.main_page'))
        else:
            flash('登錄失敗。請檢查您的電子郵件和密碼。', 'error')
            logging.warning(f"Failed login attempt for email: {email}")
    return render_template('login-page.html', title='登錄', form=form)

@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    form = FormRegister()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        existing_user = UserACC.query.filter_by(email=email).first()
        if existing_user:
            flash('該信箱已註冊過', 'error')
            return render_template('register.html', form=form)

        try:
            new_user = UserACC(email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功！', 'success')
            return redirect(url_for('auth.login_page'))
        except Exception as e:
            db.session.rollback()
            flash('註冊失敗。', 'error')
            current_app.logger.error(f"註冊錯誤: {str(e)}")
            return render_template('register.html', form=form)

    return render_template('register.html', form=form)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route("/setting/profile-setting", methods=['GET', 'POST'])
def profile_setting():
    form = FormProfile()
    current_app.logger.debug(f"Request method: {request.method}")
    current_app.logger.debug(f"Form data: {request.form}")
    if form.validate_on_submit():
        current_app.logger.debug("Form validated successfully")
        current_app.logger.debug(f"Updating user data: username={form.username.data}, MBTI={form.mbti.data}, StarSign={form.zodiac.data}, BD={form.birthday.data}, gender={form.gender.data}")

        current_user.username = form.username.data
        current_user.MBTI = form.mbti.data
        current_user.StarSign = form.zodiac.data
        current_user.BD = form.birthday.data
        current_user.gender = form.gender.data

        if form.profile_picture.data:
            file = form.profile_picture.data
            if file and allowed_file(file.filename):
                filename = secure_filename(form.profile_picture.data.filename)
                file_path = os.path.join(current_app.config['upload_pic'], filename)
                file.save(file_path)
                current_user.ProfilePicture = filename
            else:
                flash('Invalid file type. Allowed types are jpg and png.', 'error')

        try:
            db.session.commit()
            current_app.logger.info(f"Profile updated successfully for user: {current_user.UserID}")
            flash('個人資料已更新', 'success')

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database update error for user {current_user.UserID}: {str(e)}")
            flash(f'更新失敗: {str(e)}', 'error')
            # 記錄錯誤
            current_app.logger.error(f"資料庫更新錯誤: {str(e)}")

        return redirect(url_for('setting'))


    elif request.method == 'GET':
        # 使用 getattr 函数来安全地获取属性值，如果属性不存在则返回默认值
        current_app.logger.debug(f"Form validation failed. Errors: {form.errors}")
        form.username.data = getattr(current_user, 'username', '')
        form.mbti.data = getattr(current_user, 'MBTI', '')
        form.zodiac.data = getattr(current_user, 'StarSign', '')
        form.birthday.data = getattr(current_user, 'BD', None)
        form.gender.data = getattr(current_user, 'gender', '')

    else:
        current_app.logger.debug(f"Form validation failed. Errors: {form.errors}")

    return render_template('profile-setting.html', form=form)


@auth_bp.route('/setting/password_change', methods=['GET', 'POST'])
@login_required
def password_change():
    current_app.logger.info("Accessing password change route")
    form = PasswordChangeForm()
    if request.method == 'POST' and form.validate_on_submit():
        try:
            if check_password_hash(current_user.password, form.current_password.data):
                if form.new_password.data == form.confirm_password.data:
                    hashed_password = generate_password_hash(form.new_password.data)
                    current_app.logger.info(f"New hashed password generated: {hashed_password[:10]}...")

                    current_user.password = hashed_password
                    current_app.logger.info("Password assigned to user object")

                    db.session.add(current_user)
                    current_app.logger.info("User added to session")

                    db.session.commit()
                    current_app.logger.info("Database session committed")

                    flash('密碼已成功更改', category='success')
                    return redirect(url_for('setting'))
                else:
                    flash('新密碼和確認密碼不匹配', category='danger')
            else:
                flash('當前密碼不正確', category='danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error occurred: {str(e)}")
            flash('密碼更改失敗，請稍後再試', category='danger')
        except Exception as e:
            current_app.logger.error(f"Unexpected error occurred: {str(e)}")
            flash('發生錯誤，請聯繫管理員', category='danger')
    return render_template('password-change.html', form=form)
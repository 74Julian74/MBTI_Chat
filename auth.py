from flask import Blueprint, flash, redirect, url_for, jsonify, request, current_app, session, render_template
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, current_user, login_required
from extensions import db
from dbmodels import UserACC
from form import FormRegister, FormLogin, FormProfile, PasswordChangeForm
import logging
import os
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from email_validator import validate_email
from email_utils import send_email_code
from datetime import datetime, timedelta, timezone


logging.basicConfig(level=logging.DEBUG)
auth_bp = Blueprint('auth', __name__)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


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
    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            try:
                # Validate email
                valid = validate_email(email)
                email = valid.normalized

                # Check if the email is already registered
                existing_user = UserACC.query.filter_by(email=email).first()
                if existing_user:
                    current_app.logger.info(f"Attempt to register with existing email: {email}")
                    return jsonify({"status": "error", "message": "該信箱已註冊過。"}), 400

                # Send verification code
                verification_code = send_email_code(send_to=email)
                if verification_code:
                    session['verification_code'] = verification_code
                    session['verification_time'] = datetime.now(timezone.utc)
                    session['registration_data'] = {
                        'email': email,
                        'password': hashed_password
                    }
                    current_app.logger.info(f"Verification code sent to {email}")
                    return jsonify({"status": "success", "message": "請檢查您的電子郵件以獲取驗證碼。"}), 200
                else:
                    return jsonify({"status": "error", "message": "無法發送驗證碼，請稍後再試。"}), 500
            except Exception as e:
                current_app.logger.error(f"Error during registration: {e}")
                flash('註冊時發生錯誤，請稍後再試。', 'error')
                return redirect(url_for('auth.register'))
        else:
            flash('提交表單無效。', 'error')
            return redirect(url_for('auth.register'))
        # 檢查是否有驗證碼，如果有，表示用戶正在進行郵箱驗證
    show_verification = 'verification_code' in session
    return render_template('register.html', form=form, show_verification=show_verification)


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    data = request.get_json()
    input_code = request.json.get('verification_code')
    if not input_code:
        return jsonify({'success': False, 'message': '未收到驗證碼'}), 400

    session_code = session.get('verification_code')
    verification_time = session.get('verification_time')

    if not session_code or verification_time is None:
        return jsonify({'success': False, 'message': '未找到驗證碼，請重新註冊。'}), 400

    try:
        verification_time = session.get('verification_time')
        if not verification_time:
            return jsonify({'success': False, 'message': '未找到驗證碼，請重新註冊。'}), 400

        if isinstance(verification_time, str):
            verification_time = datetime.fromisoformat(verification_time)

        if verification_time.tzinfo is None:
            verification_time = verification_time.replace(tzinfo=timezone.utc)

    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'message': '驗證碼無效或已過期，請重新註冊。'}), 400

    current_time = datetime.now(timezone.utc)
    time_difference = current_time - verification_time
    
    if time_difference > timedelta(minutes=10):
        session.pop('verification_code', None)
        session.pop('verification_time', None)
        return jsonify({'success': False, 'message': '驗證碼已過期，請重新註冊。'}), 400

    if input_code.strip().lower() == session_code.strip().lower():
        registration_data = session.get('registration_data')
        if registration_data:
            try:
                new_user = UserACC(
                    email=registration_data['email'],
                    password=registration_data['password']
                )
                db.session.add(new_user)
                db.session.commit()

                session.pop('registration_data', None)
                session.pop('verification_code', None)
                session.pop('verification_time', None)

                return jsonify({
                    'success': True, 
                    'message': '註冊成功！', 
                    'redirect': url_for('auth.login_page')
                }), 200
            except SQLAlchemyError as e:
                current_app.logger.error(f"Database error: {str(e)}")
                return jsonify({'success': False, 'message': '無法完成註冊，請稍後再試。'}), 500
        else:
            return jsonify({'success': False, 'message': '會話中未找到註冊數據。'}), 400
    else:
        return jsonify({'success': False, 'message': '驗證碼不正確。'}), 400


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@auth_bp.route("/setting/profile-setting", methods=['GET', 'POST'])
@login_required
def profile_setting():
    form = FormProfile()
    current_app.logger.debug(f"Request method: {request.method}")
    current_app.logger.debug(f"Form data: {request.form}")
    if form.validate_on_submit():
        current_app.logger.debug("Form validated successfully")
        current_app.logger.debug(f"Updating user data: username={form.username.data}, MBTI={form.mbti.data}, "
                                 f"StarSign={form.zodiac.data}, BD={form.birthday.data}, gender={form.gender.data}")

        current_user.username = form.username.data
        current_user.MBTI = form.mbti.data
        current_user.StarSign = form.zodiac.data
        current_user.BD = form.birthday.data
        current_user.gender = form.gender.data

        if form.profile_picture.data:
            file = form.profile_picture.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['upload_pic'], filename)
                file.save(file_path)
                current_user.ProfilePicture = filename
            else:
                flash('Invalid file type. Allowed types are jpg and png.', 'error')

        try:
            db.session.commit()
            current_app.logger.info(f"Profile updated successfully for user: {current_user.UserID}")
            flash('個人資料已更新', 'success')

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database update error for user {current_user.UserID}: {str(e)}")
            flash(f'更新失敗: {str(e)}', 'error')

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error occurred: {str(e)}")
            flash('發生錯誤，請稍後再試。', 'error')

        return redirect(url_for('auth.profile_setting'))

    elif request.method == 'GET':
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

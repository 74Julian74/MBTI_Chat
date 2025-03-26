from flask import Blueprint, flash, redirect, url_for, render_template, request
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user
from extensions import db
from dbmodels import UserACC
from form import FormRegister, FormLogin
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login-page", methods=['GET', 'POST'])
def login_page():
    form = FormLogin()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = UserACC.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
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
            return render_template('register.html', form=form)

    return render_template('register.html', form=form)
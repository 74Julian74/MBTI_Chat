from flask import (render_template, flash, redirect, url_for, request,
                   send_from_directory,jsonify)
from PIL import Image
import os
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from form import PasswordChangeForm
from sqlalchemy import and_
from dbmodels import *
import datetime
from datetime import datetime
def register_routes(app):

    @app.route("/")
    def index():
        return render_template('index.html')

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

    def resize_image(file_path, size=(250, 250)):
        with Image.open(file_path) as img:
            img.thumbnail(size)
            img.save(file_path)

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route('/setting/profile-setting/edit/upload_profile_picture', methods=['GET', 'POST'])
    @login_required
    def upload_profile_picture():
        if request.method == 'POST':
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['upload_pic'], filename)
                    file.save(file_path)
                    current_user.ProfilePicture = filename
                    db.session.commit()
                    flash('Profile picture updated successfully', 'success')
                else:
                    flash('Invalid file type. Allowed types are jpg and png.', 'error')
            else:
                flash('No file part in the request', 'error')
        return redirect(url_for('auth.profile_setting'))

    @app.route('/search_friend', methods=['POST'])
    @login_required
    def search_friend():
        search_id = request.form.get('search_id')
        search_username = request.form.get('search_username')

        if not search_id or not search_username:
            return jsonify({'error': '請同時提供ID和用戶名'}), 400

        try:
            search_id = int(search_id)
        except ValueError:
            return jsonify({'error': 'ID必須為數字'}), 400

        user = UserACC.query.filter(
            UserACC.UserID == search_id,
            UserACC.username == search_username
        ).first()

        if user:
            return jsonify([{
                'id': user.UserID,
                'username': user.username,
                'profile_picture': user.ProfilePicture or 'default.png'
            }])
        else:
            return jsonify([])

    @app.route('/send_friend_request', methods=['POST'])
    @login_required
    def send_friend_request():
        friend_id = request.form.get('friend_id')
        new_relation = Relation(
            UserID1=current_user.UserID,
            UserID2=friend_id,
            Status='pending',
            TimeStamp=datetime.utcnow()
        )
        db.session.add(new_relation)
        db.session.commit()
        return jsonify({'status': 'success'})

    @app.route('/get_friend_requests', methods=['GET'])
    @login_required
    def get_friend_requests():
        requests = Relation.query.filter_by(UserID2=current_user.UserID, Status='pending').all()
        return jsonify([{
            'id': request.UserID1,
            'username': UserACC.query.get(request.UserID1).username,
            'profile_picture': UserACC.query.get(request.UserID1).ProfilePicture
        } for request in requests])

    @app.route('/respond_friend_request', methods=['POST'])
    @login_required
    def respond_friend_request():
        friend_id = request.form.get('friend_id')
        response = request.form.get('response')

        request1 = Relation.query.filter_by(UserID1=friend_id, UserID2=current_user.UserID).first()
        request1.Status = response

        if response == 'accepted':
            request2 = Relation(
                UserID1=current_user.UserID,
                UserID2=friend_id,
                Status='accepted',
                TimeStamp=datetime.utcnow()
            )
            db.session.add(request2)

        db.session.commit()
        return jsonify({'status': 'success'})

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['upload_pic'], filename)

    @app.route('/setting/user_info')
    @login_required
    def user_info():
        return jsonify({
            'username': current_user.username,
            'email': current_user.email
        })

    @app.route('/setting/friend-list', methods=['GET'])
    @login_required
    def friend_list():
        return render_template('friend-list.html')

    @app.route('/setting/friend-list/AFlist', methods=['GET'])
    @login_required
    def AFlist():
        return render_template('add-friend.html')

    @app.route('/setting/friend-list/AFlist/search-friend' , methods=['GET'])
    @login_required
    def SFlist():
        return render_template('add-friend-left.html')

    @app.route('/setting/friend-list/AFlist/confirm-friend', methods=['GET'])
    @login_required
    def CFlist():
        return render_template('add-friend-right.html')

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"500 error: {str(error)}")
        return "500 Internal Server Error", 500

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f"404 error: {str(error)}")
        return "404 Not Found", 404

    @app.errorhandler(415)
    def unsupported_media_type(error):
        return jsonify({'error': 'Unsupported Media Type'}), 415

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad Request'}), 400


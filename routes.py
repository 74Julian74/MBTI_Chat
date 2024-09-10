from flask import (render_template, flash, redirect, url_for, request,
                   send_from_directory,jsonify)
from PIL import Image
import os
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
from dbmodels import *
import datetime
from datetime import datetime
from sqlalchemy import or_
from extensions import csrf
from flask_wtf.csrf import CSRFProtect

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
        if friend_id:
            try:
                friend_id = int(friend_id)
                relation_id = f"{min(current_user.UserID, friend_id)}-{max(current_user.UserID, friend_id)}"

                # 檢查是否已存在相同的好友請求
                existing_request = Relation.query.filter_by(RelationID=relation_id).first()
                if existing_request:
                    return jsonify({'status': 'error', 'message': '好友請求已存在或你們已經是好友'})

                # 創建發送者的記錄
                new_relation_sender = Relation(
                    RelationID=relation_id,
                    UserID1=current_user.UserID,
                    UserID2=friend_id,
                    Status='pending',
                    TimeStamp=datetime.utcnow()
                )

                # 創建接收者的記錄
                new_relation_receiver = Relation(
                    RelationID=relation_id,
                    UserID1=friend_id,
                    UserID2=current_user.UserID,
                    Status='waiting',
                    TimeStamp=datetime.utcnow()
                )

                db.session.add(new_relation_sender)
                #db.session.add(new_relation_receiver)
                db.session.commit()

                app.logger.info(f"Friend request sent: {new_relation_sender}"
                                #f", {new_relation_receiver}"
                                )
                return jsonify({'status': 'success', 'message': '好友請求已發送'})

            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error saving friend request: {str(e)}")
                return jsonify({'status': 'error', 'message': '保存好友請求時發生錯誤'})

        return jsonify({'status': 'error', 'message': '無效的用戶ID'})

    @app.route('/get_friends', methods=['GET'])
    @login_required
    def get_friends():
        app.logger.info(f"Getting friends for user {current_user.UserID}")
        try:
            friends = Relation.query.filter(
                (Relation.UserID1 == current_user.UserID) | (Relation.UserID2 == current_user.UserID),
                Relation.Status == 'accepted'
            ).all()
            app.logger.info(f"Found {len(friends)} friends")

            friend_list = []
            for relation in friends:
                friend_id = relation.UserID2 if relation.UserID1 == current_user.UserID else relation.UserID1
                friend = UserACC.query.get(friend_id)
                if friend:
                    friend_data = {
                        'id': friend.UserID,
                        'username': friend.username,
                        'mbti': friend.MBTI,
                        'profile_picture': friend.ProfilePicture or 'default.png'
                    }
                    friend_list.append(friend_data)
                    app.logger.info(f"Added friend: {friend_data}")
                else:
                    app.logger.warning(f"Friend with ID {friend_id} not found in UserACC table")

            app.logger.info(f"Returning friend list: {friend_list}")
            return jsonify(friend_list)
        except Exception as e:
            app.logger.error(f"Error in get_friends: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    @app.route('/delete_friend', methods=['POST'])
    @login_required
    @csrf.exempt
    def delete_friend():
        app.logger.info(f"Received delete_friend request. Headers: {request.headers}")
        app.logger.info(f"Request body: {request.get_data(as_text=True)}")

        if not request.is_json:
            app.logger.error("Request is not JSON")
            return jsonify({'status': 'error', 'message': '無效的請求格式'}), 400

        data = request.json
        app.logger.info(f"Parsed JSON data: {data}")

        friend_id = data.get('friend_id')
        app.logger.info(f"Extracted friend_id: {friend_id}")

        if not friend_id:
            return jsonify({'status': 'error', 'message': '缺少好友ID'}), 400

        try:
            friend_id = int(friend_id)
            relation_id = f"{min(current_user.UserID, friend_id)}-{max(current_user.UserID, friend_id)}"

            # 刪除所有相關的好友關係記錄
            relations = Relation.query.filter_by(RelationID=relation_id).all()
            app.logger.info(f"Found {len(relations)} relations to delete")
            for relation in relations:
                db.session.delete(relation)

            db.session.commit()
            app.logger.info(f"Friend relation deleted: {relation_id}")
            return jsonify({'status': 'success', 'message': '好友已成功刪除'})

        except ValueError:
            app.logger.error(f"Invalid friend_id: {friend_id}")
            return jsonify({'status': 'error', 'message': '無效的好友ID'}), 400
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error(f"Error deleting friend relation: {str(e)}")
            return jsonify({'status': 'error', 'message': '刪除好友時發生資料庫錯誤'}), 500
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Unexpected error when deleting friend: {str(e)}")
            return jsonify({'status': 'error', 'message': '刪除好友時發生未知錯誤'}), 500

    '''
    @app.route('/get_friends', methods=['GET'])
    @login_required
    def get_friends():
        app.logger.info(f"Getting friends for user {current_user.UserID}")
        try:
            friends = Relation.query.filter(
                (Relation.UserID1 == current_user.UserID) | (Relation.UserID2 == current_user.UserID),
                Relation.Status == 'accepted'
            ).all()
            app.logger.info(f"Found {len(friends)} friends")

            friend_list = []
            for relation in friends:
                friend_id = relation.UserID2 if relation.UserID1 == current_user.UserID else relation.UserID1
                friend = UserACC.query.get(friend_id)
                if friend:
                    friend_list.append({
                        'id': friend.UserID,
                        'username': friend.username,
                        'mbti': friend.MBTI,
                        'profile_picture': friend.ProfilePicture or 'default.png'
                    })
                else:
                    app.logger.warning(f"Friend with ID {friend_id} not found in UserACC table")

            app.logger.info(f"Returning friend list: {friend_list}")
            return jsonify(friend_list)
        except Exception as e:
            app.logger.error(f"Error in get_friends: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
        '''

    @app.route('/get_friend_requests', methods=['GET'])
    @login_required
    def get_friend_requests():
        requests = Relation.query.filter_by(UserID2=current_user.UserID, Status='pending').all()
        app.logger.info(f"Fetching friend requests for user {current_user.UserID}: {requests}")
        return jsonify([{
            'id': request.UserID1,
            'username': UserACC.query.get(request.UserID1).username,
            'profile_picture': UserACC.query.get(request.UserID1).ProfilePicture or 'default.png'
        } for request in requests])

    from sqlalchemy.exc import SQLAlchemyError

    @app.route('/respond_friend_request', methods=['POST'])
    @login_required
    def respond_friend_request():
        data = request.json
        friend_id = data.get('friend_id')
        response = data.get('response')
        app.logger.info(f"respond_friend_request 被調用，數據為：{request.json}")

        if not friend_id or not response:
            return jsonify({'status': 'error', 'message': '無效的請求數據'})

        relation_id = f"{min(current_user.UserID, friend_id)}-{max(current_user.UserID, friend_id)}"
        relation_id2 = f"{min(current_user.UserID, friend_id)}-{max(current_user.UserID, friend_id)}"
        app.logger.info(f"正在查詢 RelationID：{relation_id}")

        try:
            # 首先，讓我們檢查所有與這個 RelationID 相關的記錄
            all_relations = Relation.query.filter(Relation.RelationID == relation_id,
                                                  Relation.RelationID == relation_id2).all()
            app.logger.info(f"找到的所有關係數量：{len(all_relations)}")
            for rel in all_relations:
                app.logger.info(f"關係：UserID1={rel.UserID1}, UserID2={rel.UserID2}, Status={rel.Status}")

            # 然後，讓我們進行原始的查詢
            relations = Relation.query.filter(
                Relation.RelationID == relation_id,
                or_(
                    Relation.UserID1 == current_user.UserID,
                    Relation.UserID2 == current_user.UserID
                )
            ).with_for_update().all()

            app.logger.info(f"查詢到的關係數量：{len(relations)}")
            for rel in relations:
                app.logger.info(f"查詢到的關係：UserID1={rel.UserID1}, UserID2={rel.UserID2}, Status={rel.Status}")

            if len(relations) != 2:
                app.logger.warning(f"預期找到2條記錄，但實際找到{len(relations)}條")
                # 如果只找到一條記錄，讓我們嘗試找出另一條記錄
                other_relation = Relation.query.filter(
                    Relation.RelationID == relation_id,
                    Relation.UserID1 != current_user.UserID,
                    Relation.UserID2 != current_user.UserID
                ).first()
                if other_relation:
                    app.logger.info(
                        f"找到另一條記錄：UserID1={other_relation.UserID1}, UserID2={other_relation.UserID2}, Status={other_relation.Status}")
                    relations.append(other_relation)

            if len(relations) != 1:
                return jsonify({'status': 'error', 'message': '找不到相應的好友請求'})

            if response == 'accepted':
                new_status = 'accepted'
            elif response == 'rejected':
                new_status = 'rejected'
            else:
                return jsonify({'status': 'error', 'message': '無效的響應'})

            for relation in relations:
                app.logger.info(f"更新前的狀態：{relation.Status}")
                relation.Status = new_status
                app.logger.info(f"更新後的狀態：{relation.Status}")

            try:
                db.session.commit()
                app.logger.info("事務成功提交")
                return jsonify({'status': 'success', 'message': '好友請求已處理'})

            except SQLAlchemyError as e:
                db.session.rollback()
                app.logger.error(f"提交事務時發生錯誤：{str(e)}")
                return jsonify({'status': 'error', 'message': '處理好友請求時發生資料庫錯誤'})

        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error(f"處理好友請求時發生資料庫錯誤: {str(e)}")
            return jsonify({'status': 'error', 'message': '處理好友請求時發生資料庫錯誤'})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"處理好友請求時發生未知錯誤: {str(e)}")
            return jsonify({'status': 'error', 'message': '處理好友請求時發生未知錯誤'})

    @app.route('/cleanup_duplicate_relations', methods=['GET'])
    @login_required
    def cleanup_duplicate_relations():
        try:
            with db.session.begin():
                # 找出所有重複的 RelationID
                duplicate_relations = db.session.query(Relation.RelationID).group_by(Relation.RelationID).having(
                    db.func.count() > 2).all()

                for relation_id in duplicate_relations:
                    relations = Relation.query.filter_by(RelationID=relation_id[0]).order_by(
                        Relation.TimeStamp.desc()).all()
                    # 保留最新的兩條記錄，刪除其他
                    for relation in relations[2:]:
                        db.session.delete(relation)

            return jsonify({'status': 'success', 'message': '重複關係已清理'})
        except Exception as e:
            app.logger.error(f"清理重複關係時發生錯誤: {str(e)}")
            return jsonify({'status': 'error', 'message': '清理重複關係時發生錯誤'})


    @app.route('/check_relation_status/<int:friend_id>', methods=['GET'])
    @login_required
    def check_relation_status(friend_id):
        relation_id = f"{min(current_user.UserID, friend_id)}-{max(current_user.UserID, friend_id)}"
        relations = Relation.query.filter_by(RelationID=relation_id).all()
        return jsonify([{'UserID1': r.UserID1, 'UserID2': r.UserID2, 'Status': r.Status} for r in relations])

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

    @app.route('/setting/friend-list/add-friend', methods=['GET'])
    @login_required
    def add_friend():
        return render_template('add-friend.html')

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


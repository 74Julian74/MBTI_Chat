from flask import (render_template, flash, redirect, url_for, request,
                   send_from_directory,jsonify)
from PIL import Image
import os
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from form import PasswordChangeForm
from sqlalchemy import and_, or_
from dbmodels import *
import datetime
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
from redis_utils import save_message_to_cache, get_recent_messages, mark_message_as_read, redis_client
from sentiment_analysis import analyze_sentiment
from flask_socketio import join_room
from sqlalchemy.exc import SQLAlchemyError
import uuid
from sentiment_analysis import get_opponent_user_info
import json

csrf= CSRFProtect()

#def register_routes(app):

def generate_group_id():
    return uuid.uuid4().int & (1<<31)-1  # 生成一個最大為 2^31-1 的整數

def register_routes(app, socketio):
    csrf.init_app(app)
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

        if not search_id and not search_username:
            return jsonify({'error': '請至少提供ID或用戶名中的一個'}), 400

        query = UserACC.query

        if search_id:
            try:
                search_id = int(search_id)
                query = query.filter(UserACC.UserID == search_id)
            except ValueError:
                return jsonify({'error': 'ID必須為數字'}), 400

        if search_username:
            query = query.filter(UserACC.username.ilike(f'%{search_username}%'))

        users = query.all()

        if users:
            return jsonify([{
                'id': user.UserID,
                'username': user.username,
                'profile_picture': user.ProfilePicture or 'default.png'
            } for user in users])
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
    @app.route('/get_friend_requests', methods=['GET'])
    @login_required
    def get_friend_requests():
        requests = Relation.query.filter_by(UserID2=current_user.UserID, Status='pending').all()
        return jsonify([{
            'id': request.UserID1,
            'username': UserACC.query.get(request.UserID1).username,
            'profile_picture': UserACC.query.get(request.UserID1).ProfilePicture
        } for request in requests])
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
    
    def get_username(user_id):
        user= UserACC.query.get(user_id)
        return user.username if user else "Unknown"
    
    @app.route('/send_message', methods=['POST'])
    @csrf.exempt
    def send_message():
        data = request.json
        group_id = data['group_id']
        content = data['content']
        sender_id = data['sender_id']

        # 創建新消息時包含 is_read 字段
        new_message = {
            'sender_id': sender_id,
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'is_read': False  # 新消息初始設置為未讀
        }

        save_message_to_cache(group_id, sender_id, content)

        return jsonify({
            'status': 'success',
            'message': new_message
        })

    @app.route('/get_current_user_id')
    @login_required
    def get_current_user_id():
        return jsonify({'user_id': current_user.UserID})
    
    @app.route('/get_recent_messages/<group_id>')
    @login_required
    def get_recent_messages_route(group_id):
        messages = get_recent_messages(group_id, limit=50)
        
        # 動態添加發送者的用戶名
        for message in messages:
            message['sender_name'] = get_username(message['sender_id'])
            if 'is_read' not in message:
                message['is_read'] = False
        
        return jsonify(messages)
    
    @socketio.on('join')
    def on_join(data):
        group = data['group']  # 將 'room' 改為 'group'
        join_room(group)

    @app.route('/analyze_emotion', methods=['POST'])
    @login_required
    def analyze_emotion_route():
        try:
            data = request.json
            group_id = data.get('group_id')
            reply_style = data.get('reply_style', '正式')

            if not group_id:
                return jsonify({'error': '缺少 group_id'}), 400
            
            my_user_id = current_user.UserID
            if my_user_id is None:
                return jsonify({'error': '用戶未認證'}), 401

            app.logger.info(f"Analyzing emotion with group_id: {group_id}, user_id: {my_user_id}, reply_style: {reply_style}")
            
            # 在这里获取对方的信息
            opponent_info = get_opponent_user_info(group_id, my_user_id)
            if not opponent_info:
                return jsonify({'error': '無法獲取對方信息'}), 400

            analysis = analyze_sentiment(group_id, my_user_id, opponent_info, reply_style)
            return jsonify(analysis)
        except Exception as e:
            app.logger.error(f"Error in analyze_emotion: {str(e)}", exc_info=True)
            return jsonify({'error': '分析過程中發生錯誤', 'details': str(e)}), 500
    
    @app.route('/get_new_messages/<group_id>')
    @login_required
    def get_new_messages_route(group_id):
        since = request.args.get('since', '0')
        try:
            since_datetime = datetime.fromisoformat(since.split('+')[0].split('Z')[0])
        except ValueError:
            since_datetime = datetime.min
        
        messages = get_recent_messages(group_id)
        new_messages = [
            msg for msg in messages 
            if datetime.fromisoformat(msg['timestamp']) > since_datetime
        ]
        
        # 動態添加發送者的用戶名
        for message in new_messages:
            message['sender_name'] = get_username(message['sender_id'])
            if 'is_read' not in message:
                message['is_read'] = False
        
        return jsonify(new_messages)
    
    @app.route('/create_chat', methods=['POST'])
    @login_required
    def create_chat():
        data = request.json
        chat_type = data.get('type')
        other_user_id = data.get('other_user_id')
        group_name = data.get('group_name')

        try:
            if chat_type == 'private':
                if not other_user_id:
                    return jsonify({'error': '缺少其他用戶ID'}), 400
                # 使用兩個用戶ID生成GroupID
                current_user_id = int(current_user.UserID)
                other_user_id = int(other_user_id)
                group_id = f"{min(current_user.UserID, other_user_id)}_{max(current_user.UserID, other_user_id)}"
                group_name = f"私聊: {current_user.username} 和 {UserACC.query.get(other_user_id).username}"
            elif chat_type == 'group':
                if not group_name:
                    return jsonify({'error': '缺少群組名稱'}), 400
                group_id = generate_group_id()  # 對於群組聊天，保持原有的ID生成方式
            else:
                return jsonify({'error': '無效的聊天類型'}), 400

            # 檢查是否已存在相同的聊天組
            existing_chat = Chat.query.filter_by(GroupID=group_id).first()
            if existing_chat:
                return jsonify({'message': '聊天已存在', 'group_id': group_id}), 200

            new_chat = Chat(
                GroupID=group_id,
                GroupName=group_name,
                CreatorID=current_user.UserID,
                CreateAt=datetime.utcnow(),
                FilterType=False
            )
            db.session.add(new_chat)

            # 添加創建者作為成員
            creator_member = ChatMember(
                GroupID=group_id,
                UserID=current_user.UserID,
                Role='creator',
                NiceName=current_user.username
            )
            db.session.add(creator_member)

            if chat_type == 'private':
                other_member = ChatMember(
                    GroupID=group_id,
                    UserID=other_user_id,
                    Role='member',
                    NiceName=UserACC.query.get(other_user_id).username
                )
                db.session.add(other_member)

            db.session.commit()
            return jsonify({'message': '聊天創建成功', 'group_id': group_id}), 201

        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': f'數據庫錯誤: {str(e)}'}), 500
        except Exception as e:
            return jsonify({'error': f'未知錯誤: {str(e)}'}), 500

    @app.route('/get_user_chats', methods=['GET'])
    @login_required
    def get_user_chats():
        try:
            user_chats = db.session.query(Chat).join(ChatMember).filter(
                ChatMember.UserID == current_user.UserID
            ).all()

            chats_data = [{
                'group_id': chat.GroupID,
                'name': chat.GroupName,
                'type': 'private' if chat.GroupName.startswith('私聊:') else 'group',
                'created_at': chat.CreateAt.isoformat()
            } for chat in user_chats]

            return jsonify(chats_data), 200
        except Exception as e:
            return jsonify({'error': f'獲取聊天列表失敗: {str(e)}'}), 500

    @app.route('/add_chat_member', methods=['POST'])
    @login_required
    def add_chat_member():
        data = request.json
        group_id = data.get('group_id')
        user_id = data.get('user_id')
        
        if not group_id or not user_id:
            return jsonify({'error': '缺少必要參數'}), 400

        try:
            chat = Chat.query.get(group_id)
            if not chat:
                return jsonify({'error': '聊天組不存在'}), 404

            existing_member = ChatMember.query.filter_by(GroupID=group_id, UserID=user_id).first()
            if existing_member:
                return jsonify({'message': '用戶已經是該聊天組的成員'}), 200

            new_member = ChatMember(
                GroupID=group_id,
                UserID=user_id,
                Role='member',
                NiceName=UserACC.query.get(user_id).username
            )
            db.session.add(new_member)
            db.session.commit()

            return jsonify({'message': '成功添加新成員'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'添加成員失敗: {str(e)}'}), 500
        
    @app.route('/mark_as_read', methods=['POST'])
    @login_required
    def mark_as_read():
        data = request.json
        group_id = data['group_id']
        message_timestamp = data['message_timestamp']
        
        updated = mark_message_as_read(group_id, message_timestamp)
        
        if updated:
            # 立即发送 Socket.IO 事件
            socketio.emit('message_read', {
                'group_id': group_id,
                'timestamp': message_timestamp,
                'reader_id': current_user.UserID
            }, room=group_id)
    
        return jsonify({'status': 'success', 'updated': updated})
    
    @app.route('/check_message_status', methods=['GET'])
    def check_message_status():
        group_id = request.args.get('group_id')
        timestamp = request.args.get('timestamp')
        
        # 從 Redis 中獲取消息
        messages = redis_client.lrange(f'chat:{group_id}', 0, -1)
        for msg_bytes in messages:
            msg = json.loads(msg_bytes)
            if msg['timestamp'] == timestamp:
                return jsonify({'is_read': msg.get('is_read', False)})
        
        return jsonify({'is_read': False})
    
    @app.route('/update_read_status', methods=['POST'])
    @login_required
    def update_read_status():
        data = request.json
        group_id = data.get('group_id')
        last_read_timestamp = data.get('last_read_timestamp')
        
        if not group_id or not last_read_timestamp:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        try:
            messages = get_recent_messages(group_id)
            updated_messages = []
            for message in messages:
                if message['timestamp'] <= last_read_timestamp and message['sender_id'] != current_user.UserID:
                    mark_message_as_read(group_id, message['timestamp'])
                    updated_messages.append(message['timestamp'])
            
            # 發送 Socket.IO 事件通知所有客戶端更新已讀狀態
            socketio.emit('messages_read', {'group_id': group_id, 'timestamps': updated_messages}, room=group_id)
            
            return jsonify({'status': 'success', 'updated_messages': updated_messages}), 200
        except Exception as e:
            app.logger.error(f"Error updating read status: {str(e)}")
            return jsonify({'error': 'Failed to update read status'}), 500
    
    @app.route('/get_user_avatar/<int:user_id>')
    def get_user_avatar(user_id):
        user = UserACC.query.get(user_id)
        if user and user.ProfilePicture:
            return jsonify({'avatar_url': f"/uploads/{user.ProfilePicture}"})
        return jsonify({'avatar_url': '/static/image/default-avatar.png'})
    
    @app.route('/get_user_info/<int:user_id>')
    def get_user_info(user_id):
        user = UserACC.query.get(user_id)
        if user:
            return jsonify({
                'id': user.UserID,
                'username': user.username,
                'avatar': f"/uploads/{user.ProfilePicture}" if user.ProfilePicture else "/static/image/default-avatar.png"
            })
        return jsonify({'error': 'User not found'}), 404
    
    return app
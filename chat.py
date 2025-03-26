from flask import Blueprint, render_template
from flask_socketio import emit
from extensions import socketio


chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/main-page')
def main_page():
    return render_template('main-page.html')

@chat_bp.route('/chat-room', methods=['GET', 'POST'])
def chat_room():
    return render_template('chat-room.html')

# Socket.IO 事件處理器將在 app.py 中定義
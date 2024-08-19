from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
app = Flask(__name__, static_url_path='/static', template_folder="templates")
app.secret_key = 'your_secret_key'


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/login-page", methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        password = request.form.get('password')

        if user_name == '410630734' and password == '12345678':
            return redirect(url_for('main_page', username=user_name))  # Pass the username to the main_page
        else:
            flash('Invalid username or password')
            return redirect(url_for('login_page'))
    return render_template('login-page.html')


@app.route("/main-page")
def main_page():
    username = request.args.get('username', 'default_user')  # Retrieve the username from the request
    return render_template('main-page.html', username=username)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password == confirm_password:
            return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/chat-room/<username>')
def chat_room(username):
    user_info = {
        'helena-hills': {'name': 'Helena Hills', 'avatar': 'image/avatar-1@2x.png', 'status': '20 minutes ago'},
        'oscar-davis': {'name': 'Oscar Davis', 'avatar': 'image/rectangle-1@2x.png', 'status': '10 minutes ago'},
        'daniel-jay-park': {'name': 'Daniel Jay Park', 'avatar': 'image/avatar-2@2x.png', 'status': 'Recently online'},
        'mark-rojas': {'name': 'Mark Rojas', 'avatar': 'image/avatar-3@2x.png', 'status': 'Online'},
        'giannis-constantinou': {'name': 'Giannis Constantinou', 'avatar': 'image/avatar-4@2x.png', 'status': 'Online'},
        'briana-lewis': {'name': 'Briana Lewis', 'avatar': 'image/avatar-5@2x.png', 'status': '2 hours ago'},
        'mom': {'name': 'Mom', 'avatar': 'image/avatar-6@2x.png', 'status': '1 day ago'},
        'sherry-roy': {'name': 'Sherry Roy', 'avatar': 'image/avatar-7@2x.png', 'status': 'Online'}
    }
    current_user = user_info.get(username, {'name': 'Unknown'}).get('name', 'Unknown')
    now = datetime.now()

    chat_records = {
        'helena-hills': [
            {'text': 'Will head to the Help Center...', 'timestamp': now.strftime('%Y-%m-%d %H:%M'), 'type': 'sender'},
            {'text': 'Great, see you there!', 'timestamp': now.strftime('%Y-%m-%d %H:%M'), 'type': 'receiver'}
    ],
        'oscar-davis': [
            {'text': 'Trueeeeee', 'timestamp': now.strftime('%Y-%m-%d %H:%M'), 'type': 'sender'}],
        'daniel-jay-park': [
            {'text': 'lol yeah, are you coming to the lunch on the 13th?', 'timestamp': now.strftime('%Y-%m-%d %H:%M'), 'type': 'sender'}],
        'mark-rojas': [
            {'text': 'great catching up over dinner!!', 'timestamp': now.strftime('%Y-%m-%d %H:%M'), 'type': 'sender'}],
        'giannis-constantinou': [
            {'text': 'yep :0', 'timestamp': now.strftime('%Y-%m-%d %H:%M'), 'type': 'sender'}],
        'briana-lewis': [
            {'text': 'When are you coming back to town? Would love to catch up.', 'timestamp': now.strftime('%Y-%m-%d %H:%M'), 'type': 'sender'}],
        'mom': [
            {'text': 'Thanks!', 'timestamp': now.strftime('%Y-%m-%d %H:%M'), 'type': 'sender'}],
        'sherry-roy': [
            {'text': 'Jack needs to find a sitter for the dog and I don’t know who’s good...', 'timestamp': now.strftime('%Y-%m-%d %H:%M'), 'type': 'sender'}]
    }

    user = user_info.get(username, {'name': 'Unknown', 'avatar': 'image/default-avatar.png', 'status': 'Offline'})
    messages = chat_records.get(username, [])
    # 處理日期分隔邏輯
    formatted_records = []
    last_date = None
    for record in messages:
        current_date = record['timestamp'].split(' ')[0]
        if current_date != last_date:
            formatted_records.append({'type': 'date_separator', 'date': current_date})
            last_date = current_date
        formatted_records.append(record)
    return render_template('chat-room.html', user_info=user, chat_records=formatted_records, current_user=current_user)


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


if __name__ == "__main__":
    app.run(debug=True)


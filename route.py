from flask import Flask, render_template, request, redirect, url_for, flash

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
    # 模拟用户数据
    user_data = {
        'helena-hills': {
            'name': 'Helena Hills',
            'status': '20 minutes ago',
            'avatar': 'image/avatar-1@2x.png',
            'messages': [
                'Hello, how are you?',
                'Will head to the Help Center...'
            ]
        },
        'oscar-davis': {
            'name': 'Oscar Davis',
            'status': 'Recently online',
            'avatar': 'image/rectangle-1@2x.png',
            'messages': [
                'Trueeeeee'
            ]
        },
        'daniel-jay-park': {
            'name': 'Daniel Jay Park',
            'status': 'Recently online',
            'avatar': 'image/avatar-2@2x.png',
            'messages': [
                'lol yeah, are you coming to the lunch on the 13th?'
            ]
        },
        'mark-rojas': {
            'name': 'Mark Rojas',
            'status': 'Online',
            'avatar': 'image/avatar-3@2x.png',
            'messages': [
                'great catching up over dinner!!'
            ]
        },
        'giannis-constantino': {
            'name': 'Giannis Constantinou',
            'status': 'Online',
            'avatar': 'image/avatar-4@2x.png',
            'messages': [
                'yep :0'
            ]
        },
        'briana-lewis': {
            'name': 'Briana Lewis',
            'status': 'Recently online',
            'avatar': 'image/avatar-5@2x.png',
            'messages': [
                'When are you coming back to town? Would love to catch up.'
            ]
        },
        'mom': {
            'name': 'Mom',
            'status': '10 minutes ago',
            'avatar': 'image/avatar-6@2x.png',
            'messages': [
                'Thanks!'
            ]
        },
        'sherry-roy': {
            'name': 'Sherry Roy',
            'status': '1 hour ago',
            'avatar': 'image/avatar-7@2x.png',
            'messages': [
                'Jack needs to find a sitter for the dog and I don’t know who’s good...'
            ]
        }
    }
    user_info = user_data.get(username,
                              {'avatar': 'image/avatar-1@2x.png', 'name': 'Helena Hills', 'status': '20 minutes ago'})
    chat_records = user_info.get('messages', [])
    return render_template('chat-room.html', username=username, user_info=user_info, chat_records=chat_records)


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

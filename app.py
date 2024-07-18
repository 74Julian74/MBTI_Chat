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
            return redirect(url_for('main_page'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login_page'))
    return render_template('login-page.html')


@app.route("/main-page")
def main_page():
    return render_template('main-page.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password == confirm_password:
            return redirect(url_for('/'))
    return render_template('register.html')


@app.route('/chat-room', methods=['GET', 'POST'])
def chat_room():
    return render_template('chat-room.html')


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
    app.run()

@app.route('/Sentiment_Analysis', methods=['GET'])
def Sentiment_Analysis():
    return 'this is Sentiment_Analysis'

if __name__== "__main__": #如果以主程式執行
    app.run() #立刻啟動伺服器

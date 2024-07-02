from flask import Flask, jsonify, render_template, request,redirect, url_for, flash

app= Flask(__name__, static_url_path='/static', template_folder="templates")#_name_ 代表目前執行的模組

@app.route("/")#函式的裝飾(Decorator): 已函式為基礎，提供附加的功能
def index():
    return render_template('/index.html')
    #return "This is home"

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        password = request.form.get('password')

        if user_name == '410630734' and password == '12345678':
            return redirect(url_for('main_page'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))
    return render_template('login-page.html')
    
@app.route("/main-page")
def main_page():
    return render_template('/main-page.html')
    #return "this is main page"

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name= request.form.get('user_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password == confirm_password:
            return redirect(url_for('/'))
    return render_template('/register.html')
    #return "this is register"

@app.route('/chat_room', methods=['GET'])
def chat_room():
    return 'this is chat room'

@app.route('/MBTIclassification', methods=['GET'])
def MBTIclassification():
    return 'this is MBTI classification'

@app.route('/Profile', methods=['GET'])
def Profile():
    return 'this is Profile'

@app.route('/setting', methods=['GET'])
def setting():
    return 'this is setting'

@app.route('/Sentiment_Analysis', methods=['GET'])
def Sentiment_Analysis():
    return 'this is Sentiment_Analysis'

if __name__== "__main__": #如果以主程式執行
    app.run() #立刻啟動伺服器
from flask import Flask, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
# pip install flask_sqlalchemy
# pip install pymysql
app = Flask(__name__)
# _name_ 代表目前執行的模組

@app.route("/")
# 函式的裝飾(Decorator): 已函式為基礎，提供附加的功能
def home():
    # return render_template('主畫面.html檔')
    return "This is home"

# 下面這塊是連接資料庫
HOSTNAME = "127.0.0.1"
# 改成VM的IP
PORT = 3306
USERNAME = "root"
# 改你自己的資料庫
PASSWORD = "juju920713"
# 改你自己的資料庫
DATABASE = "MBTI"
# 改你自己的資料庫

app.config['SQLALCHEMY_DATABASE_URI'] = (f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}"
                                         f"?charset=utf8mb4")
db = SQLAlchemy(app)

# with db.engine.connect() as conn: 測試資料庫,但這個應該沒辦法用
#    rs=conn.execute("select 1")
#    print(rs.fetchone())

@app.route("/login_page", methods=['POST'])
# 代表我們要處理的網站路徑
def login_page():
    user_name = request.form.get('user_name')
    password = request.form.get('password')

    if user_name == '410630734' and password == '12345678':
        return jsonify({'redirect_url': url_for('main_page')})
    else:
        print('Invalid user_name or password')
        return redirect(url_for('/'))
    
@app.route("/main_page")
def main_page():
    # return render_template('main_page.html')
    return "this is main page"

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password == confirm_password:
            return redirect(url_for('/'))
    # return render_template('註冊畫面.html')
    return "this is register"

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

if __name__=="__main__":  # 如果以主程式執行
    app.run() # 立刻啟動伺服器
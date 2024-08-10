from flask import Flask, jsonify, request
from flask.views import MethodView
from itsdangerous import TimedJSONWebSignatureSerializer as TJSS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ABCDEFhijklm'


class AuthorToken(MethodView):
    def post(self):

        grant_type = request.form.get('grant_type')
        username = request.form.get('username')
        password = request.form.get('password')

        # 判裝grant_type是否為password，這是我們預計採用的模式
        if grant_type is None or grant_type != 'password':
            response = jsonify(message='bad grant type!')
            response.status_code = 400
            return response

        # 測試用，僅判斷是否為shaoe.chen
        if username != 'shaoe.chen' or password != '123456':
            response = jsonify(message='wrong username or password!')
            response.status_code = 400
            return response

        # 產生token，有效期設置為3600秒
        res = TJSS(app.config['SECRET_KEY'], expires_in=3600)
        token = res.dumps({'username': username}).decode('utf-8')
        return token


app.add_url_rule('/author_token/', view_func=AuthorToken.as_view('author_token'))

if __name__ == '__main__':
    app.run(debug=True)
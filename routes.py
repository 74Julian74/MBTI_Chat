from flask import render_template
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

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"500 error: {str(error)}")
        return "500 Internal Server Error", 500

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f"404 error: {str(error)}")
        return "404 Not Found", 404



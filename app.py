from flask import Flask
from home import home_bp
from online_courses import online_courses_bp
from credit_details import credit_details_bp
from blended_courses import blended_courses_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(home_bp)
app.register_blueprint(online_courses_bp)
app.register_blueprint(credit_details_bp)
app.register_blueprint(blended_courses_bp)

if __name__ == '__main__':
    app.run(debug=True)

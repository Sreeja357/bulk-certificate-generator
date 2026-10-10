from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.routes import api
    app.register_blueprint(api)

    @app.route("/")
    def home():
        return {
            "message": "Bulk Certificate Generator API is running"
        }

    return app
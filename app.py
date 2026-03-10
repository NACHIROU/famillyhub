from flask import Flask
from flask_login import LoginManager
from flask_mongoengine import MongoEngine
from config import Config

db = MongoEngine()

login_manager = LoginManager()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    
    from models import User
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)
    
    from routes.auth import auth
    from routes.main import main
    from routes.meetings import meetings
    from routes.decisions import decisions
    from routes.votes import votes
    from routes.contributions import contributions
    from routes.documents import documents
    
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(meetings)
    app.register_blueprint(decisions)
    app.register_blueprint(votes)
    app.register_blueprint(contributions)
    app.register_blueprint(documents)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

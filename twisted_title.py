import logging, os
logging.basicConfig(format='%(asctime)s | %(levelname)s: %(message)s', level=logging.INFO)

from flask import Flask
from flask_login import LoginManager

from extensions import twisted_db
from dotenv import load_dotenv
load_dotenv()


def create_twisted_title(): 
    twisted_title = Flask(__name__)

    twisted_title.config['SECRET_KEY'] = os.getenv('twisted_flask_secret', 'ERROR: No Flask Secret Found')
    twisted_title.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///twisted_db.sqlite'
    twisted_db.init_app(twisted_title)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.auth_login'
    login_manager.login_message = "Please login to see this content."
    login_manager.init_app(twisted_title)

    from models.user import User
    @login_manager.user_loader
    def load_user(id):
        return twisted_db.session.execute(
            twisted_db.select(User).filter_by(id=id)
            ).scalar_one_or_none()

    # Register the blueprint
    from routes.game_routes import game_blueprint
    from routes.auth_routes import auth_blueprint
    twisted_title.register_blueprint(game_blueprint)
    twisted_title.register_blueprint(auth_blueprint)
    
    return twisted_title

# Create the app instance for Gunicorn
twisted_title = create_twisted_title()

# Run database initialization only once, and not when imported by Gunicorn
if __name__ == "__main__":
    with twisted_title.app_context():
        twisted_db.create_all()  # Create tables if they don't exist
    twisted_title.run(port=8000)  # Run the development server
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    # Create the Flask app instance
    app = Flask(__name__)

    # Load configuration from config.py
    app.config.from_object('config.Config')

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Configure LoginManager settings
    login_manager.login_view = 'main.login'  # Redirect to login if not authenticated

    # Define user_loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        # Handle pseudo-user (fixed admin credentials)
        class FixedUser(UserMixin):
            def __init__(self, username):
                self.id = 1  # Fixed ID for admin
                self.username = username
                self.role = "Admin"

        # Return the fixed pseudo-user if the ID matches
        if user_id == "1":  # Fixed ID for admin
            return FixedUser("admin")

        return None

    # Import and register Blueprints
    from app.routes import main
    app.register_blueprint(main)

    return app  # Ensure the app object is returned

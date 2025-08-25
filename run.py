from flask import Flask
from routes import routes_bp
from extensions import db
import os

def create_app():
    app = Flask(__name__)

    # Configure DB (SQLite for now; can change later)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fences.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(routes_bp)

    # Initialize detection manager
    from routes import init_detection_manager
    init_detection_manager(app)

    # Create database tables (only for development)
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

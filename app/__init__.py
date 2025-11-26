import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app():
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    db_uri = os.environ.get('DATABASE_URL')
    if not db_uri:
        os.makedirs(app.instance_path, exist_ok=True)
        db_uri = 'sqlite:///' + os.path.join(app.instance_path, 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from .models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.propiedades import propiedades_bp
    from .routes.pago import pago_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(propiedades_bp, url_prefix='/propiedades')
    app.register_blueprint(pago_bp, url_prefix='/pago')

    with app.app_context():
        db.create_all()

    return app

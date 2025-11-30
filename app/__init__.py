import os
from flask import Flask, session, request
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv

# Inicialización de extensiones globales
db = SQLAlchemy()                    # ORM para base de datos
login_manager = LoginManager()       # Gestión de sesiones y autenticación
migrate = Migrate()                  # Sistema de migraciones de DB
socketio = SocketIO()                # WebSockets para tiempo real


def create_app():
    # Fábrica de aplicaciones Flask - Configura y retorna la app
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)

    # Configuración básica de la aplicación
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

    # Inicializar extensiones con la aplicación
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    socketio.init_app(app, cors_allowed_origins="*")  # Permitir CORS para WebSockets

    # Configurar el cargador de usuarios para Flask-Login
    from .models import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        # Carga un usuario desde la DB por su ID para mantener la sesión
        return Usuario.query.get(int(user_id))

    # Importar y registrar blueprints (módulos de rutas)
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.propiedades import propiedades_bp
    from .routes.pago import pago_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(propiedades_bp, url_prefix='/propiedades')
    app.register_blueprint(pago_bp, url_prefix='/pago')
    
    # Manejar conexiones de Socket.IO para notificaciones en tiempo real
    @socketio.on('connect')
    def handle_connect():
        if current_user.is_authenticated:
            join_room(f'user_{current_user.id}')
            
    @socketio.on('disconnect')
    def handle_disconnect():
        if current_user.is_authenticated:
            leave_room(f'user_{current_user.id}')

    # nl2br para que los saltos de linea se muestren en el template
    @app.template_filter('nl2br')
    def nl2br_filter(value):
        if not value:
            return ''
        return Markup(value.replace('\n', '<br>'))

    # Crear tablas de la base de datos si no existen
    with app.app_context():
        db.create_all()

    return app

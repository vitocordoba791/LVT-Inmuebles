from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def login_required(f):
    # Decorador que requiere que el usuario esté autenticado
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    # Decorador que requiere que el usuario sea administrador
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Primero verificar si está autenticado
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Luego verificar si es administrador
        if not current_user.es_admin:
            flash('Acceso denegado. Se requieren privilegios de administrador.', 'danger')
            return redirect(url_for('main.index'))
            
        return f(*args, **kwargs)
    return decorated_function


def propietario_o_admin_required(f):
    # Decorador que requiere que el usuario sea propietario de la propiedad o administrador
    @wraps(f)
    def decorated_function(propiedad_id, *args, **kwargs):
        from .models import Propiedad
        propiedad = Propiedad.query.get_or_404(propiedad_id)
        
        # Verificar autenticación
        if not current_user.is_authenticated:
            flash('Por favor inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))
            
        # Verificar si es propietario o administrador
        if not (current_user.es_admin or propiedad.propietario_id == current_user.id):
            flash('No tienes permiso para realizar esta acción.', 'danger')
            return redirect(url_for('main.index'))
            
        return f(propiedad_id, *args, **kwargs)
    return decorated_function

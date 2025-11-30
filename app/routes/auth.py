from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from ..models import db, Usuario
from ..auth_utils import admin_required


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        usuario = Usuario.query.filter_by(email=email).first()
        
        if not usuario:
            flash('Credenciales inválidas', 'danger')
            return render_template('auth/login.html')
            
        if not usuario.activo:
            flash('Tu cuenta ha sido desactivada. Por favor, contacta al administrador.', 'danger')
            return render_template('auth/login.html')
            
        if usuario.verificar_password(password):
            login_user(usuario)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.inicio'))
            
        flash('Credenciales inválidas', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre_usuario = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not nombre_usuario or not email or not password:
            flash('Completa todos los campos')
            return render_template('auth/register.html')
        existe = Usuario.query.filter_by(email=email).first() or Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
        if existe:
            flash('Usuario o email ya existe')
            return render_template('auth/register.html')
        # El primer usuario registrado será administrador
        es_primer_usuario = Usuario.query.count() == 0
        usuario = Usuario(
            nombre_usuario=nombre_usuario, 
            email=email,
            es_administrador=es_primer_usuario
        )
        usuario.establecer_password(password)
        db.session.add(usuario)
        db.session.commit()
        login_user(usuario)
        if es_primer_usuario:
            flash('¡Bienvenido! Eres el primer usuario y has sido asignado como administrador.', 'success')
        return redirect(url_for('main.inicio'))
    return render_template('auth/register.html')


@auth_bp.route('/admin/usuarios')
@admin_required
def admin_usuarios():
    usuarios = Usuario.query.all()
    return render_template('admin/usuarios.html', usuarios=usuarios)


@auth_bp.route('/admin/usuario/<int:usuario_id>/toggle_admin', methods=['POST'])
@admin_required
def toggle_admin(usuario_id):
    if current_user.id == usuario_id:
        flash('No puedes cambiar tus propios permisos de administrador', 'danger')
        return redirect(url_for('auth.admin_usuarios'))
        
    usuario = Usuario.query.get_or_404(usuario_id)
    usuario.es_administrador = not usuario.es_administrador
    db.session.commit()
    
    accion = 'ahora es administrador' if usuario.es_administrador else 'ya no es administrador'
    flash(f'Usuario {usuario.nombre_usuario} {accion}', 'success')
    
    # Notificar al usuario a través de WebSocket si está conectado
    if usuario.es_administrador:
        socketio.emit('rol_admin_asignado', 
                     {'mensaje': f'¡Felicidades! Se te han asignado permisos de administrador.'},
                     room=f'user_{usuario_id}')
    else:
        socketio.emit('rol_admin_revocado', 
                     {'mensaje': 'Tus permisos de administrador han sido revocados.'},
                     room=f'user_{usuario_id}')
    
    return redirect(url_for('auth.admin_usuarios'))


from flask_socketio import emit
from app import socketio

@auth_bp.route('/admin/usuario/<int:usuario_id>/toggle_estado', methods=['POST'])
@admin_required
def toggle_estado(usuario_id):
    if current_user.id == usuario_id:
        flash('No puedes desactivar tu propia cuenta', 'danger')
        return redirect(url_for('auth.admin_usuarios'))
        
    usuario = Usuario.query.get_or_404(usuario_id)
    usuario.activo = not usuario.activo
    db.session.commit()
    
    accion = 'activada' if usuario.activo else 'desactivada'
    flash(f'Cuenta de {usuario.nombre_usuario} {accion} correctamente', 'success')
    
    # Notificar al usuario a través de WebSocket si está conectado
    if not usuario.activo:
        socketio.emit('cuenta_desactivada', 
                     {'mensaje': 'Tu cuenta ha sido desactivada por un administrador.'},
                     room=f'user_{usuario_id}')
    
    return redirect(url_for('auth.admin_usuarios'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.inicio'))

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from ..models import db, Usuario


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.verificar_password(password):
            login_user(usuario)
            return redirect(url_for('main.inicio'))
        flash('Credenciales inválidas')
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
        usuario = Usuario(nombre_usuario=nombre_usuario, email=email)
        usuario.establecer_password(password)
        db.session.add(usuario)
        db.session.commit()
        login_user(usuario)
        return redirect(url_for('main.inicio'))
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.inicio'))

from flask import Blueprint, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def inicio():
    # Redirigir a la ruta de listar propiedades para mantener consistencia
    return redirect(url_for('propiedades.listar'))

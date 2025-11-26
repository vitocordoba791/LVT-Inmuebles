from flask import Blueprint, render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
from ..models import db, Propiedad


propiedades_bp = Blueprint('propiedades', __name__)


@propiedades_bp.route('/')
def listar():
    propiedades = Propiedad.query.all()
    return render_template('propiedades/lista.html', propiedades=propiedades)


@propiedades_bp.route('/<int:propiedad_id>')
@login_required
def detalle(propiedad_id):
    propiedad = Propiedad.query.get_or_404(propiedad_id)
    return render_template('propiedades/detalle.html', propiedad=propiedad)


@propiedades_bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        precio = request.form.get('precio', '').strip()
        direccion = request.form.get('direccion', '').strip()
        
        if not titulo or not descripcion or not precio or not direccion:
            return render_template('propiedades/crear.html', error='Completa todos los campos')
        
        try:
            precio_valor = float(precio)
        except ValueError:
            return render_template('propiedades/crear.html', error='Precio inválido')
        
        propiedad = Propiedad(
            titulo=titulo, 
            descripcion=descripcion, 
            precio=precio_valor, 
            direccion=direccion, 
            propietario_id=current_user.id
        )
        
        db.session.add(propiedad)
        db.session.commit()
        return redirect(url_for('propiedades.detalle', propiedad_id=propiedad.id))
    
    return render_template('propiedades/crear.html')


@propiedades_bp.route('/<int:propiedad_id>/editar', methods=['GET', 'POST'])
@login_required
def editar(propiedad_id):
    propiedad = Propiedad.query.get_or_404(propiedad_id)
    
    if propiedad.propietario_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        propiedad.titulo = request.form.get('titulo', propiedad.titulo).strip()
        propiedad.descripcion = request.form.get('descripcion', propiedad.descripcion).strip()
        propiedad.direccion = request.form.get('direccion', propiedad.direccion).strip()
        
        try:
            propiedad.precio = float(request.form.get('precio', propiedad.precio))
        except ValueError:
            return render_template('propiedades/editar.html', propiedad=propiedad, error='Precio inválido')
        
        db.session.commit()
        return redirect(url_for('propiedades.detalle', propiedad_id=propiedad.id))
    
    return render_template('propiedades/editar.html', propiedad=propiedad)


@propiedades_bp.route('/<int:propiedad_id>/eliminar', methods=['POST'])
@login_required
def eliminar(propiedad_id):
    propiedad = Propiedad.query.get_or_404(propiedad_id)
    
    if propiedad.propietario_id != current_user.id:
        abort(403)
    
    db.session.delete(propiedad)
    db.session.commit()
    return redirect(url_for('propiedades.listar'))

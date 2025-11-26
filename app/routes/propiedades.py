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
        # Obtener datos básicos
        titulo = request.form.get('titulo', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        precio = request.form.get('precio', '').strip()
        direccion = request.form.get('direccion', '').strip()
        
        # Obtener características
        metros_cuadrados = request.form.get('metros_cuadrados', '0').strip()
        habitaciones = request.form.get('habitaciones', '0').strip()
        banos = request.form.get('banos', '0').strip()
        estacionamientos = request.form.get('estacionamientos', '0').strip()
        
        # Validar campos requeridos
        campos_requeridos = {
            'título': titulo,
            'descripción': descripcion,
            'precio': precio,
            'dirección': direccion,
            'metros cuadrados': metros_cuadrados
        }
        
        for campo, valor in campos_requeridos.items():
            if not valor:
                return render_template('propiedades/crear.html', 
                                    error=f'El campo {campo} es obligatorio')
        
        # Validar y convertir valores numéricos
        try:
            precio_valor = float(precio)
            metros_cuadrados_valor = float(metros_cuadrados)
            habitaciones_valor = int(habitaciones) if habitaciones else 0
            banos_valor = int(banos) if banos else 0
            estacionamientos_valor = int(estacionamientos) if estacionamientos else 0
            
            if precio_valor <= 0:
                return render_template('propiedades/crear.html', 
                                    error='El precio debe ser mayor a 0')
                
            if metros_cuadrados_valor <= 0:
                return render_template('propiedades/crear.html',
                                    error='Los metros cuadrados deben ser mayores a 0')
                
            if habitaciones_valor < 0 or banos_valor < 0 or estacionamientos_valor < 0:
                return render_template('propiedades/crear.html',
                                    error='Los valores numéricos no pueden ser negativos')
                
        except ValueError as e:
            return render_template('propiedades/crear.html', 
                                error='Por favor ingresa valores numéricos válidos')
        
        # Crear la propiedad con todos los campos
        propiedad = Propiedad(
            titulo=titulo,
            descripcion=descripcion,
            precio=precio_valor,
            direccion=direccion,
            metros_cuadrados=metros_cuadrados_valor,
            habitaciones=habitaciones_valor,
            banos=banos_valor,
            estacionamientos=estacionamientos_valor,
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
    from ..models import Pago
    
    # Obtener la propiedad con bloqueo para evitar condiciones de carrera
    propiedad = Propiedad.query.with_for_update().get_or_404(propiedad_id)
    
    if propiedad.propietario_id != current_user.id:
        abort(403)
    
    try:
        # Primero eliminamos los pagos asociados a esta propiedad
        Pago.query.filter_by(propiedad_id=propiedad.id).delete()
        
        # Luego eliminamos la propiedad
        db.session.delete(propiedad)
        db.session.commit()
        
        # Limpiar la caché del navegador para forzar la actualización
        response = redirect(url_for('propiedades.listar'))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        db.session.rollback()
        # Si hay un error, redirigir con un mensaje de error
        from flask import flash
        flash('No se pudo eliminar la propiedad. Por favor, intente nuevamente.', 'error')
        return redirect(url_for('propiedades.detalle', propiedad_id=propiedad_id))

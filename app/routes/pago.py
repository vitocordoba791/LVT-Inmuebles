from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app, flash
from flask_login import login_required, current_user
from sqlalchemy.orm.exc import StaleDataError
from ..models import db, Pago, Propiedad
from .. import tasks
from functools import wraps


pago_bp = Blueprint('pago', __name__)


def verificar_disponibilidad(f):
    @wraps(f)
    def decorated_function(propiedad_id, *args, **kwargs):
        # Verificar si la propiedad existe y está disponible
        propiedad = Propiedad.query.get_or_404(propiedad_id)
        
        # Verificar si la propiedad ya está vendida
        if propiedad.vendida:
            flash('Lo sentimos, esta propiedad ya ha sido vendida.', 'error')
            return redirect(url_for('propiedades.detalle', propiedad_id=propiedad_id))
            
        # Verificar si hay un pago exitoso para esta propiedad
        pago_exitoso = Pago.query.filter_by(
            propiedad_id=propiedad_id,
            estado='pagado'
        ).first()
        
        if pago_exitoso:
            # Si encontramos un pago exitoso, marcamos la propiedad como vendida
            propiedad.vendida = True
            db.session.commit()
            flash('Lo sentimos, esta propiedad ya ha sido vendida recientemente.', 'error')
            return redirect(url_for('propiedades.detalle', propiedad_id=propiedad_id))
            
        return f(propiedad, *args, **kwargs)
    return decorated_function


@pago_bp.route('/pagar/<int:propiedad_id>', methods=['GET', 'POST'])
@login_required
@verificar_disponibilidad
def pagar(propiedad):
    # El decorador ya verificó que la propiedad existe y está disponible
    # y nos la pasa como parámetro
    
    # Verificar que el usuario no sea el propietario
    if propiedad.propietario_id == current_user.id:
        flash('No puedes comprar tu propia propiedad', 'error')
        return redirect(url_for('propiedades.detalle', propiedad_id=propiedad.id))
    
    if request.method == 'POST':
        try:
            # Verificar nuevamente si la propiedad sigue disponible (doble verificación)
            propiedad_actual = Propiedad.query.get(propiedad.id)
            if propiedad_actual.vendida:
                flash('Lo sentimos, esta propiedad acaba de ser vendida.', 'error')
                return redirect(url_for('propiedades.detalle', propiedad_id=propiedad.id))
            
            # Crear un nuevo pago
            pago = Pago(
                monto=propiedad.precio, 
                estado='procesando', 
                usuario_id=current_user.id, 
                propiedad_id=propiedad.id
            )
            
            db.session.add(pago)
            db.session.commit()
            
            # Iniciar el procesamiento del pago en segundo plano
            job_id = tasks.enviar_procesar_pago(current_app._get_current_object(), pago.id)
            return redirect(url_for('pago.esperar', job_id=job_id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error al crear pago: {str(e)}')
            flash('Ocurrió un error al procesar tu solicitud. Por favor, inténtalo de nuevo.', 'error')
    
    return render_template('pago/pagar.html', propiedad=propiedad)


@pago_bp.route('/esperar/<job_id>')
@login_required
def esperar(job_id):
    return render_template('pago/esperar.html', job_id=job_id)


@pago_bp.route('/estado/<job_id>')
@login_required
def estado(job_id):
    try:
        info = tasks.obtener_estado_trabajo(job_id)
        
        if not info or info.get('estado') == 'no_encontrado':
            return jsonify({
                "estado": "no_encontrado",
                "exito": False,
                "mensaje": "Trabajo no encontrado"
            }), 404
        
        respuesta = {
            "estado": info.get('estado', 'desconocido'),
            "exito": False,
            "mensaje": "Procesando..."
        }
        
        # Inicializar resultado como diccionario vacío si es None
        resultado = info.get('resultado', {}) or {}
        
        # Obtener el ID del pago del resultado si está disponible
        pago_id = resultado.get('pago_id')
        propiedad_id = resultado.get('propiedad_id')
        
        if info.get('estado') == 'completado':
            respuesta.update({
                'pago_id': pago_id,
                'propiedad_id': propiedad_id,
                'exito': resultado.get('exito', False),
                'mensaje': resultado.get('mensaje', 'Pago procesado correctamente'),
                'propiedad_vendida': resultado.get('propiedad_vendida', False)
            })
        elif info.get('estado') == 'error':
            error_msg = info.get('error') or resultado.get('mensaje') or 'Error desconocido al procesar el pago'
            respuesta.update({
                'exito': False,
                'mensaje': str(error_msg),
                'estado': 'error'
            })
        
        return jsonify(respuesta)
        
    except Exception as e:
        # Registrar el error en los logs
        current_app.logger.error(f"Error en /estado/{job_id}: {str(e)}")
        return jsonify({
            'estado': 'error',
            'exito': False,
            'mensaje': 'Error interno al procesar la solicitud'
        }), 500


@pago_bp.route('/exito/<int:pago_id>')
@login_required
def exito(pago_id):
    pago = Pago.query.get_or_404(pago_id)
    
    # Verificar que el pago pertenece al usuario actual
    if pago.usuario_id != current_user.id:
        flash('No tienes permiso para ver este pago', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('pago/exito.html', pago=pago)

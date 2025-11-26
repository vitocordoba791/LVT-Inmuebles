from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from ..models import db, Pago, Propiedad
from .. import tasks


pago_bp = Blueprint('pago', __name__)


@pago_bp.route('/pagar/<int:propiedad_id>', methods=['GET', 'POST'])
@login_required
def pagar(propiedad_id):
    propiedad = Propiedad.query.get_or_404(propiedad_id)
    
    if request.method == 'POST':
        pago = Pago(
            monto=propiedad.precio, 
            estado='procesando', 
            usuario_id=current_user.id, 
            propiedad_id=propiedad.id
        )
        
        db.session.add(pago)
        db.session.commit()
        
        job_id = tasks.enviar_procesar_pago(current_app._get_current_object(), pago.id)
        return redirect(url_for('pago.esperar', job_id=job_id))
    
    return render_template('pago/pagar.html', propiedad=propiedad)


@pago_bp.route('/esperar/<job_id>')
@login_required
def esperar(job_id):
    return render_template('pago/esperar.html', job_id=job_id)


@pago_bp.route('/estado/<job_id>')
@login_required
def estado(job_id):
    info = tasks.obtener_estado_trabajo(job_id)
    
    if not info or info.get('estado') == 'no_encontrado':
        return jsonify({"estado": "no_encontrado"}), 404
    
    respuesta = {"estado": info.get('estado')}
    pago_id = None
    
    meta = info.get('meta') or {}
    if isinstance(meta, dict):
        pago_id = meta.get('pago_id')
    
    if pago_id:
        pago = Pago.query.get(pago_id)
        if pago:
            respuesta["estado_pago"] = pago.estado
            respuesta["propiedad_id"] = pago.propiedad_id
    
    return jsonify(respuesta)

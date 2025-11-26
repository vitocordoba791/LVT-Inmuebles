from flask import Blueprint, render_template, current_app, request
from sqlalchemy import or_
from ..models import Propiedad
from .. import tasks


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def inicio():
    busqueda = (request.args.get('q') or '').strip()
    consulta = Propiedad.query
    
    if busqueda:
        patron = f"%{busqueda}%"
        consulta = consulta.filter(
            or_(
                Propiedad.titulo.ilike(patron),
                Propiedad.direccion.ilike(patron),
                Propiedad.descripcion.ilike(patron),
            )
        )
    
    propiedades = consulta.order_by(Propiedad.id.desc()).all()
    estadisticas = tasks.calcular_estadisticas_paralelo(current_app._get_current_object())
    
    return render_template('propiedades/lista.html', 
                         propiedades=propiedades, 
                         estadisticas=estadisticas, 
                         busqueda=busqueda)

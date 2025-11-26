from threading import Thread, Lock
from uuid import uuid4
from time import sleep
from typing import Any, Dict, Optional

from . import db
from .models import Pago, Usuario, Propiedad


_trabajos: Dict[str, Dict[str, Any]] = {}
_bloqueo = Lock()


def _ejecutar_en_app(app, fn, *args, **kwargs):
    with app.app_context():
        return fn(*args, **kwargs)


def enviar_trabajo(app, fn, *args, meta: Optional[Dict[str, Any]] = None, **kwargs) -> str:
    id_trabajo = str(uuid4())
    with _bloqueo:
        _trabajos[id_trabajo] = {"estado": "ejecutando", "resultado": None, "error": None, "meta": meta or {}}

    def objetivo():
        try:
            resultado = _ejecutar_en_app(app, fn, *args, **kwargs)
            with _bloqueo:
                _trabajos[id_trabajo]["estado"] = "completado"
                _trabajos[id_trabajo]["resultado"] = resultado
        except Exception as e:  # noqa: BLE001
            with _bloqueo:
                _trabajos[id_trabajo]["estado"] = "error"
                _trabajos[id_trabajo]["error"] = str(e)

    hilo = Thread(target=objetivo, daemon=True)
    hilo.start()
    return id_trabajo


def obtener_estado_trabajo(id_trabajo: str) -> Dict[str, Any]:
    with _bloqueo:
        return _trabajos.get(id_trabajo, {"estado": "no_encontrado"}).copy()


# Tareas específicas del dominio

def _procesar_pago(pago_id: int) -> Dict[str, Any]:
    from sqlalchemy.orm import sessionmaker
    from . import create_app
    
    # Configuración inicial
    app = create_app()
    Session = sessionmaker(bind=db.engine)
    session = Session()
    
    try:
        # Pequeña pausa para simular procesamiento
        sleep(2)
        
        # Obtener el pago con bloqueo para evitar actualizaciones simultáneas
        pago = session.query(Pago).with_for_update(skip_locked=True).get(pago_id)
        if not pago:
            app.logger.error(f"Pago no encontrado: {pago_id}")
            return {
                "exito": False, 
                "mensaje": "Pago no encontrado",
                "pago_id": pago_id,
                "propiedad_vendida": False
            }
            
        # Verificar si la propiedad ya está vendida
        if pago.propiedad is None:
            app.logger.error(f"Propiedad no encontrada para el pago: {pago_id}")
            return {
                "exito": False,
                "mensaje": "La propiedad asociada al pago no existe",
                "pago_id": pago.id,
                "propiedad_vendida": False
            }
            
        if pago.propiedad.vendida:
            app.logger.warning(f"Intento de pago para propiedad ya vendida: {pago.propiedad.id}")
            return {
                "exito": False, 
                "mensaje": "La propiedad ya ha sido vendida",
                "pago_id": pago.id,
                "propiedad_id": pago.propiedad.id,
                "propiedad_vendida": True
            }
            
        # Marcar pago como pagado
        pago.estado = "pagado"
        
        # Marcar propiedad como vendida
        pago.propiedad.vendida = True
        
        # Confirmar los cambios
        session.commit()
        
        app.logger.info(f"Pago {pago.id} procesado exitosamente para la propiedad {pago.propiedad.id}")
        
        return {
            "exito": True,
            "mensaje": "Pago procesado exitosamente",
            "pago_id": pago.id,
            "propiedad_id": pago.propiedad.id,
            "status": "pagado",
            "propiedad_vendida": True
        }
        
    except Exception as e:
        session.rollback()
        error_msg = f"Error procesando pago {pago_id}: {str(e)}"
        app.logger.error(error_msg, exc_info=True)
        
        return {
            "exito": False,
            "mensaje": f"Error al procesar el pago: {str(e)}",
            "pago_id": pago_id,
            "propiedad_vendida": False
        }
        
    finally:
        try:
            session.close()
        except Exception as e:
            app.logger.error(f"Error cerrando la sesión: {str(e)}")


def enviar_procesar_pago(app, pago_id: int) -> str:
    return enviar_trabajo(app, _procesar_pago, pago_id, meta={"pago_id": pago_id})


# Estadísticas en paralelo para la página de inicio

def _contar_usuarios() -> int:
    return Usuario.query.count()


def _contar_propiedades() -> int:
    return Propiedad.query.count()


def _contar_pagos() -> int:
    return Pago.query.count()


def _sumar_montos_pagados() -> float:
    from sqlalchemy import func
    total = db.session.query(func.sum(Pago.monto)).filter(Pago.estado == "pagado").scalar()
    return float(total or 0.0)


def calcular_estadisticas_paralelo(app) -> Dict[str, Any]:
    from sqlalchemy import func

    resultados: Dict[str, Any] = {}

    def ejecutar_y_guardar(clave, fn):
        valor = _ejecutar_en_app(app, fn)
        resultados[clave] = valor

    # Métricas adicionales
    def _precio_promedio() -> float:
        promedio = db.session.query(func.avg(Propiedad.precio)).scalar()
        return float(promedio or 0.0)

    def _precio_minimo() -> float:
        v = db.session.query(func.min(Propiedad.precio)).scalar()
        return float(v or 0.0)

    def _precio_maximo() -> float:
        v = db.session.query(func.max(Propiedad.precio)).scalar()
        return float(v or 0.0)

    def _contar_pagados() -> int:
        return db.session.query(Pago).filter(Pago.estado == "pagado").count()

    def _propiedades_vendidas() -> int:
        return int(db.session.query(func.count(func.distinct(Pago.propiedad_id))).filter(Pago.estado == "pagado").scalar() or 0)

    def _ticket_promedio() -> float:
        v = db.session.query(func.avg(Pago.monto)).filter(Pago.estado == "pagado").scalar()
        return float(v or 0.0)

    def _contar_propietarios() -> int:
        return int(db.session.query(func.count(func.distinct(Propiedad.propietario_id))).scalar() or 0)

    hilos = [
        Thread(target=ejecutar_y_guardar, args=("usuarios", _contar_usuarios), daemon=True),
        Thread(target=ejecutar_y_guardar, args=("propiedades", _contar_propiedades), daemon=True),
        Thread(target=ejecutar_y_guardar, args=("pagos", _contar_pagos), daemon=True),
        Thread(target=ejecutar_y_guardar, args=("total_pagado", _sumar_montos_pagados), daemon=True),
        Thread(target=ejecutar_y_guardar, args=("precio_promedio", _precio_promedio), daemon=True),
        Thread(target=ejecutar_y_guardar, args=("precio_minimo", _precio_minimo), daemon=True),
        Thread(target=ejecutar_y_guardar, args=("precio_maximo", _precio_maximo), daemon=True),
        Thread(target=ejecutar_y_guardar, args=("pagos_realizados", _contar_pagados), daemon=True),
        Thread(target=ejecutar_y_guardar, args=("propiedades_vendidas", _propiedades_vendidas), daemon=True),
        Thread(target=ejecutar_y_guardar, args=("ticket_promedio", _ticket_promedio), daemon=True),
        Thread(target=ejecutar_y_guardar, args=("total_propietarios", _contar_propietarios), daemon=True),
    ]
    
    for hilo in hilos:
        hilo.start()
    
    for hilo in hilos:
        hilo.join()
    
    return resultados

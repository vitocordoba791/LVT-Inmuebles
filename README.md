# LVT Inmuebles - Plataforma de Gestión Inmobiliaria

## 📋 Descripción

LVT Inmuebles es una plataforma web para la gestión de propiedades inmobiliarias que permite a los usuarios publicar, buscar y gestionar propiedades, así como realizar pagos de forma segura. La aplicación sigue una arquitectura en tres capas (presentación, aplicación y persistencia) y está desarrollada con Flask en el backend y HTML/CSS/JavaScript en el frontend.

## 🏗️ Arquitectura del Sistema

### Estructura de Carpetas

```
LVT-Inmuebles/
├── app/
│   ├── __init__.py         # Configuración de la aplicación
│   ├── models.py           # Modelos de base de datos
│   ├── tasks.py            # Tareas asíncronas y gestión de hilos
│   ├── routes/             # Controladores/Blueprints
│   │   ├── __init__.py
│   │   ├── auth.py         # Autenticación de usuarios
│   │   ├── main.py         # Rutas principales
│   │   ├── properties.py   # Gestión de propiedades
│   │   └── payment.py      # Procesamiento de pagos
│   ├── static/             # Archivos estáticos
│   │   ├── css/
│   │   └── js/
│   └── templates/          # Plantillas HTML
├── migrations/             # Migraciones de base de datos
└── requirements.txt        # Dependencias de Python
```

## 🔄 Modelo de Concurrencia

### 🧵 Arquitectura de Concurrencia

El sistema implementa un patrón de **Worker Pool** con hilos para manejar tareas de larga duración sin bloquear el hilo principal de la aplicación web, lo que es crucial para mantener la capacidad de respuesta de la aplicación.

### 🔧 Componentes Clave

#### 1. **Sistema de Gestión de Tareas (`tasks.py`)**

**Variables Globales**:
```python
_trabajos: Dict[str, Dict[str, Any]] = {}  # Almacena el estado de todas las tareas
_bloqueo = Lock()  # Sincroniza el acceso al diccionario de trabajos
```

**Funcionalidades Principales**:

1. **`enviar_trabajo(app, fn, *args, meta=None, **kwargs) -> str`**
   - Crea un nuevo trabajo con un ID único
   - Inicia un hilo demonio para ejecutar la tarea
   - Devuelve el ID del trabajo para seguimiento

2. **`obtener_estado_trabajo(id_trabajo: str) -> Dict[str, Any]`**
   - Consulta el estado de un trabajo por su ID
   - Retorna el estado actual, resultado o error

3. **`_ejecutar_en_app(app, fn, *args, **kwargs)`**
   - Asegura que el código se ejecute dentro del contexto de la aplicación Flask

### 🎯 Problemas Resueltos

1. **No Bloquear el Hilo Principal**
   - **Problema**: Operaciones largas (como procesar pagos) pueden congelar la interfaz.
   - **Solución**: Las tareas se ejecutan en hilos separados, permitiendo que el servidor siga respondiendo.

2. **Seguimiento de Estado**
   - **Problema**: Necesidad de saber el estado de operaciones asíncronas.
   - **Solución**: El diccionario `_trabajos` mantiene el estado de cada tarea.

3. **Seguridad en Concurrencia**
   - **Problema**: Riesgo de condiciones de carrera al acceder a recursos compartidos.
   - **Solución**: Uso de `Lock()` para sincronizar el acceso al diccionario de trabajos.

### 📊 Casos de Uso Implementados

#### 1. Procesamiento de Pagos
```python
def _procesar_pago(pago_id: int) -> Dict[str, Any]:
    sleep(2)  # Simula procesamiento
    pago = Pago.query.get(pago_id)
    if pago is None:
        return {"exito": False, "mensaje": "Pago no encontrado"}
    pago.estado = "pagado"
    db.session.commit()
    return {"exito": True, "pago_id": pago.id}
```

#### 2. Cálculo de Estadísticas en Paralelo
```python
def calcular_estadisticas_paralelo(app) -> Dict[str, Any]:
    resultados = {}
    hilos = []

    def ejecutar_y_guardar(clave, fn):
        valor = _ejecutar_en_app(app, fn)
        resultados[clave] = valor

    # Ejecutar consultas en paralelo
    metricas = [
        ("total_usuarios", _contar_usuarios),
        ("total_propiedades", _contar_propiedades),
        ("monto_total", _sumar_montos_pagados)
    ]

    for clave, fn in metricas:
        hilo = Thread(target=ejecutar_y_guardar, args=(clave, fn))
        hilo.start()
        hilos.append(hilo)

    # Esperar a que terminen todos los hilos
    for hilo in hilos:
        hilo.join()

    return resultados
```

### ⚠️ Limitaciones y Consideraciones

1. **Persistencia en Memoria**:
   - El estado de las tareas se pierde al reiniciar el servidor
   - **Solución propuesta**: Usar Redis o una base de datos para persistir el estado

2. **Escalabilidad**:
   - Los hilos compiten por el GIL (Global Interpreter Lock) de Python
   - **Solución propuesta**: Usar procesos separados o un sistema de colas como Celery

3. **Manejo de Errores**:
   - Los errores no manejados en los hilos pueden pasar desapercibidos
   - **Solución propuesta**: Implementar un sistema de logging robusto

### 🚀 Mejoras Potenciales

1. **Límite de Hilos Activos**:
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   ejecutor = ThreadPoolExecutor(max_workers=5)
   
   def enviar_trabajo_mejorado(fn, *args, **kwargs):
       future = ejecutor.submit(fn, *args, **kwargs)
       return future
   ```

2. **Tiempo de Espera Máximo**:
   ```python
   from concurrent.futures import TimeoutError
   
   try:
       resultado = future.result(timeout=30)  # Timeout de 30 segundos
   except TimeoutError:
       # Manejar timeout
   ```

3. **Reintentos Automáticos**:
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential
   
   @retry(stop=stop_after_attempt(3), 
          wait=wait_exponential(multiplier=1, min=4, max=10))
   def operacion_con_reintentos():
       # Código que puede fallar
   ```

### 🔄 Flujo de Ejecución

1. **Inicio de Tarea**:
   ```python
   # En el controlador de pagos (payment.py)
   id_trabajo = enviar_trabajo(
       app,
       _procesar_pago,
       pago_id=pago.id,
       meta={"usuario_id": current_user.id, "tipo": "pago"}
   )
   ```

2. **Procesamiento en Segundo Plano**:
   - Se crea un nuevo hilo que ejecuta `_procesar_pago`
   - El hilo principal devuelve inmediatamente una respuesta al cliente

3. **Seguimiento del Estado**:
   ```python
   # El cliente puede consultar el estado
   @payment_route.get("/payment/status/<job_id>")
   def status_pago(job_id):
       estado = obtener_estado_trabajo(job_id)
       return jsonify(estado)
   ```

Esta implementación proporciona una base sólida para el procesamiento asíncrono, pero para un entorno de producción a gran escala, se recomendaría considerar soluciones más robustas como Celery con Redis/RabbitMQ.

### Ejemplo de Uso

```python
# Iniciar una nueva tarea
id_trabajo = enviar_trabajo(
    app,
    _procesar_pago,
    pago_id=123,
    meta={"tipo": "pago", "usuario_id": current_user.id}
)

# Consultar estado
estado = obtener_estado_trabajo(id_trabajo)
```

## 💾 Modelo de Datos

### Entidades Principales

1. **Usuario**
   - Autenticación y autorización
   - Relación uno a muchos con Propiedad y Pago
   - Contraseñas almacenadas con hash seguro (bcrypt)

2. **Propiedad**
   - Información detallada de inmuebles
   - Relación con Propietario (Usuario)
   - Estado de disponibilidad

3. **Pago**
   - Transacciones financieras
   - Estados: pendiente, procesando, completado, fallido
   - Relaciones con Usuario y Propiedad

## 🔒 Seguridad

- Autenticación con Flask-Login
- Hashing de contraseñas con bcrypt
- Protección contra CSRF
- Validación de entrada en formularios
- Manejo seguro de sesiones

## 🚀 Despliegue

### Requisitos

- Python 3.8+
- SQLite (desarrollo) / PostgreSQL (producción)
- Dependencias de Python (ver `requirements.txt`)

### Instalación

1. Clonar el repositorio
2. Crear un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```
5. Inicializar la base de datos:
   ```bash
   flask db upgrade
   ```
6. Ejecutar la aplicación:
   ```bash
   flask run
   ```

## 📊 API Endpoints

### Autenticación
- `POST /auth/register` - Registrar nuevo usuario
- `POST /auth/login` - Iniciar sesión
- `POST /auth/logout` - Cerrar sesión

### Propiedades
- `GET /properties` - Listar propiedades
- `GET /properties/<id>` - Ver detalle de propiedad
- `POST /properties` - Crear nueva propiedad (requiere autenticación)
- `PUT /properties/<id>` - Actualizar propiedad
- `DELETE /properties/<id>` - Eliminar propiedad

### Pagos
- `POST /payment/process` - Iniciar proceso de pago
- `GET /payment/status/<job_id>` - Consultar estado de pago

## 🧪 Pruebas

Para ejecutar las pruebas:

```bash
pytest tests/
```

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## ✨ Características Futuras

- [ ] Sistema de notificaciones en tiempo real con WebSockets
- [ ] Integración con pasarelas de pago externas
- [ ] Búsqueda avanzada con filtros
- [ ] Panel de administración mejorado
- [ ] Documentación de API con Swagger/OpenAPI

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor, lee las [pautas de contribución](CONTRIBUTING.md) para más detalles.

## 📞 Contacto

Para consultas o soporte, contactar al equipo de desarrollo.

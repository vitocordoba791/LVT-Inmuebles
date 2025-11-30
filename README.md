# 🏠 LVT Inmuebles - Sistema Inmobiliario con Concurrencia y Tiempo Real

Aplicación web completa para gestión de propiedades inmobiliarias con procesamiento asíncrono, notificaciones en tiempo real y control de acceso por roles.

## 🚀 **Características Principales**

### 🏡 **Gestión de Propiedades**
- Publicación y edición de propiedades
- Galería de imágenes con vistas múltiples
- Búsqueda y filtrado avanzado
- Sistema de paginación eficiente
- Estado de venta (disponible/vendida)

### 👥 **Sistema de Usuarios con Roles**
- **Usuarios Regulares**: Pueden ver propiedades y publicar las suyas
- **Administradores**: Gestión completa de usuarios y propiedades
- **Propietarios**: Control sobre sus propias propiedades

### 💳 **Procesamiento de Pagos**
- Pagos asíncronos con hilos daemon
- Simulación de pasarelas de pago
- Estado en tiempo real del procesamiento
- Confirmación automática de ventas

### 🔄 **Notificaciones en Tiempo Real**
- WebSockets con Socket.IO
- Notificaciones instantáneas de cambios de rol
- Alertas de desactivación de cuentas
- Actualización automática de permisos

### 🛡️ **Seguridad Avanzada**
- Hashing de contraseñas con Werkzeug
- Decoradores de acceso por rol
- Validación de estado de cuenta
- Protección CSRF y sanitización

---

## 📁 **Estructura del Proyecto**

```
LVT-Inmuebles/
├── app/
│   ├── __init__.py          # Fábrica de aplicaciones y WebSockets
│   ├── models.py            # Modelos de base de datos
│   ├── auth_utils.py        # Decoradores de seguridad
│   ├── tasks.py             # Sistema de concurrencia con hilos
│   ├── routes/              # Controladores/endpoints
│   │   ├── __init__.py
│   │   ├── auth.py          # Autenticación y administración
│   │   ├── main.py          # Página principal
│   │   ├── propiedades.py   # CRUD de propiedades
│   │   └── pago.py          # Procesamiento de pagos
│   ├── static/              # Assets frontend
│   │   ├── css/
│   │   ├── js/
│   │   └── uploads/
│   └── templates/           # Vistas Jinja2
│       ├── base.html
│       ├── auth/
│       ├── propiedades/
│       └── admin/
├── migrations/              # Versiones de base de datos
├── instance/                # Base de datos SQLite
├── requirements.txt        # Dependencias
└── run.py                   # Punto de entrada
```

---

## 🔄 **Sistema de Concurrencia**

### 🧵 **Arquitectura de Hilos**

El sistema implementa un patrón **Worker Pool** con hilos daemon para procesar tareas de larga duración sin bloquear el hilo principal de la aplicación web.

#### **Variables Globales de Control**
```python
_trabajos: Dict[str, Dict[str, Any]] = {}  # Almacena estado de los trabajos
_bloqueo = Lock()                            # Mutex para acceso seguro
```

#### **Flujo de Ejecución Concurrente**

1. **Envío de Trabajo** (`enviar_trabajo`)
   - Genera ID único con UUID4
   - Registra estado inicial (thread-safe)
   - Inicia hilo daemon con la tarea

2. **Ejecución en Hilo Separado**
   - Crea contexto de aplicación Flask
   - Ejecuta la función target
   - Actualiza estado con resultado/error
   - Manejo de excepciones seguro

3. **Seguimiento de Estado** (`obtener_estado_trabajo`)
   - Consulta estado en memoria compartida
   - Retorna: ejecutando, completado, error, no_encontrado

#### **Procesamiento de Pagos Asíncrono**
```python
def _procesar_pago(pago_id: int) -> Dict[str, Any]:
    # Simulación de pasarela de pago
    sleep(2)  # Delay de procesamiento
    
    # Actualización atómica de DB
    pago.estado = 'completado'
    pago.propiedad.vendida = True
    session.commit()
```

**Beneficios:**
- ✅ Non-blocking: UI no se congela
- ✅ Paralelismo: Múltiples pagos simultáneos
- ✅ Escalabilidad: Hilos daemon no bloquean servidor

---

## 🌐 **WebSockets y Tiempo Real**

### **Gestión de Salas Privadas**
```python
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')  # Sala única por usuario
```

### **Eventos en Tiempo Real**

#### **1. Cambio de Rol de Administrador**
```python
@auth_bp.route('/admin/usuario/<int:usuario_id>/toggle_admin')
def toggle_admin(usuario_id):
    usuario.es_administrador = not usuario.es_administrador
    db.session.commit()
    
    # Notificación inmediata
    if usuario.es_administrador:
        socketio.emit('rol_admin_asignado', 
                     {'mensaje': '¡Felicidades! Se te han asignado permisos de administrador.'},
                     room=f'user_{usuario_id}')
```

#### **2. Desactivación de Cuenta**
```python
@auth_bp.route('/admin/usuario/<int:usuario_id>/toggle_estado')
def toggle_estado(usuario_id):
    usuario.activo = not usuario.activo
    db.session.commit()
    
    if not usuario.activo:
        socketio.emit('cuenta_desactivada', 
                     {'mensaje': 'Tu cuenta ha sido desactivada.'},
                     room=f'user_{usuario_id}')
```

### **Manejo en Frontend**
```javascript
// Recepción de eventos
socket.on('rol_admin_asignado', function(data) {
    // Toast verde + recarga automática
    setTimeout(() => window.location.reload(), 2000);
});

socket.on('cuenta_desactivada', function(data) {
    // Modal rojo + logout forzado
    window.location.href = "/auth/logout";
});
```

---

## 🛡️ **Sistema de Seguridad**

### 🔐 **Hashing de Contraseñas**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def establecer_password(self, password):
    self.password_hash = generate_password_hash(password)  # Nunca texto plano

def verificar_password(self, password):
    if not self.activo:
        return False  # Usuarios inactivos bloqueados
    return check_password_hash(self.password_hash, password)
```

### 🛡️ **Decoradores de Acceso**

#### **1. Requerir Autenticación**
```python
@login_required
def mi_ruta():
    # Solo usuarios logueados
```

#### **2. Requerir Rol de Administrador**
```python
@admin_required
def ruta_admin():
    # Solo administradores
    if not current_user.es_admin:
        flash('Acceso denegado', 'danger')
        return redirect(url_for('main.index'))
```

#### **3. Propietario o Administrador**
```python
@propietario_o_admin_required
def editar_propiedad(propiedad_id):
    # Solo propietario o admin pueden editar
    if not (current_user.es_admin or propiedad.propietario_id == current_user.id):
        flash('No tienes permiso', 'danger')
        return redirect(url_for('main.index'))
```

### 🔒 **Validaciones de Seguridad**
- ✅ Verificación de estado de cuenta (activo/inactivo)
- ✅ Sanitización de inputs
- ✅ Protección CSRF
- ✅ Sesiones seguras con Flask-Login
- ✅ Control de acceso por recurso

---

## 👥 **Sistema de Roles**

### 🎭 **Rol: Usuario Regular**
**Permisos:**
- ✅ Ver todas las propiedades disponibles
- ✅ Buscar y filtrar propiedades
- ✅ Publicar propiedades propias
- ✅ Editar sus propias propiedades
- ✅ Procesar pagos de propiedades

**Restricciones:**
- ❌ No puede ver propiedades vendidas
- ❌ No puede acceder al panel de administración
- ❌ No puede gestionar otros usuarios

### 🛡️ **Rol: Administrador**
**Permisos:**
- ✅ Todos los permisos de usuario regular
- ✅ Acceso al panel de administración
- ✅ Gestionar usuarios (activar/desactivar)
- ✅ Asignar/revocar roles de administrador
- ✅ Ver todas las propiedades (incluidas vendidas)
- ✅ Eliminar cualquier propiedad

**Funciones Especiales:**
- 🔄 Notificaciones en tiempo real de cambios
- 📊 Estadísticas del sistema
- 👥 Gestión completa de usuarios

### 🏠 **Rol: Propietario**
**Permisos:**
- ✅ Ver propiedades propias (vendidas incluidas)
- ✅ Editar solo sus propiedades
- ✅ Ver sus propios pagos
- ✅ Contactar vendedores de otras propiedades

**Restricciones:**
- ❌ No puede editar propiedades ajenas
- ❌ No puede acceder a funciones administrativas

---

## 🚀 **Instalación y Ejecución**

### **Prerrequisitos**
- Python 3.8+
- pip (gestor de paquetes)

### **Pasos de Instalación**

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd LVT-Inmuebles
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con SECRET_KEY y DATABASE_URL
```

5. **Inicializar base de datos**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. **Ejecutar aplicación**
```bash
python run.py
```

La aplicación estará disponible en `http://localhost:5000`

---

## 📊 **Flujos de Uso Principales**

### 🔄 **Flujo de Cambio de Rol en Tiempo Real**
```
1. Admin accede → /auth/admin/usuarios
2. Cambia rol → Botón "Hacer Admin"/"Quitar Admin"
3. DB actualiza → usuario.es_administrador = True/False
4. Socket.IO emite → rol_admin_asignado/revocado
5. Cliente recibe → socket.on('rol_admin_asignado')
6. UI actualiza → Toast + recarga automática
7. Permisos activos → Nuevo rol disponible inmediatamente
```

### 💳 **Flujo de Procesamiento de Pago**
```
1. Usuario selecciona → Botón "Comprar Propiedad"
2. Sistema crea → Pago con estado 'pendiente'
3. Tarea enviada → enviar_trabajo(_procesar_pago)
4. Hilo iniciado → Thread daemon procesa pago
5. Simulación → sleep(2) + actualización DB
6. Estado final → pago.estado = 'completado'
7. Propiedad vendida → propiedad.vendida = True
8. Notificación → Redirect con confirmación
```

### 🛡️ **Flujo de Desactivación de Usuario**
```
1. Admin desactiva → toggle_estado(usuario_id)
2. DB actualiza → usuario.activo = False
3. Socket.IO emite → cuenta_desactivada
4. Usuario notificado → Modal rojo inmediato
5. Sesión cerrada → Logout forzado
6. Login bloqueado → verificar_password() retorna False
```

---

## 🔧 **Tecnologías Utilizadas**

### **Backend**
- **Flask**: Framework web principal
- **Flask-SQLAlchemy**: ORM para base de datos
- **Flask-Login**: Gestión de sesiones
- **Flask-Migrate**: Migraciones de DB
- **Flask-SocketIO**: WebSockets para tiempo real
- **Werkzeug**: Hashing de contraseñas

### **Frontend**
- **Bootstrap 5**: Framework CSS
- **JavaScript**: Interactividad cliente
- **Socket.IO Client**: Comunicación WebSocket
- **Jinja2**: Templates HTML

### **Base de Datos**
- **SQLite**: Base de datos ligera
- **Alembic**: Sistema de migraciones

### **Concurrencia**
- **Threading**: Hilos Python estándar
- **Lock**: Sincronización de recursos
- **UUID**: Identificación única de tareas

---

## 📈 **Características Técnicas Destacadas**

### 🔄 **Concurrencia Avanzada**
- Hilos daemon para tareas background
- Mutex para acceso thread-safe
- Estado compartido en memoria
- Contexto de aplicación en hilos

### 🌐 **Tiempo Real**
- WebSockets bidireccionales
- Salas privadas por usuario
- Eventos instantáneos
- Sincronización de estado

### 🛡️ **Seguridad Robusta**
- Hashing BCrypt de contraseñas
- Decoradores de acceso granular
- Validación de estado de cuenta
- Control de recursos por rol

### 📱 **UX Moderna**
- Interfaz responsiva
- Notificaciones no intrusivas
- Actualizaciones automáticas
- Feedback visual inmediato

---

## 🤝 **Contribución**

1. Fork del proyecto
2. Crear feature branch (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push al branch (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

---

## 📞 **Contacto y Soporte**

Para consultas técnicas, reporte de bugs o sugerencias:
- **Issues**: GitHub repository
- **Documentation**: Wiki del proyecto
- **Email**: equipo de desarrollo

---

**LVT Inmuebles** - Transformando la gestión inmobiliaria con tecnología moderna y experiencia de usuario excepcional.

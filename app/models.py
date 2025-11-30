from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Importar la instancia de la base de datos desde __init__.py
from . import db


class Usuario(UserMixin, db.Model):
    # Modelo de usuario - Gestiona autenticación, roles y estado de cuenta
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # Hash de contraseña
    es_administrador = db.Column(db.Boolean, default=False, nullable=False)  # Permisos de administrador
    activo = db.Column(db.Boolean, default=True, nullable=False)  # Estado de la cuenta (activa/desactivada)
    
    # Relaciones con otras tablas  / Claves Forananeas
    propiedades = db.relationship('Propiedad', backref='propietario', lazy=True)
    pagos = db.relationship('Pago', backref='usuario', lazy=True, order_by='desc(Pago.fecha_creacion)')

    def establecer_password(self, password):
        # Crea un hash de la contraseña y lo almacena
        self.password_hash = generate_password_hash(password)

    def verificar_password(self, password):
        # Verifica la contraseña y el estado de la cuenta
        if not self.activo:
            return False  # Usuarios inactivos no pueden iniciar sesión
        return check_password_hash(self.password_hash, password)
        
    @property
    def es_admin(self):
        # Propiedad conveniente para verificar si es administrador
        return self.es_administrador


class Propiedad(db.Model):
    # Modelo de propiedad inmobiliaria - Almacena detalles de las propiedades publicadas
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    metros_cuadrados = db.Column(db.Float, nullable=False, default=0)
    habitaciones = db.Column(db.Integer, nullable=False, default=0)
    banos = db.Column(db.Integer, nullable=False, default=0)
    estacionamientos = db.Column(db.Integer, nullable=False, default=0)
    vendida = db.Column(db.Boolean, default=False, nullable=False)  # Estado de venta
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Clave foránea que relaciona con el usuario propietario
    propietario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Relación con pagos asociados a esta propiedad
    pagos = db.relationship('Pago', backref='propiedad', lazy=True, order_by='desc(Pago.fecha_creacion)')
    
    def marcar_como_vendida(self):
        # Marca la propiedad como vendida y guarda en la base de datos
        self.vendida = True
        db.session.commit()
        return self


class Pago(db.Model):
    # Modelo de pago - Registra las transacciones de compra de propiedades
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(50), default='pendiente')  # pendiente, completado, fallido
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Claves foráneas para relacionar con usuario y propiedad
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    propiedad_id = db.Column(db.Integer, db.ForeignKey('propiedad.id'), nullable=False)
    
    def marcar_como_pagado(self):
        # Marca el pago como pagado y guarda en la base de datos
        self.estado = 'pagado'
        db.session.commit()
        return self

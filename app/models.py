from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    propiedades = db.relationship('Propiedad', backref='propietario', lazy=True)
    pagos = db.relationship('Pago', backref='usuario', lazy=True)

    def establecer_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verificar_password(self, password):
        return check_password_hash(self.password_hash, password)


class Propiedad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    metros_cuadrados = db.Column(db.Float, nullable=False, default=0)
    habitaciones = db.Column(db.Integer, nullable=False, default=0)
    banos = db.Column(db.Integer, nullable=False, default=0)
    estacionamientos = db.Column(db.Integer, nullable=False, default=0)
    vendida = db.Column(db.Boolean, default=False, nullable=False)
    propietario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    pagos = db.relationship('Pago', backref='propiedad', lazy=True, order_by='desc(Pago.fecha_creacion)')
    
    def marcar_como_vendida(self):
        self.vendida = True
        db.session.commit()
        return self


class Pago(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='pendiente')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    propiedad_id = db.Column(db.Integer, db.ForeignKey('propiedad.id'), nullable=False)
    
    def marcar_como_pagado(self):
        self.estado = 'pagado'
        db.session.commit()
        return self

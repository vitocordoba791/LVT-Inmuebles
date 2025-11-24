import sqlite3  
   
    --  Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    gmail TEXT UNIQUE NOT NULL,
    contraseña TEXT NOT NULL
);
--  Tabla de inmuebles

CREATE TABLE IF NOT EXISTS inmuebles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    direccion TEXT,
    tipo TEXT CHECK (tipo IN ('venta', 'alquiler')) NOT NULL,
    precio REAL NOT NULL,
    disponible INTEGER DEFAULT 1,
    id_propietario INTEGER,
    imagen_url TEXT,
    FOREIGN KEY (id_propietario) REFERENCES usuarios (id)
);


 -- Tabla de transacciones

CREATE TABLE IF NOT EXISTS transacciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    id_inmueble INTEGER NOT NULL,
    tipo_operacion TEXT CHECK (tipo_operacion IN ('compra', 'alquiler')),
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    monto REAL,
    estado TEXT CHECK (estado IN ('pendiente', 'completada', 'cancelada')) DEFAULT 'pendiente',
    FOREIGN KEY (id_usuario) REFERENCES usuarios (id),
    FOREIGN KEY (id_inmueble) REFERENCES inmuebles (id)
);

--  Tabla de alquileres
CREATE TABLE IF NOT EXISTS alquileres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_inquilino INTEGER NOT NULL,
    id_inmueble INTEGER NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    monto_mensual REAL NOT NULL,
    activo INTEGER DEFAULT 1,
    FOREIGN KEY (id_inquilino) REFERENCES usuarios (id),
    FOREIGN KEY (id_inmueble) REFERENCES inmuebles (id)
);

--  Tabla de pagos
CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_alquiler INTEGER NOT NULL,
    fecha_pago DATETIME DEFAULT CURRENT_TIMESTAMP,
    monto REAL NOT NULL,
    metodo_pago TEXT,
    FOREIGN KEY (id_alquiler) REFERENCES alquileres (id)
);

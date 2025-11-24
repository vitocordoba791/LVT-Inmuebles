import sqlite3

# Conexión o creación de la base de datos
conexion = sqlite3.connect("inmobiliaria.db")
cursor = conexion.cursor()

# Si ya existe la tabla, la borramos
cursor.execute("DROP TABLE IF EXISTS usuarios")

# Creamos la tabla correctamente
cursor.execute("""
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    gmail TEXT UNIQUE NOT NULL,
    contraseña TEXT NOT NULL
)
""")

conexion.commit()
conexion.close()

print("✅ Tabla 'usuarios' creada correctamente.")

import sqlite3

def crear_bd():
    with open('schema.sql', 'r', encoding='utf-8') as f:
        schema = f.read()

    conexion = sqlite3.connect('inmobiliaria.db')
    cursor = conexion.cursor()
    cursor.executescript(schema)
    conexion.commit()
    conexion.close()
    print("✅ Base de datos 'inmobiliaria.db' creada correctamente.")

if __name__ == "__main__":
    crear_bd()
    
import sqlite3
conexion = sqlite3.connect('inmobiliaria.db')
cursor = conexion.cursor()
cursor.execute("INSERT INTO usuarios (nombre, email, contrasena, rol) VALUES (?, ?, ?, ?)",
               ("Admin", "admin@correo.com", "1234", "admin"))
conexion.commit()
conexion.close()
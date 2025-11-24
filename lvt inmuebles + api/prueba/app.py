from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import mercadopago

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'  # 🔐 necesaria para sesiones

# --- Configuración Mercado Pago ---
sdk = mercadopago.SDK("TEST-3908467500595389-112415-b19fca487bda461f3aba525c632aa90c-1434219177")

# --- Ruta para crear un pago ---
@app.route("/crear_pago")
def crear_pago():

    preference_data = {
        "items": [
            {
                "title": "Producto de prueba",
                "quantity": 1,
                "unit_price": 1000.0
            }
        ]
    }

    response = sdk.preference().create(preference_data)
    init_point = response["response"]["init_point"]

    return jsonify({"link_de_pago": init_point})


# --- Conexión con base de datos ---
def obtener_conexion():
    conexion = sqlite3.connect('inmobiliaria.db')
    conexion.row_factory = sqlite3.Row
    return conexion

# --- Página principal ---
@app.route('/')
def inicio():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM inmuebles WHERE disponible = 1")
    inmuebles = cursor.fetchall()
    conexion.close()
    return render_template('index.html', inmuebles=inmuebles)

# --- Página de login ---
@app.route('/login')
def login():
    return render_template('login.html')

# --- Registro ---
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        gmail = request.form['gmail']
        contraseña = request.form['contraseña']

        conexion = obtener_conexion()
        cursor = conexion.cursor()

        try:
            cursor.execute("""
                INSERT INTO usuarios (nombre, apellido, gmail, contraseña)
                VALUES (?, ?, ?, ?)
            """, (nombre, apellido, gmail, contraseña))
            conexion.commit()
            conexion.close()
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            return "<h3>El correo ya está registrado. <a href='/registro'>Intentar de nuevo</a></h3>"
    
    return render_template('registro.html')

# --- Verificar login ---
@app.route('/verificar_login', methods=['POST'])
def verificar_login():
    gmail = request.form['gmail']
    contraseña = request.form['contraseña']

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE gmail = ? AND contraseña = ?", (gmail, contraseña))
    usuario = cursor.fetchone()
    conexion.close()

    if usuario:
        session['usuario'] = usuario['nombre']
        return redirect(url_for('inicio'))
    else:
        return "<h2>Usuario o contraseña incorrectos</h2><a href='/login'>Volver</a>"

# --- Agregar inmueble ---
@app.route('/agregar', methods=['GET', 'POST'])
def agregar_inmueble():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        direccion = request.form['direccion']
        tipo = request.form['tipo']
        precio = request.form['precio']

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO inmuebles (titulo, descripcion, direccion, tipo, precio, disponible)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (titulo, descripcion, direccion, tipo, precio))
        conexion.commit()
        conexion.close()

        return redirect(url_for('inicio'))
    return render_template('agregar.html')

# --- Logout ---
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('inicio'))

# --- Iniciar servidor ---
if __name__ == "__main__":
    app.run(debug=True)

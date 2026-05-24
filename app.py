import pyodbc
from werkzeug.security import generate_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'KeyInstitute_Security_2026'

# --- CONEXIÓN A BASE DE DATOS ---
def get_db_connection():
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=GOGUILPTP\\SQLEXPRESS;'
        'DATABASE=KeyInstituteDB;'
        'Trusted_Connection=yes;'
    )
    return pyodbc.connect(conn_str)

# --- RUTA DE LOGIN (CON REDIRECCIÓN POR ROL) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        # Redirección inteligente si ya existe una sesión activa
        rol = session.get('rol')
        if rol == 'Admin':
            return redirect(url_for('panel_admin'))
        elif rol == 'Maestro':
            return redirect(url_for('panel_profesor'))
        else:
            return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validación de dominio institucional
        if not email.endswith('@keyinstitute.edu.sv'):
            flash('Debes usar tu correo @keyinstitute.edu.sv', 'danger')
            return redirect(url_for('login'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Buscamos al usuario por sus credenciales
            cursor.execute("SELECT id_usuario, nombre, rol FROM Usuarios WHERE email = ? AND password = ?", (email, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                # Guardamos los datos en la sesión
                session['user_id'] = user[0]
                session['username'] = user[1] 
                session['rol'] = user[2]
                
                # REDIRECCIÓN SEGÚN ROL (Punto clave para Erick Varela)
                if user[2] == 'Admin':
                    return redirect(url_for('panel_admin'))
                elif user[2] == 'Maestro':
                    return redirect(url_for('panel_profesor'))
                else:
                    # Estudiantes o usuarios por defecto
                    return redirect(url_for('index'))
            else:
                flash('Correo o contraseña incorrectos.', 'danger')
        except Exception as e:
            flash(f'Error de conexión: {str(e)}', 'danger')
            
    return render_template('login.html')

# --- RUTA PARA PROCESAR LOS REPORTES (MODALES) ---
@app.route('/crear_reporte', methods=['POST'])
def crear_reporte():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Recibimos los datos de los nombres (name="") que pusimos en el HTML
    tipo = request.form.get('tipo')
    descripcion = request.form.get('descripcion')
    prioridad = request.form.get('prioridad')
    categoria = request.form.get('categoria')
    titulo = request.form.get('titulo', 'Sin título')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Reportes (tipo, categoria, titulo, descripcion, prioridad, id_usuario)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (tipo, categoria, titulo, descripcion, prioridad, session['user_id']))
        conn.commit()
        conn.close()
        flash('Reporte enviado correctamente. ¡Gracias por tu aporte!', 'success')
    except Exception as e:
        flash(f'Error al enviar reporte: {str(e)}', 'danger')

    return redirect(url_for('index'))

# --- VISTA DEL ALUMNO ---
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Si un maestro intenta entrar aquí, lo mandamos a su panel
    if session.get('rol') == 'Maestro':
        return redirect(url_for('panel_profesor'))

    return render_template('index.html', nombre_usuario=session['username'])

# --- VISTA DEL PROFESOR ---
@app.route('/panel_profesor')
def panel_profesor():
    # ... validación de sesión ...
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # IMPORTANTE: Seleccionamos 7 columnas (del 0 al 6)
    # R.id_reporte será r[6]
    cursor.execute("""
        SELECT R.tipo, R.titulo, R.descripcion, R.prioridad, R.fecha_creacion, U.nombre, R.id_reporte
        FROM Reportes R
        JOIN Usuarios U ON R.id_usuario = U.id_usuario
        ORDER BY R.fecha_creacion DESC
    """)
    reportes = cursor.fetchall()
    conn.close()
    return render_template('profesor.html', reportes=reportes)

@app.route('/responder_reporte/<int:id_reporte>', methods=['POST'])
def responder_reporte(id_reporte):
    if 'user_id' not in session or session.get('rol') != 'Maestro':
        return redirect(url_for('login'))

    respuesta = request.form.get('respuesta')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Guardamos la respuesta en la nueva tabla
        cursor.execute("""
            INSERT INTO Respuestas (id_reporte, mensaje_respuesta)
            VALUES (?, ?)
        """, (id_reporte, respuesta))
        
        # 2. Opcional: Cambiamos el estado del reporte a 'Resuelto'
        cursor.execute("UPDATE Reportes SET estado = 'Resuelto' WHERE id_reporte = ?", (id_reporte,))
        
        conn.commit()
        conn.close()
        flash('Respuesta enviada y reporte actualizado', 'success')
    except Exception as e:
        flash(f'Error al responder: {str(e)}', 'danger')

    return redirect(url_for('panel_profesor'))

@app.route('/bandeja_estudiante')
def bandeja_estudiante():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # SIMULACIÓN DE DATOS PARA LA PRESENTACIÓN
    # En un caso real, aquí harías el SELECT a tu tabla de Respuestas
    respuestas_inventadas = [
        {
            'titulo_reporte': 'Pérdida de teléfono móvil',
            'mensaje': 'Hola David, ya revisamos las cámaras de seguridad. El dispositivo fue encontrado en la dirección y puedes pasar por él a la oficina de coordinación.',
            'fecha': '12/05/2026 - 10:30 AM'
        }
    ]

    return render_template('bandeja.html', respuestas=respuestas_inventadas)

@app.route('/panel_admin')
def panel_admin():
    if 'user_id' not in session or session.get('rol') != 'Admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Obtenemos todos los usuarios excepto al admin actual para evitar auto-bloqueo
    cursor.execute("SELECT id_usuario, nombre, email, rol FROM Usuarios WHERE rol != 'Admin'")
    usuarios = cursor.fetchall()
    conn.close()
    
    return render_template('admin.html', usuarios=usuarios)

@app.route('/cambiar_rol/<int:id_usuario>', methods=['POST'])
def cambiar_rol(id_usuario):
    if 'user_id' not in session or session.get('rol') != 'Admin':
        return redirect(url_for('login'))
    
    nuevo_rol = request.form.get('nuevo_rol')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Usuarios SET rol = ? WHERE id_usuario = ?", (nuevo_rol, id_usuario))
    conn.commit()
    conn.close()
    
    flash('Rol actualizado correctamente', 'success')
    return redirect(url_for('panel_admin'))

@app.route('/agregar_usuario', methods=['POST'])
def agregar_usuario():
    if 'user_id' not in session or session.get('rol') != 'Admin':
        return redirect(url_for('login'))

    correo = request.form['correo'].strip().lower()
    password = request.form['password']

    nombre = correo.split('@')[0]
    nombre = nombre.replace('.', ' ').replace('_', ' ').replace('-', ' ')
    nombre = nombre.title()
    nombre = nombre.replace('Deleon', 'de León')

    rol = 'Alumno'

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Usuarios (nombre, email, [password], rol)
            VALUES (?, ?, ?, ?)
        """, (nombre, correo, password, rol))

        conn.commit()
        conn.close()

        flash('Usuario agregado correctamente.', 'success')

    except Exception as e:
        flash(f'Error al agregar usuario: {str(e)}', 'danger')

    return redirect(url_for('panel_admin'))


# --- CERRAR SESIÓN ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/eliminar_usuario', methods=['POST'])
def eliminar_usuario():
    if 'user_id' not in session or session.get('rol') != 'Admin':
        return redirect(url_for('login'))

    id_usuario = request.form.get('id_usuario')

    if not id_usuario:
        return redirect(url_for('panel_admin'))

    id_usuario = int(id_usuario)

    # Evita que el admin se borre a sí mismo
    if id_usuario == session.get('user_id'):
        return redirect(url_for('panel_admin'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM Usuarios
        WHERE id_usuario = ? AND rol != 'Admin'
    """, (id_usuario,))

    conn.commit()
    conn.close()

    return redirect(url_for('panel_admin'))


if __name__ == '__main__':
    app.run(debug=True)
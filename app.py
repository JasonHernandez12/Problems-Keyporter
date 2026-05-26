
import os
import re
import smtplib
import secrets
import string
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
    
import pyodbc
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
import google.generativeai as genai
from werkzeug.utils import secure_filename
import PIL.Image

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'KeyInstitute_Security_2026')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads', 'foro')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx', 'xlsx', 'zip', 'rar'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = os.getenv('OUTLOOK_EMAIL')
SMTP_PASSWORD = os.getenv('OUTLOOK_PASSWORD')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# CONEXIÓN A BASE DE DATOS
# ============================================================
def get_db_connection():
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=7GUERRERO\\SQLEXPRESS;'
        'DATABASE=KeyInstituteDB;'
        'Trusted_Connection=yes;'
    )
    return pyodbc.connect(conn_str)


# ============================================================
# UTILIDADES DE RECUPERACIÓN DE CONTRASEÑA
# ============================================================
def generar_password_aleatoria(longitud=12):
    """Genera una contraseña alfanumérica segura."""
    alfabeto = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alfabeto) for _ in range(longitud))


def validar_estructura_email(email):
    """Valida formato básico de correo electrónico."""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None


def enviar_correo_recuperacion(destinatario, enlace_recuperacion):
    if not SMTP_USER or not SMTP_PASSWORD:
        print("\n" + "="*60)
        print("📧 CORREO DE RECUPERACIÓN (MODO DEMO)")
        print("="*60)
        print(f"📬 Para: {destinatario}")
        print(f"🔗 Enlace de recuperación: {enlace_recuperacion}")
        print("="*60)
        print("ℹ️  Para envío real, configura OUTLOOK_EMAIL y OUTLOOK_PASSWORD en .env")
        print("="*60 + "\n")
        logger.info(f"[DEMO] Correo simulado a {destinatario}")
        return True, "Correo enviado (modo demo)."

    mensaje = MIMEMultipart('alternative')
    mensaje['Subject'] = 'Recuperación de Contraseña - Key Institute'
    mensaje['From'] = SMTP_USER
    mensaje['To'] = destinatario

    cuerpo_html = f"""
    <html>
      <body style="font-family: Segoe UI, sans-serif; background:#f4f4f4; padding:20px;">
        <div style="max-width:500px; margin:auto; background:white; padding:30px; border-radius:12px; box-shadow:0 4px 10px rgba(0,0,0,0.08);">
          <h2 style="color:#1d4ed8;">Key Institute</h2>
          <p>Hola,</p>
          <p>Hemos recibido una solicitud para restablecer tu contraseña. Haz clic en el siguiente enlace para continuar:</p>
          <div style="text-align:center; margin-top:25px; margin-bottom:25px;">
            <a href="{enlace_recuperacion}" style="background:#1d4ed8; color:white; padding:12px 24px; text-decoration:none; border-radius:8px; font-weight:bold; display:inline-block;">Restablecer Contraseña</a>
          </div>
          <p style="margin-top:20px; font-size: 14px; color: #666;">Si el botón no funciona, copia y pega esta dirección en tu navegador:</p>
          <p style="font-size: 12px; word-break: break-all; color: #666;">{enlace_recuperacion}</p>
          <p style="margin-top:20px;">Este enlace expirará en 1 hora. Si no solicitaste este cambio, puedes ignorar este correo.</p>
        </div>
      </body>
    </html>
    """
    mensaje.attach(MIMEText(cuerpo_html, 'html'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, destinatario, mensaje.as_string())
        logger.info(f"Correo enviado a {destinatario}")
        return True, "Correo enviado."
    except Exception as e:
        logger.error(f"Error SMTP: {e}")
        return False, "Error al enviar el correo."


# ============================================================
# RUTA DE LOGIN
# ============================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
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

        if not email.endswith('@keyinstitute.edu.sv'):
            flash('Debes usar tu correo @keyinstitute.edu.sv', 'danger')
            return redirect(url_for('login'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id_usuario, nombre, rol, password FROM Usuarios WHERE email = ?", (email,))
            user = cursor.fetchone()
            conn.close()

            if user:
                stored_password = user[3]
                is_valid_password = False
                if stored_password.startswith('scrypt:') or stored_password.startswith('pbkdf2:'):
                    is_valid_password = check_password_hash(stored_password, password)
                else:
                    is_valid_password = (stored_password == password)

                if is_valid_password:
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    session['rol'] = user[2]

                    if user[2] == 'Admin':
                        return redirect(url_for('panel_admin'))
                    elif user[2] == 'Maestro':
                        return redirect(url_for('panel_profesor'))
                    else:
                        return redirect(url_for('index'))
                else:
                    flash('Correo o contraseña incorrectos.', 'danger')
            else:
                flash('Correo o contraseña incorrectos.', 'danger')
        except Exception as e:
            flash(f'Error de conexión: {str(e)}', 'danger')

    return render_template('login.html')


# ============================================================
# RUTA DE RECUPERACIÓN DE CONTRASEÑA
# ============================================================
@app.route('/recover-password', methods=['POST'])
def recover_password():
    data = request.get_json()
    email = (data.get('email') or '').strip().lower()

    if not validar_estructura_email(email):
        return jsonify({'success': False, 'message': 'Formato de correo inválido.'}), 400

    if not email.endswith('@keyinstitute.edu.sv'):
        return jsonify({'success': False, 'message': 'Debes usar tu correo @keyinstitute.edu.sv'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_usuario FROM Usuarios WHERE email = ?", (email,))
        usuario = cursor.fetchone()

        if not usuario:
            conn.close()
            return jsonify({'success': True, 'message': 'Si el correo existe, recibirás un mensaje.'})

        conn.close()

        s = URLSafeTimedSerializer(app.secret_key)
        token = s.dumps(email, salt='password-recovery')
        enlace_recuperacion = url_for('reset_password', token=token, _external=True)
        enviado, mensaje = enviar_correo_recuperacion(email, enlace_recuperacion)

        if enviado:
            return jsonify({'success': True, 'message': 'Correo enviado correctamente.'})
        else:
            return jsonify({'success': False, 'message': mensaje}), 500

    except Exception as e:
        logger.error(f"Error en recuperación de contraseña: {e}")
        return jsonify({'success': False, 'message': 'Error en el servidor.'}), 500


# ============================================================
# RUTA DE RESTABLECIMIENTO CON TOKEN
# ============================================================
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = URLSafeTimedSerializer(app.secret_key)
    try:
        email = s.loads(token, salt='password-recovery', max_age=3600)
    except Exception as e:
        flash('El enlace de recuperación es inválido o ha expirado.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not new_password or new_password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('reset_password.html', token=token)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            hashed_password = generate_password_hash(new_password)
            cursor.execute("UPDATE Usuarios SET password = ? WHERE email = ?", (hashed_password, email))
            conn.commit()
            conn.close()
            flash('Tu contraseña ha sido actualizada correctamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error al actualizar la contraseña: {str(e)}', 'danger')
            return render_template('reset_password.html', token=token)

    return render_template('reset_password.html', token=token)


# ============================================================
# RUTA PARA PROCESAR LOS REPORTES
# ============================================================
@app.route('/crear_reporte', methods=['POST'])
def crear_reporte():
    if 'user_id' not in session:
        return redirect(url_for('login'))

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


# ============================================================
# VISTA DEL ALUMNO
# ============================================================
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('rol') == 'Maestro':
        return redirect(url_for('panel_profesor'))

    return render_template('index.html', nombre_usuario=session['username'])


# ============================================================
# VISTA DEL PROFESOR
# ============================================================
@app.route('/panel_profesor')
def panel_profesor():
    conn = get_db_connection()
    cursor = conn.cursor()
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
        cursor.execute("""
            INSERT INTO Respuestas (id_reporte, mensaje_respuesta)
            VALUES (?, ?)
        """, (id_reporte, respuesta))
        cursor.execute("UPDATE Reportes SET estado = 'Resuelto' WHERE id_reporte = ?", (id_reporte,))
        conn.commit()
        conn.close()
        flash('Respuesta enviada y reporte actualizado', 'success')
    except Exception as e:
        flash(f'Error al responder: {str(e)}', 'danger')

    return redirect(url_for('panel_profesor'))


# ============================================================
# BANDEJA DEL ESTUDIANTE
# ============================================================
@app.route('/bandeja_estudiante')
def bandeja_estudiante():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    respuestas_inventadas = [
        {
            'titulo_reporte': 'Pérdida de teléfono móvil',
            'mensaje': 'Hola David, ya revisamos las cámaras de seguridad. El dispositivo fue encontrado en la dirección y puedes pasar por él a la oficina de coordinación.',
            'fecha': '12/05/2026 - 10:30 AM'
        }
    ]
    return render_template('bandeja.html', respuestas=respuestas_inventadas)


# ============================================================
# PANEL DE ADMINISTRADOR
# ============================================================
@app.route('/panel_admin')
def panel_admin():
    if 'user_id' not in session or session.get('rol') != 'Admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
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

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Usuarios (nombre, email, [password], rol)
            VALUES (?, ?, ?, ?)
        """, (nombre, correo, password, 'Alumno'))
        conn.commit()
        conn.close()
        flash('Usuario agregado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al agregar usuario: {str(e)}', 'danger')

    return redirect(url_for('panel_admin'))


@app.route('/eliminar_usuario', methods=['POST'])
def eliminar_usuario():
    if 'user_id' not in session or session.get('rol') != 'Admin':
        return redirect(url_for('login'))

    id_usuario = request.form.get('id_usuario')
    if not id_usuario:
        return redirect(url_for('panel_admin'))

    id_usuario = int(id_usuario)
    if id_usuario == session.get('user_id'):
        return redirect(url_for('panel_admin'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Usuarios WHERE id_usuario = ? AND rol != 'Admin'", (id_usuario,))
    conn.commit()
    conn.close()
    return redirect(url_for('panel_admin'))


# ============================================================
# CERRAR SESIÓN
# ============================================================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ============================================================
#  FORO ESTUDIANTIL  (esta es mi parte — ordenada según el
#  diagrama de flujo, de arriba hacia abajo)
# ============================================================

# Categorías que aparecen en la barra lateral del foro
CATEGORIAS_FORO = [
    'General', 'Cohorte 1', 'Cohorte 2', 'Cohorte 3',
    'Wellness', 'Injusticias', 'Dudas', 'Clases',
    'Horas Key', 'Platzi', 'Co-curriculares', 'Book Club', 'Clubes', 'Memes'
]


# ------------------------------------------------------------
#  PASO 1-3 — ENTRAR AL FORO Y VER EL FEED
# ------------------------------------------------------------
@app.route('/foro', methods=['GET'])
@app.route('/foro/<categoria>', methods=['GET'])
def foro(categoria='General'):
    # PASO 2 — ¿Sesión iniciada?
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if categoria not in CATEGORIAS_FORO:
        categoria = 'General'

    # PASO 3 — Cargar los mensajes de la categoría con el nombre del autor
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT M.id_mensaje, M.mensaje, M.fecha_publicacion, U.nombre, M.archivo_adjunto
        FROM Foro_Mensajes M
        JOIN Usuarios U ON M.id_usuario = U.id_usuario
        WHERE M.categoria = ?
        ORDER BY M.fecha_publicacion DESC
    """, (categoria,))
    mensajes_db = cursor.fetchall()

    mensajes = []
    for msg in mensajes_db:
        id_msg = msg[0]
        cursor.execute("""
            SELECT tipo_reaccion, COUNT(*) as cantidad
            FROM Foro_Reacciones
            WHERE id_mensaje = ?
            GROUP BY tipo_reaccion
        """, (id_msg,))
        reacciones_db = cursor.fetchall()
        reacciones = {r[0]: r[1] for r in reacciones_db}
        mensajes.append({
            'id_mensaje': id_msg,
            'mensaje': msg[1],
            'fecha': msg[2].strftime('%d/%m/%Y %H:%M'),
            'autor': msg[3],
            'archivo_adjunto': msg[4],
            'reacciones': reacciones
        })

    conn.close()
    # PASO 9 — Mostrar el feed en la plantilla
    return render_template('foro.html', mensajes=mensajes, categorias=CATEGORIAS_FORO, categoria_actual=categoria)


# ------------------------------------------------------------
#  FUNCIONES DE APOYO PARA PUBLICAR
# ------------------------------------------------------------

# Valida que la extensión del archivo esté permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ▶ PASO 7 — MODERACIÓN CON IA (Gemini): revisa texto y, si hay, la imagen
def es_mensaje_toxico(texto, file_path=None):
    load_dotenv(override=True)
    api_key = os.getenv('GEMINI_API_KEY')

    if not api_key:
        logger.warning("Falta GEMINI_API_KEY en .env, dejando pasar el mensaje...")
        return False

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        prompt = f"Eres un moderador extremadamente estricto de una escuela. Analiza el siguiente contenido. Responde ÚNICAMENTE con la palabra 'TOXICO' si contiene groserías, palabras inapropiadas, alusiones sexuales (como 'sexo', 'gay' usado como insulto, etc), violencia explícita, insultos o acoso. Si el mensaje y/o la imagen son 100% amigables y normales, responde 'SEGURO'. Mensaje a analizar: '{texto}'"

        contents = [prompt]
        if file_path:
            ext = file_path.rsplit('.', 1)[1].lower()
            if ext in {'png', 'jpg', 'jpeg', 'gif'}:
                img = PIL.Image.open(file_path)
                contents.append(img)

        response = model.generate_content(contents, safety_settings=safety_settings)
        resultado = response.text.strip().upper()
        logger.info(f"Gemini respondió: {resultado} para el mensaje: {texto} con archivo: {file_path}")

        if "TOXICO" in resultado or "TÓXICO" in resultado:
            return True
        return False

    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Error con Gemini: {error_msg}")
        if "safety" in error_msg or "blocked" in error_msg or "candidate" in error_msg or "valueerror" in error_msg:
            return True
        return False


# ------------------------------------------------------------
#  PASO 4-8 — PUBLICAR UN MENSAJE
# ------------------------------------------------------------
@app.route('/foro/publicar', methods=['POST'])
def publicar_foro():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # PASO 4 — Recibir lo que envió el usuario
    mensaje = request.form.get('mensaje', '')
    categoria = request.form.get('categoria', 'General')
    archivo = request.files.get('archivo')

    tiene_texto   = len(mensaje.strip()) > 0
    tiene_archivo = archivo and archivo.filename != ''

    # PASO 5 — No se puede publicar vacío
    if not tiene_texto and not tiene_archivo:
        flash('Debes escribir un mensaje o adjuntar un archivo.', 'danger')
        return redirect(url_for('foro', categoria=categoria))

    nombre_archivo_guardado = None
    ruta_completa = None

    # PASO 6 — Guardar el archivo de forma segura
    if tiene_archivo:
        if allowed_file(archivo.filename):
            import time
            nombre_original = secure_filename(archivo.filename)
            nombre_archivo_guardado = f"{int(time.time())}_{nombre_original}"
            ruta_completa = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo_guardado)
            archivo.save(ruta_completa)
        else:
            flash('Tipo de archivo no permitido.', 'danger')
            return redirect(url_for('foro', categoria=categoria))

    # PASO 7 — Moderar con IA. Si es tóxico, borra el archivo y bloquea
    if es_mensaje_toxico(mensaje, ruta_completa):
        if ruta_completa and os.path.exists(ruta_completa):
            os.remove(ruta_completa)
        flash('Tu mensaje viola las normas de la comunidad y ha sido bloqueado por nuestra IA de moderación.', 'danger')
        return redirect(url_for('foro', categoria=categoria))

    # PASO 8 — Solo si pasó el filtro, se inserta en la base de datos
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Foro_Mensajes (id_usuario, categoria, mensaje, archivo_adjunto)
            VALUES (?, ?, ?, ?)
        """, (session['user_id'], categoria, mensaje if tiene_texto else None, nombre_archivo_guardado))
        conn.commit()
        conn.close()
        flash('Mensaje publicado correctamente.', 'success')
    except Exception as e:
        flash(f'Error al publicar: {str(e)}', 'danger')

    return redirect(url_for('foro', categoria=categoria))


# ------------------------------------------------------------
#  ▶ FLUJO APARTE — REACCIONAR (sin recargar la página)
#    Lo llama el JavaScript con fetch y devuelve JSON.
#    Toggle de 3 caminos: misma reacción la quita, otra la cambia,
#    ninguna todavía la crea.
# ------------------------------------------------------------
@app.route('/foro/reaccionar', methods=['POST'])
def reaccionar_foro():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    data = request.get_json()
    id_mensaje = data.get('id_mensaje')
    tipo_reaccion = data.get('tipo_reaccion')

    reacciones_validas = ['Me divierte', 'Me encanta', 'Me gusta', 'Me enoja', 'Me entristece']
    if tipo_reaccion not in reacciones_validas:
        return jsonify({'success': False, 'message': 'Reacción inválida'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_reaccion, tipo_reaccion FROM Foro_Reacciones WHERE id_mensaje = ? AND id_usuario = ?", (id_mensaje, session['user_id']))
        reaccion_existente = cursor.fetchone()

        if reaccion_existente:
            if reaccion_existente[1] == tipo_reaccion:
                cursor.execute("DELETE FROM Foro_Reacciones WHERE id_reaccion = ?", (reaccion_existente[0],))
            else:
                cursor.execute("UPDATE Foro_Reacciones SET tipo_reaccion = ? WHERE id_reaccion = ?", (tipo_reaccion, reaccion_existente[0]))
        else:
            cursor.execute("INSERT INTO Foro_Reacciones (id_mensaje, id_usuario, tipo_reaccion) VALUES (?, ?, ?)", (id_mensaje, session['user_id'], tipo_reaccion))

        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
import pyodbc
from flask import Blueprint, request, redirect, url_for, session, flash

# Creamos un Blueprint para conectar este archivo con tu app.py principal
reportes_bp = Blueprint('reportes', __name__)

# Reutilizamos tu misma función de conexión
def get_db_connection():
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=ELIEZERRDR\\SQLEXPRESS;'
        'DATABASE=KeyInstituteDB;'
        'Trusted_Connection=yes;'
    )
    return pyodbc.connect(conn_str)

@reportes_bp.route('/crear_reporte', methods=['POST'])
def crear_reporte():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Capturamos los datos que vienen de tus modales
    tipo = request.form.get('tipo')
    descripcion = request.form.get('descripcion')
    prioridad = request.form.get('prioridad')
    categoria = request.form.get('categoria')
    titulo = request.form.get('titulo', 'Sin título') # Por si es incidente y no lleva título
    
    id_usuario = session['user_id']
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Reportes (id_usuario, tipo, titulo, descripcion, prioridad, categoria)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (id_usuario, tipo, titulo, descripcion, prioridad, categoria))
        conn.commit()
        conn.close()
        flash('Reporte enviado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al guardar reporte: {str(e)}', 'danger')
        
    return redirect(url_for('index'))
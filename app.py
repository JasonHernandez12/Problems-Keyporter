import pyodbc
from flask import Flask, render_template

app = Flask(__name__)

# Función para conectar a SQL Server
def get_db_connection():
    # IMPORTANTE: Cambia 'SERVER=...' por el nombre que sale en tu SSMS al conectar
    # Usualmente es localhost\SQLEXPRESS o el nombre de tu PC
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=ELIEZERRDR\SQLEXPRESS;'
        'DATABASE=KeyInstituteDB;'
        'Trusted_Connection=yes;'
    )
    return pyodbc.connect(conn_str)

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Consulta para el "Listado por prioridad" (Alta primero)
    cursor.execute("""
        SELECT titulo, prioridad, estado, fecha_creacion 
        FROM Reportes 
        ORDER BY 
            CASE prioridad 
                WHEN 'Alta' THEN 1 
                WHEN 'Media' THEN 2 
                ELSE 3 
            END
    """)
    mis_reportes = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', reportes=mis_reportes)

if __name__ == '__main__':
    app.run(debug=True)
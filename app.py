import pyodbc
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'KeyInstitute_Security_2026'

def get_db_connection():
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=GOGUILPTP\\SQLEXPRESS;'
        'DATABASE=KeyInstituteDB;'
        'Trusted_Connection=yes;'
    )
    return pyodbc.connect(conn_str)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validación del dominio institucional
        if not email.endswith('@keyinstitute.edu.sv'):
            flash('Debes usar tu correo @keyinstitute.edu.sv', 'danger')
            return redirect(url_for('login'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id_usuario, nombre, rol FROM Usuarios WHERE email = ? AND password = ?", (email, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                session['user_id'] = user[0]
                session['username'] = user[1] 
                session['rol'] = user[2]
                return redirect(url_for('index'))
            else:
                flash('Correo o contraseña incorrectos.', 'danger')
        except Exception as e:
            flash(f'Error de conexión: {str(e)}', 'danger')
            
    return render_template('login.html')

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Pasamos el nombre a la plantilla
    return render_template('index.html', nombre_usuario=session['username'])

# Logout
@app.route('/logout')
def logout():
    session.clear() # Borra todo (id, username, rol)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
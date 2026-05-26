import pyodbc
import os

conn_str = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=ELIEZERRDR\\SQLEXPRESS;'
    'DATABASE=KeyInstituteDB;'
    'Trusted_Connection=yes;'
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Agregar la columna si no existe
    cursor.execute("""
    IF NOT EXISTS(SELECT * FROM sys.columns WHERE Name = N'archivo_adjunto' AND Object_ID = Object_ID(N'Foro_Mensajes'))
    BEGIN
        ALTER TABLE Foro_Mensajes ADD archivo_adjunto NVARCHAR(MAX) NULL
    END
    """)
    conn.commit()
    print("Columna archivo_adjunto añadida exitosamente.")
except Exception as e:
    print(f"Error en base de datos: {e}")
finally:
    if 'conn' in locals():
        conn.close()

# Crear directorio
upload_path = os.path.join(os.getcwd(), 'static', 'uploads', 'foro')
os.makedirs(upload_path, exist_ok=True)
print(f"Directorio creado: {upload_path}")

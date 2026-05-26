import pyodbc

conn_str = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=ELIEZERRDR\\SQLEXPRESS;'
    'DATABASE=KeyInstituteDB;'
    'Trusted_Connection=yes;'
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Eliminar primero las reacciones por la restricción de clave foránea
    cursor.execute("DELETE FROM Foro_Reacciones")
    
    # Luego eliminar los mensajes
    cursor.execute("DELETE FROM Foro_Mensajes")

    # Reiniciar el contador de identidades para que los ID vuelvan a empezar en 1 (opcional pero recomendado)
    cursor.execute("DBCC CHECKIDENT ('Foro_Mensajes', RESEED, 0)")
    cursor.execute("DBCC CHECKIDENT ('Foro_Reacciones', RESEED, 0)")

    conn.commit()
    print("Todos los mensajes y reacciones del foro han sido eliminados.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()

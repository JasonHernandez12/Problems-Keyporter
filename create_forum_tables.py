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

    # Tabla Foro_Mensajes
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Foro_Mensajes' and xtype='U')
    CREATE TABLE Foro_Mensajes (
        id_mensaje INT IDENTITY(1,1) PRIMARY KEY,
        id_usuario INT NOT NULL,
        categoria NVARCHAR(100) NOT NULL,
        mensaje NVARCHAR(MAX) NOT NULL,
        fecha_publicacion DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario)
    )
    """)

    # Tabla Foro_Reacciones
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Foro_Reacciones' and xtype='U')
    CREATE TABLE Foro_Reacciones (
        id_reaccion INT IDENTITY(1,1) PRIMARY KEY,
        id_mensaje INT NOT NULL,
        id_usuario INT NOT NULL,
        tipo_reaccion NVARCHAR(50) NOT NULL,
        FOREIGN KEY (id_mensaje) REFERENCES Foro_Mensajes(id_mensaje),
        FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario),
        CONSTRAINT UQ_Reaccion UNIQUE(id_mensaje, id_usuario)
    )
    """)

    conn.commit()
    print("Tablas creadas exitosamente.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()

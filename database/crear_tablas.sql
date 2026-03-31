-- 1. Crear la base
CREATE DATABASE KeyInstituteDB;
GO

USE KeyInstituteDB;
GO

-- 2. Tabla de Usuarios (para el registro que pide la rúbrica)
CREATE TABLE Usuarios (
    id_usuario INT PRIMARY KEY IDENTITY(1,1),
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

-- 3. Tabla de Reportes (con lo que pide la imagen: Prioridad)
CREATE TABLE Reportes (
    id_reporte INT PRIMARY KEY IDENTITY(1,1),
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT NOT NULL,
    prioridad VARCHAR(20) CHECK (prioridad IN ('Baja', 'Media', 'Alta')),
    estado VARCHAR(20) DEFAULT 'Pendiente', -- Pendiente, En Proceso, Resuelto
    fecha_creacion DATETIME DEFAULT GETDATE(),
    id_usuario INT FOREIGN KEY REFERENCES Usuarios(id_usuario)
);
GO

-- 4. Un par de datos de prueba para ver si el Listado funciona
INSERT INTO Reportes (titulo, descripcion, prioridad, estado)
VALUES ('Falla en Wifi', 'No hay señal en el lab 2', 'Alta', 'Pendiente'),
       ('Silla rota', 'Aula 4 tiene una silla dañada', 'Baja', 'Resuelto');
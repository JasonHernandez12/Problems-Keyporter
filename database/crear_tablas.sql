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


-- Nuevo código sql a copiar 

USE KeyInstituteDB;
GO

-- 1. Eliminar tablas anteriores para empezar de cero
-- Eliminamos primero Reportes por si existía (por la llave foránea)
IF OBJECT_ID('Reportes', 'U') IS NOT NULL DROP TABLE Reportes;
IF OBJECT_ID('Usuarios', 'U') IS NOT NULL DROP TABLE Usuarios;
GO

-- 2. Crear únicamente la tabla necesaria para el Login
CREATE TABLE Usuarios (
    id_usuario INT PRIMARY KEY IDENTITY(1,1),
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,       -- Correo institucional
    password VARCHAR(255) NOT NULL,           -- Contraseña (texto plano por ahora)
    rol VARCHAR(20) NOT NULL DEFAULT 'Alumno' -- Admin, Director, Maestro, Alumno
);
GO

-- 3. Insertar el usuario para probar el sistema
INSERT INTO Usuarios (nombre, email, password, rol)
VALUES ('David Munguía', 'david.munguia@keyinstitute.edu.sv', '12345', 'Alumno'),
('Fernando Barrera', 'fernando.barrera@keyinstitute.edu.sv', '12345', 'Alumno'),
('Jose Serrano', 'jose.serrano@keyinstitute.edu.sv', '12345', 'Alumno'),
('Diego de León', 'diego.deleon@keyinstitute.edu.sv', '12345', 'Alumno'),
('Jason Hernández', 'jason.hernandez@keyinstitute.edu.sv', '12345', 'Alumno');
GO

--Nuevo código sql a copiar
-- Script para configurar el usuario Administrador del sistema Key Institute
IF EXISTS (SELECT 1 FROM Usuarios WHERE email = 'erick.varela@keyinstitute.edu.sv')
BEGIN
    -- Si el usuario ya existe, elevamos sus privilegios a Admin
    UPDATE Usuarios 
    SET rol = 'Admin' 
    WHERE email = 'erick.varela@keyinstitute.edu.sv';
END
ELSE
BEGIN
    -- Si el usuario no existe, lo creamos con las credenciales por defecto
    INSERT INTO Usuarios (nombre, email, password, rol) 
    VALUES ('Erick Varela', 'erick.varela@keyinstitute.edu.sv', 'admin123', 'Admin');
END


CREATE TABLE Respuestas (
    id_respuesta INT IDENTITY(1,1) PRIMARY KEY,
    id_reporte INT NOT NULL,
    id_docente INT NOT NULL,
    mensaje_respuesta VARCHAR(MAX) NOT NULL,
    fecha_respuesta DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_Respuestas_Reportes
    FOREIGN KEY (id_reporte) REFERENCES Reportes(id_reporte),

    CONSTRAINT FK_Respuestas_Docente
    FOREIGN KEY (id_docente) REFERENCES Usuarios(id_usuario)
);
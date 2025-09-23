import pymysql

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',  
        db='final_seguridad',
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id_usuario INT(11) NOT NULL AUTO_INCREMENT,
                nombre VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                id_rol INT(11) NOT NULL,
                fecha_registro TIMESTAMP NOT NULL DEFAULT current_timestamp(),
                PRIMARY KEY (id_usuario),
                KEY id_rol (id_rol)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                id_rol INT(11) NOT NULL AUTO_INCREMENT,
                nombre_rol VARCHAR(50) NOT NULL UNIQUE,
                PRIMARY KEY (id_rol)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cuentas_bancarias (
                id_cuenta INT(11) NOT NULL AUTO_INCREMENT,
                id_usuario INT(11) NOT NULL,
                numero_cuenta VARCHAR(20) NOT NULL UNIQUE,
                saldo DECIMAL(15,2) NOT NULL DEFAULT 0.00,
                fecha_creacion TIMESTAMP NOT NULL DEFAULT current_timestamp(),
                PRIMARY KEY (id_cuenta),
                KEY id_usuario (id_usuario),
                FOREIGN KEY (id_usuario) REFERENCES usuarios (id_usuario) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS permisos (
                id_permiso INT(11) NOT NULL AUTO_INCREMENT,
                nombre_permiso VARCHAR(100) NOT NULL UNIQUE,
                descripcion TEXT DEFAULT NULL,
                PRIMARY KEY (id_permiso)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tarjetas_credito (
                id_tarjeta INT AUTO_INCREMENT PRIMARY KEY,
                numero_tarjeta VARCHAR(19) NOT NULL,
                fecha_expiracion VARCHAR(5) NOT NULL,
                tipo_tarjeta ENUM('VISA', 'Mastercard', 'American Express', 'Discover') NOT NULL,
                limite_credito DECIMAL(10,2) NOT NULL,
                saldo_disponible DECIMAL(10,2) NOT NULL,
                id_usuario INT NOT NULL,
                numero_cuenta VARCHAR(20),
                saldo_cuenta DECIMAL(10,2),
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
                FOREIGN KEY (numero_cuenta) REFERENCES cuentas_bancarias(numero_cuenta)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tarjetas_debito (
                id_tarjeta INT AUTO_INCREMENT PRIMARY KEY,
                numero_tarjeta VARCHAR(19) NOT NULL,
                fecha_expiracion VARCHAR(5) NOT NULL,
                tipo_tarjeta ENUM('VISA', 'Mastercard', 'American Express', 'Discover') NOT NULL,
                saldo_disponible DECIMAL(10,2) NOT NULL,
                numero_cuenta VARCHAR(20) NOT NULL,
                saldo_cuenta DECIMAL(10,2),
                id_usuario INT NOT NULL,
                FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
                FOREIGN KEY (numero_cuenta) REFERENCES cuentas_bancarias(numero_cuenta)
            )
        """)


        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transferencias (
                id_transferencia INT(11) NOT NULL AUTO_INCREMENT,
                id_cuenta_origen INT(11) NOT NULL,
                id_cuenta_destino INT(11) NOT NULL,
                monto DECIMAL(15,2) NOT NULL,
                fecha_transferencia TIMESTAMP NOT NULL DEFAULT current_timestamp(),
                token_validacion VARCHAR(255) NOT NULL,
                saldo_restante DECIMAL NOT NULL,
                PRIMARY KEY (id_transferencia),
                KEY id_cuenta_origen (id_cuenta_origen),
                KEY id_cuenta_destino (id_cuenta_destino),
                FOREIGN KEY (id_cuenta_origen) REFERENCES cuentas_bancarias (id_cuenta),
                FOREIGN KEY (id_cuenta_destino) REFERENCES cuentas_bancarias (id_cuenta)
            )
        """)
        connection.commit()
    connection.close()
init_db()

print("Base de datos inicializada correctamente.")

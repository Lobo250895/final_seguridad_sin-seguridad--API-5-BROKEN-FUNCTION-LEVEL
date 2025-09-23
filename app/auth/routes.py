from flask import Blueprint, request, jsonify, render_template, redirect, url_for,make_response
from app.utils.db import get_connection
from app.auth.utils import generate_jwt, hash_password, check_password
from flask import session, redirect, url_for, make_response
from flask import flash, redirect, url_for

bp_auth = Blueprint('auth', __name__)


@bp_auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        if data['password'] != data['confirm_password']:
            flash('Las contraseñas no coinciden', 'error')  
            return redirect(url_for('auth.register')) 

        hashed_password = hash_password(data['password'])
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_rol FROM roles WHERE nombre_rol = 'cliente'")
            result = cursor.fetchone()
            if result:
                id_rol = result['id_rol']
            else:
                flash('Rol no encontrado', 'error')  
                return redirect(url_for('auth.register'))

            cursor.execute("""
                INSERT INTO usuarios (nombre, email, password, id_rol)
                VALUES (%s, %s, %s, %s)
            """, (data['nombre'], data['email'], hashed_password, id_rol))
            connection.commit()

        flash('Registro exitoso por favor inicia Sesion', 'success')  
        return redirect(url_for('auth.login'))  

    return render_template('register.html')


@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form

        if not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Todos los campos son obligatorios'}), 400
        FIELD_LIMITS = {
            'email': 254,
            'password': 20,
        }

        for field, limit in FIELD_LIMITS.items():
            if len(data.get(field, '').strip()) > limit:
                return jsonify({'message': f'El campo {field} no puede tener más de {limit} caracteres'}), 400
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (data['email'],))
            user = cursor.fetchone()
        
        if user and check_password(user['password'], data['password']):
            token = generate_jwt(user['id_usuario'], user['id_rol'])

            response = make_response()
            if user['id_rol'] == 1:  # Admin
                response = redirect(url_for('administrador.dashboard'))
            elif user['id_rol'] == 2:  # Empleado
                response = redirect(url_for('empleado.dashboard'))
            elif user['id_rol'] == 3:  # Cliente
                response = redirect(url_for('cliente.dashboard'))
            else:
                return jsonify({'message': 'Rol no encontrado'}), 400

            response.set_cookie(
                'authToken',  
                token,  
                httponly=True,  # No accesible desde JavaScript
                secure=False,  #True Solo se transmite por HTTPS
                samesite='Lax' # Protege contra CSRF 'Strict'
            )
            return response

        return jsonify({'message': 'Invalid credentials'}), 401

    return render_template('login.html')


@bp_auth.route('/logout', methods=['GET'])
def logout():
    session.clear()
    response = make_response(redirect(url_for('auth.login')))
    response.set_cookie(
        'authToken', '',  # Valor vacío para eliminar el token
        expires=0,        # Expira inmediatamente
        httponly=True,    # Solo accesible desde el servidor
        secure=True,      # Asegúrate de que HTTPS esté activado en producción
        samesite='Strict' # Evita envío en solicitudes de terceros
    )
    return response
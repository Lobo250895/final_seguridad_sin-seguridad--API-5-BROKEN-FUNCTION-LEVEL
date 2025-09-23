from flask import Blueprint, render_template,jsonify,request,flash,redirect,url_for
from app.utils.auth_middleware import jwt_required
from app.utils.db import get_connection
import logging
import validators

bp_admin = Blueprint('administrador', __name__,template_folder='templates')

@bp_admin.route('/dashboard')
#@jwt_required(roles=[1], permissions=['ver_dashboard_admin'])
def dashboard(user=None):
    if not user:
        user = {'user_id': 1} 
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.email, cb.numero_cuenta, cb.saldo
            FROM usuarios u
            LEFT JOIN cuentas_bancarias cb ON u.id_usuario = cb.id_usuario
            WHERE u.id_rol = 3
        """)
        clientes = cursor.fetchall()

        cursor.execute("""
            SELECT COUNT(*) AS total_clientes
            FROM usuarios
            WHERE id_rol = 3
        """)
        total_clientes = cursor.fetchone()['total_clientes']

        cursor.execute("""
            SELECT COUNT(*) AS cantidad_tarjetas
            FROM tarjetas_debito t
            JOIN usuarios u ON t.id_usuario = u.id_usuario
            WHERE u.id_rol = 3
        """)
        cantidad_tarjetas = cursor.fetchone()["cantidad_tarjetas"]

        cursor.execute("""
            SELECT COALESCE(SUM(cb.saldo), 0) AS saldo_total
            FROM cuentas_bancarias cb
            JOIN usuarios u ON cb.id_usuario = u.id_usuario
            WHERE u.id_rol = 3
        """)
        saldo_total = cursor.fetchone()["saldo_total"]

        
        if not clientes:
            logging.warning(f"No se encontraron clientes. Usuario: {user['user_id']} desde IP: {request.remote_addr}")
            return jsonify({"message": "No hay clientes registrados"}), 404

        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.email
            FROM usuarios u
            WHERE u.id_usuario = %s
        """, (user['user_id'],)) 
        admin_info = cursor.fetchone()

        if not admin_info:
            logging.error(f"No se encontró el administrador con ID {user['user_id']}")
            return jsonify({"message": "Administrador no encontrado"}), 404
    return render_template('administrador/dashboard.html', clientes=clientes, admin_nombre=admin_info['nombre'], total_clientes=total_clientes,cantidad_tarjetas=cantidad_tarjetas,saldo_total=saldo_total )


@bp_admin.route('/clientes')
#@jwt_required(roles=[1], permissions=['ver_clientes'])
def clientes(user=None):
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.email, cb.numero_cuenta, cb.saldo
            FROM usuarios u
            LEFT JOIN cuentas_bancarias cb ON u.id_usuario = cb.id_usuario
            WHERE u.id_rol = 3
        """)
        clientes = cursor.fetchall()

        if not clientes:
            logging.warning(f"No se encontraron clientes. Usuario: {user['user_id']} desde IP: {request.remote_addr}")
            return jsonify({"message": "No hay clientes registrados"}), 404
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.email
            FROM usuarios u
            WHERE u.id_usuario = %s
        """, (user['user_id'],))
        admin_info = cursor.fetchone()

        if not admin_info:
            logging.error(f"No se encontró el administrador con ID {user['user_id']}")
            return jsonify({"message": "Administrador no encontrado"}), 404
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.email, r.nombre_rol
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id_rol
            WHERE u.id_rol = 3
        """)
        roles_clientes = cursor.fetchall()
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.email, p.nombre_permiso
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id_rol
            JOIN roles_permisos rp ON r.id_rol = rp.id_rol
            JOIN permisos p ON rp.id_permiso = p.id_permiso
            WHERE u.id_rol = 3
        """)
        permisos_clientes = cursor.fetchall()

    return render_template(
        'administrador/clientes.html',clientes=clientes,admin_nombre=admin_info['nombre'],roles_clientes=roles_clientes,permisos_clientes=permisos_clientes)


@bp_admin.route('/clientes/<int:id_usuario>/editar', methods=['GET', 'POST'])
#@jwt_required(roles=[1], permissions=['ver_clientes'])
def editar_cliente(id_usuario, user=None):
    connection = get_connection()
    with connection.cursor() as cursor:
        if request.method == 'GET':
            cursor.execute("""SELECT id_usuario, nombre, email FROM usuarios WHERE id_usuario = %s""", (id_usuario,))
            cliente = cursor.fetchone()

            if not cliente:
                flash('Cliente no encontrado.', 'error')  
                return redirect(url_for('administrador.clientes')) 

            return render_template('administrador/editar_cliente.html', cliente=cliente)

        elif request.method == 'POST':
            nombre = request.form['nombre'].strip()
            email = request.form['email'].strip()

            if not nombre or len(nombre) > 50:
                flash('El nombre es obligatorio y debe tener como máximo 50 caracteres.', 'error')
                return redirect(url_for('administrador.editar_cliente', id_usuario=id_usuario))

            if not email or len(email) > 100 or not validators.email(email):
                flash('El correo electrónico es inválido.', 'error')
                return redirect(url_for('administrador.editar_cliente', id_usuario=id_usuario))
            cursor.execute("""
                UPDATE usuarios
                SET nombre = %s, email = %s
                WHERE id_usuario = %s
            """, (nombre, email, id_usuario))
            connection.commit()

            flash('Cliente actualizado correctamente.', 'success')
            return redirect(url_for('administrador.clientes'))  
        
@bp_admin.route('/clientes/<int:id_usuario>/eliminar', methods=['POST'])
#@jwt_required(roles=[1], permissions=['eliminar_clientes'])
def eliminar_cliente(id_usuario, user=None):
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("""SELECT id_usuario FROM usuarios WHERE id_usuario = %s""", (id_usuario,))
        cliente = cursor.fetchone()

        if not cliente:
            flash('Cliente no encontrado.', 'error')  
            return redirect(url_for('administrador.clientes'))  

        cursor.execute("""DELETE FROM usuarios WHERE id_usuario = %s""", (id_usuario,))
        connection.commit()

    flash('Cliente eliminado correctamente.', 'success')
    return redirect(url_for('administrador.clientes')) 


@bp_admin.route('/clientes/<int:id_usuario>/editar_rol', methods=['POST'])
@jwt_required(roles=[1], permissions=['editar_roles'])
def editar_rol(id_usuario, user):
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("""SELECT id_usuario, nombre, id_rol FROM usuarios WHERE id_usuario = %s""", (id_usuario,))
        cliente = cursor.fetchone()

        if not cliente:
            flash('Cliente no encontrado.', 'error')
            return redirect(url_for('administrador.clientes'))
        nuevo_rol = request.form.get('rol')  
        cursor.execute("""UPDATE usuarios SET id_rol = %s WHERE id_usuario = %s""", (nuevo_rol, id_usuario))
        connection.commit()

        flash('Rol actualizado con éxito.', 'success')
        return redirect(url_for('administrador.clientes'))


@bp_admin.route('/editar_permisos/<int:id_usuario>', methods=['GET', 'POST'])
#@jwt_required(roles=[1], permissions=['editar_permisos'])
def editar_permisos(id_usuario, user=None):
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.id_permiso, p.nombre_permiso
            FROM permisos p
            JOIN roles_permisos rp ON p.id_permiso = rp.id_permiso
            JOIN usuarios u ON u.id_rol = rp.id_rol
            WHERE u.id_usuario = %s;
        """, (id_usuario,))
        permisos_usuario = cursor.fetchall()
        cursor.execute("SELECT id_permiso, nombre_permiso FROM permisos")
        todos_permisos = cursor.fetchall()
    permisos_usuario_set = set([p['id_permiso'] for p in permisos_usuario])

    return render_template(
        'administrador/editar_permisos.html',
        todos_permisos=todos_permisos,
        permisos_usuario_set=permisos_usuario_set,
        id_usuario=id_usuario  
    )


@bp_admin.route('/editar_permisos/<int:id_usuario>', methods=['POST'])
#@jwt_required(roles=[1], permissions=['editar_permisos'])
def editar_permisos_post(id_usuario, user=None):
    permisos_seleccionados = request.form.getlist('permisos')
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM roles_permisos 
            WHERE id_rol = (SELECT id_rol FROM usuarios WHERE id_usuario = %s);
        """, (id_usuario,))
        for permiso_id in permisos_seleccionados:
            cursor.execute("""
                INSERT INTO roles_permisos (id_rol, id_permiso)
                VALUES (
                    (SELECT id_rol FROM usuarios WHERE id_usuario = %s),
                    %s
                );
            """, (id_usuario, permiso_id))
        connection.commit()
    flash('Permisos actualizados correctamente', 'success')
    return redirect(url_for('administrador.editar_permisos', id_usuario=id_usuario))


@bp_admin.route('/clientes/<int:id_usuario>/editar_cuenta', methods=['GET', 'POST'])
#@jwt_required(roles=[1], permissions=['crear_cuentas'])
def editar_cuenta(id_usuario, user=None):
    connection = get_connection()
    if request.method == 'GET':
        with connection.cursor() as cursor:
            cursor.execute("""SELECT id_usuario, nombre FROM usuarios WHERE id_usuario = %s""", (id_usuario,))
            cliente = cursor.fetchone()

            if not cliente:
                flash('Cliente no encontrado.', 'error')
                return redirect(url_for('administrador.clientes'))

            cursor.execute("""SELECT * FROM cuentas_bancarias WHERE id_usuario = %s""", (id_usuario,))
            cuentas = cursor.fetchall()

        return render_template(
            'administrador/editar_cuenta.html',
            cliente=cliente,
            cuentas=cuentas
        )

    elif request.method == 'POST':
        numero_cuenta = request.form.get('numero_cuenta')
        saldo = request.form.get('saldo')

        if not numero_cuenta or not saldo:
            flash('El número de cuenta y el saldo son obligatorios.', 'error')
            return redirect(url_for('administrador.editar_cuenta', id_usuario=id_usuario))

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO cuentas_bancarias (id_usuario, numero_cuenta, saldo)
                VALUES (%s, %s, %s)
            """, (id_usuario, numero_cuenta, saldo))
            connection.commit()

        flash('Cuenta bancaria creada exitosamente.', 'success')
        return redirect(url_for('administrador.editar_cuenta', id_usuario=id_usuario))




@bp_admin.route('/empleados')
#@jwt_required(roles=[1], permissions=['ver_empleados'])
def empleados(user=None):
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.email, r.nombre_rol, u.id_rol
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id_rol
            WHERE u.id_rol = 2  -- Asumiendo que el rol de empleado tiene id_rol = 2
        """)
        empleados = cursor.fetchall()
        permisos_empleados = {}
        for empleado in empleados:
            cursor.execute("""
                SELECT p.nombre_permiso
                FROM permisos p
                JOIN roles_permisos rp ON p.id_permiso = rp.id_permiso
                WHERE rp.id_rol = %s
            """, (empleado['id_rol'],))
            permisos_empleados[empleado['id_usuario']] = [p['nombre_permiso'] for p in cursor.fetchall()]

    return render_template('administrador/empleados.html', empleados=empleados, permisos_empleados=permisos_empleados)



@bp_admin.route('/empleados/<int:id_usuario>/editar', methods=['GET', 'POST'])
#@jwt_required(roles=[1], permissions=['editar_empleado'])
def editar_empleado(id_usuario, user=None):
    connection = get_connection()
    with connection.cursor() as cursor:
        if request.method == 'GET':
            cursor.execute("SELECT id_usuario, nombre, email FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            empleado = cursor.fetchone()
            if not empleado:
                flash('Empleado no encontrado.', 'error')
                return redirect(url_for('administrador.empleados'))
            return render_template('administrador/editar_empleado.html', empleado=empleado)

        elif request.method == 'POST':
            nombre = request.form['nombre'].strip()
            email = request.form['email'].strip()
            cursor.execute("""
                UPDATE usuarios
                SET nombre = %s, email = %s
                WHERE id_usuario = %s
            """, (nombre, email, id_usuario))
            connection.commit()
            flash('Empleado actualizado correctamente.', 'success')
            return redirect(url_for('administrador.empleados'))


@bp_admin.route('/empleados/<int:id_usuario>/eliminar', methods=['POST'])
#@jwt_required(roles=[1], permissions=['eliminar_empleados'])
def eliminar_empleado(id_usuario, user=None):
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        connection.commit()
    flash('Empleado eliminado correctamente.', 'success')
    return redirect(url_for('administrador.empleados'))


@bp_admin.route('/empleados/<int:id_usuario>/editar_rol_permisos', methods=['GET', 'POST'])
#@jwt_required(roles=[1], permissions=['editar_roles_permisos'])
def editar_rol_permisos(id_usuario, user=None):
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT id_rol, nombre_rol FROM roles")
        roles = cursor.fetchall()
        cursor.execute("SELECT id_permiso, nombre_permiso FROM permisos")
        permisos = cursor.fetchall()

        cursor.execute("""
            SELECT u.id_rol
            FROM usuarios u
            WHERE u.id_usuario = %s
        """, (id_usuario,))
        rol_actual = cursor.fetchone()['id_rol']

        cursor.execute("""
            SELECT p.id_permiso
            FROM permisos p
            JOIN roles_permisos rp ON p.id_permiso = rp.id_permiso
            WHERE rp.id_rol = %s
        """, (rol_actual,))
        permisos_actuales = [p['id_permiso'] for p in cursor.fetchall()]

        if request.method == 'POST':
            nuevo_rol = request.form['rol']
            cursor.execute("""
                UPDATE usuarios
                SET id_rol = %s
                WHERE id_usuario = %s
            """, (nuevo_rol, id_usuario))
            permisos_seleccionados = request.form.getlist('permisos')

            cursor.execute("""
                DELETE FROM roles_permisos WHERE id_rol = %s
            """, (rol_actual,))


            for permiso_id in permisos_seleccionados:
                cursor.execute("""
                    INSERT INTO roles_permisos (id_rol, id_permiso)
                    VALUES (%s, %s)
                """, (nuevo_rol, permiso_id))

            connection.commit()

            flash('Rol y permisos actualizados correctamente.', 'success')
            return redirect(url_for('administrador.empleados'))

    return render_template('administrador/editar_rol_permisos.html', roles=roles, permisos=permisos,
                           rol_actual=rol_actual, permisos_actuales=permisos_actuales, id_usuario=id_usuario)



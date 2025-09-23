from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify
from app.utils.auth_middleware import jwt_required
from app.utils.db import get_connection
import secrets
from decimal import Decimal
from flask import session
import logging
import validators


bp_cliente = Blueprint(
    'cliente', __name__, 
    template_folder='templates' 
)


@bp_cliente.route('/dashboard')
#@jwt_required(roles=[3], permissions=['ver_dashboard_cliente'])
def dashboard(user=None):
    if not user:
        user = {'user_id': 3} 
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT cb.*, u.nombre AS nombre_dueno
            FROM cuentas_bancarias cb
            LEFT JOIN usuarios u ON cb.id_usuario = u.id_usuario
            WHERE cb.id_usuario = %s
        """, (user['user_id'],))
        cuenta = cursor.fetchone()

        if not cuenta:
            logging.warning(f"Intento de acceso a dashboard sin cuenta válida. Usuario: {user['user_id']} desde IP: {request.remote_addr}")
            return jsonify({"message": "Cuenta no encontrada o acceso denegado"}), 404

        saldo = cuenta['saldo'] if cuenta['saldo'] is not None else 0
        print(f"Saldo recuperado: {saldo}")

        cursor.execute("SELECT * FROM tarjetas_debito WHERE id_usuario = %s", (user['user_id'],))
        tarjeta_debito = cursor.fetchall()

        cursor.execute("SELECT * FROM tarjetas_credito WHERE id_usuario = %s", (user['user_id'],))
        tarjeta_credito = cursor.fetchall()

        cursor.execute("""
            SELECT 
                t.fecha_transferencia, t.monto, t.saldo_restante,
                t.id_cuenta_origen, t.id_cuenta_destino, 
                u_origen.nombre AS nombre_origen, u_destino.nombre AS nombre_destino,
                cb_origen.numero_cuenta AS numero_cuenta_origen,
                cb_destino.numero_cuenta AS numero_cuenta_destino
            FROM transferencias t
            LEFT JOIN cuentas_bancarias cb_origen ON t.id_cuenta_origen = cb_origen.id_cuenta
            LEFT JOIN usuarios u_origen ON cb_origen.id_usuario = u_origen.id_usuario
            LEFT JOIN cuentas_bancarias cb_destino ON t.id_cuenta_destino = cb_destino.id_cuenta
            LEFT JOIN usuarios u_destino ON cb_destino.id_usuario = u_destino.id_usuario
            WHERE t.id_cuenta_origen = %s OR t.id_cuenta_destino = %s
            ORDER BY t.fecha_transferencia DESC
            LIMIT 5
        """, (user['user_id'], user['user_id']))
        movimientos = cursor.fetchall()

    for movimiento in movimientos:
        if movimiento['id_cuenta_origen'] == user['user_id']:
            movimiento['mostrar_saldo_restante'] = True
            movimiento['mostrar_monto'] = False
        elif movimiento['id_cuenta_destino'] == user['user_id']:
            movimiento['mostrar_saldo_restante'] = False
            movimiento['mostrar_monto'] = True

    return render_template('cliente/dashboard.html', cuenta=cuenta, saldo=cuenta['saldo'], tarjeta_debito=tarjeta_debito, tarjeta_credito=tarjeta_credito, movimientos=movimientos)



@bp_cliente.route('/datos_personales', methods=['GET', 'POST'])
#@jwt_required(roles=[3] , permissions=['editar_perfil']) 
def datos_personales(user):
    connection = get_connection()
    
    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        email = request.form['email'].strip()

        if not nombre or len(nombre) > 50:
            flash('El nombre es obligatorio y debe tener como máximo 50 caracteres.', 'error')
            return redirect(url_for('cliente.datos_personales'))

        if not email or len(email) > 100 or not validators.email(email):
            flash('El correo electrónico es inválido.', 'error')
            return redirect(url_for('cliente.datos_personales'))

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE usuarios 
                SET nombre = %s, email = %s
                WHERE id_usuario = %s
            """, (nombre, email, user['user_id']))
            connection.commit()

        flash('Datos personales actualizados correctamente.', 'success')
        return redirect(url_for('cliente.datos_personales'))
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                u.nombre AS usuario_nombre, 
                u.email AS usuario_email, 
                r.nombre_rol AS rol_nombre, 
                cb.numero_cuenta, 
                cb.saldo 
            FROM usuarios u
            INNER JOIN roles r ON u.id_rol = r.id_rol
            LEFT JOIN cuentas_bancarias cb ON u.id_usuario = cb.id_usuario
            WHERE u.id_usuario = %s
        """, (user['user_id'],))
        datos = cursor.fetchone()
    if not datos:
        return render_template('cliente/error.html', message='Usuario no encontrado'), 404
    return render_template('cliente/datos_personales.html', datos=datos)


def generar_token_transferencia():
    return secrets.token_hex(16)  


@bp_cliente.route('/transferencias', methods=['GET', 'POST'])
#@jwt_required(roles=[3] , permissions=['realizar_transferencias'])  
def transferencias(user):
    connection = get_connection()
    token = None

    if request.method == 'GET':
        if 'generate_token' in request.args:
            token = generar_token_transferencia()
            session['transfer_token'] = token
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id_cuenta, numero_cuenta, saldo FROM cuentas_bancarias WHERE id_usuario = %s",
                (user['user_id'],)
            )
            cuentas_origen = cursor.fetchall()
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT cb.id_cuenta AS id_cuenta_destino, cb.numero_cuenta
                FROM transferencias t
                INNER JOIN cuentas_bancarias cb ON t.id_cuenta_destino = cb.id_cuenta
                WHERE t.id_cuenta_origen IN (
                    SELECT id_cuenta
                    FROM cuentas_bancarias
                    WHERE id_usuario = %s
                )
            """, (user['user_id'],))
            cuentas_destino = cursor.fetchall()

        return render_template(
            'cliente/transferencias.html',
            token=token,
            cuentas_origen=cuentas_origen,
            cuentas_destino=cuentas_destino,
            mis_cuentas=cuentas_origen  
        )
    elif request.method == 'POST':
        cuenta_origen_id = request.form['cuenta_origen']
        tipo_destino = request.form['tipo_destino']
        cantidad = Decimal(request.form['cantidad'])
        token_recibido = request.form['token']

        if token_recibido != session.get('transfer_token'):
            #logging.warning(f"Token inválido. Usuario: {user['user_id']} desde IP: {request.remote_addr}")
            #flash('Token de validación incorrecto', 'error')
            return redirect(url_for('cliente.transferencias'))

        if tipo_destino == 'agendada':
            cuenta_destino_id = request.form['cuenta_agendada']
        elif tipo_destino == 'mis_cuentas':
            cuenta_destino_id = request.form['mis_cuentas']
        elif tipo_destino == 'nueva':
            cuenta_destino = request.form['nueva_cuenta']
            with connection.cursor() as cursor:
                cursor.execute("SELECT id_cuenta FROM cuentas_bancarias WHERE numero_cuenta = %s", (cuenta_destino,))
                cuenta_destino_row = cursor.fetchone()
                if not cuenta_destino_row:
                    flash('Cuenta destino no válida', 'error')
                    return redirect(url_for('cliente.transferencias'))
                cuenta_destino_id = cuenta_destino_row['id_cuenta']
        elif tipo_destino == 'otro_banco':
            cuenta_destino = request.form['otro_banco_cuenta']
            cuenta_destino_id = None  
        else:
            flash('Tipo de destino no válido', 'error')
            return redirect(url_for('cliente.transferencias'))
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT saldo FROM cuentas_bancarias WHERE id_cuenta = %s AND id_usuario = %s",
                (cuenta_origen_id, user['user_id'])
            )
            cuenta_origen = cursor.fetchone()
            if not cuenta_origen or cuenta_origen['saldo'] < cantidad:
                flash('Saldo insuficiente', 'error')
                return redirect(url_for('cliente.transferencias'))
        with connection.cursor() as cursor:
            cursor.execute("UPDATE cuentas_bancarias SET saldo = saldo - %s WHERE id_cuenta = %s", (cantidad, cuenta_origen_id))
            if cuenta_destino_id:
                cursor.execute("UPDATE cuentas_bancarias SET saldo = saldo + %s WHERE id_cuenta = %s", (cantidad, cuenta_destino_id))
            cursor.execute("""
                INSERT INTO transferencias 
                (id_cuenta_origen, id_cuenta_destino, monto, fecha_transferencia, token_validacion, saldo_restante) 
                VALUES (%s, %s, %s, NOW(), %s, %s)
            """, (cuenta_origen_id, cuenta_destino_id, cantidad, session.get('transfer_token'), cuenta_origen['saldo'] - cantidad))
            connection.commit()
        session.pop('transfer_token', None)
        flash('Transferencia realizada correctamente', 'success')
        return redirect(url_for('cliente.transferencias'))
    











from flask import Blueprint, render_template,jsonify,request
from app.utils.auth_middleware import jwt_required
from app.utils.db import get_connection
import logging

bp_empleado = Blueprint('empleado', __name__,
                        template_folder='templates')

@bp_empleado.route('/dashboard')
@jwt_required(roles=[2], permissions=['ver_dashboard_empleado'])
def dashboard(user):
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
    return render_template('empleado/dashboard.html', clientes=clientes)

@bp_empleado.route('/clientes')
@jwt_required(roles=[2], permissions=['ver_clientes'])
def clientes(user):
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT u.id_usuario, u.nombre, u.email, cb.numero_cuenta, cb.saldo,
                   tc.numero_tarjeta, tc.tipo_tarjeta, tc.limite_credito, tc.saldo_disponible
            FROM usuarios u
            LEFT JOIN cuentas_bancarias cb ON u.id_usuario = cb.id_usuario
            LEFT JOIN tarjetas_credito tc ON u.id_usuario = tc.id_usuario
            WHERE u.id_rol = 3
        """)
        clientes = cursor.fetchall()
        if not clientes:
            logging.warning(f"No se encontraron clientes. Usuario: {user['user_id']} desde IP: {request.remote_addr}")
            return jsonify({"message": "No hay clientes registrados"}), 404

    return render_template('empleado/clientes.html', clientes=clientes)




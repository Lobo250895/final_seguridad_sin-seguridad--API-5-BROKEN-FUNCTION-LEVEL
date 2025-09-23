from functools import wraps
from flask import request, jsonify
from app.auth.utils import decode_jwt
import logging
from app.utils.db import get_connection

def jwt_required(roles=None, permissions=None):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.cookies.get('authToken')
            if not token:
                logging.warning(f"Intento de acceso sin token desde IP: {request.remote_addr}")
                return jsonify({'message': 'No autorizado: falta token'}), 401
            try:
                user_data = decode_jwt(token)
            except Exception:
                logging.warning(f"Token inválido desde IP: {request.remote_addr}")
                return jsonify({'message': 'No autorizado: token inválido'}), 401

            if roles and user_data.get('role') not in roles:
                logging.warning(f"Intento de acceso no autorizado. Usuario: {user_data.get('user_id')} Rol: {user_data.get('role')} desde IP: {request.remote_addr}")
                return jsonify({'message': 'Prohibido: permisos insuficientes'}), 403
            
            if permissions:
                connection = get_connection()
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT p.nombre_permiso
                        FROM permisos p
                        JOIN roles_permisos rp ON p.id_permiso = rp.id_permiso
                        WHERE rp.id_rol = %s AND p.nombre_permiso IN %s
                    """, (user_data['role'], tuple(permissions)))
                    granted_permissions = cursor.fetchall()
                    granted_permissions = {perm['nombre_permiso'] for perm in granted_permissions}
                    if not all(perm in granted_permissions for perm in permissions):
                        logging.warning(f"Usuario: {user_data['user_id']} no tiene permisos suficientes para acceder a la ruta desde IP: {request.remote_addr}")
                        return jsonify({'message': 'Prohibido: permisos insuficientes'}), 403
            
            kwargs['user'] = user_data
            return f(*args, **kwargs)
        return decorated_function
    return wrapper




from flask import Flask
from app.utils.db import init_db
from app.auth.routes import bp_auth
from app.cliente.routes import bp_cliente
from app.empleado.routes import bp_empleado
from app.administrador.routes import bp_admin

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    app.register_blueprint(bp_auth, url_prefix='/auth')
    app.register_blueprint(bp_cliente, url_prefix='/cliente')
    app.register_blueprint(bp_empleado, url_prefix='/empleado')
    app.register_blueprint(bp_admin, url_prefix='/admin')
    init_db()

    return app

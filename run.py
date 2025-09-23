from flask import Flask, render_template
from app.auth.routes import bp_auth  # Importar el blueprint de autenticación
from app.utils.db import init_db  # Función para inicializar la base de datos
#import logging
from app.administrador.routes import bp_admin
from app.empleado.routes import bp_empleado
from app.cliente.routes import bp_cliente

#logging.basicConfig(
#    filename='app.log',  
#    level=logging.DEBUG,  
#    format='%(asctime)s - %(levelname)s - %(message)s'  
#)

app = Flask(__name__, static_folder='app/static', template_folder='app/templates')

app.config['SECRET_KEY'] = 'your_secret_key' 

try:
    init_db()
    app.logger.info("Base de datos inicializada correctamente.")
except Exception as e:
    app.logger.critical(f"Error al inicializar la base de datos: {e}")
    raise

# Registro de blueprints
app.register_blueprint(bp_auth, url_prefix='/auth')  
app.register_blueprint(bp_admin, url_prefix='/administrador')
app.register_blueprint(bp_empleado, url_prefix='/empleado')
app.register_blueprint(bp_cliente, url_prefix='/cliente')

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)  

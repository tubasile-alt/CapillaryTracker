import os
import logging
import traceback
from flask import Flask, render_template

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting Flask application...")

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    logger.info("Accessing index route")
    return render_template('base.html')

@app.route('/dashboard')
def dashboard():
    logger.info("Accessing dashboard route")
    try:
        # Create a simple dashboard data structure
        dashboard_data = {
            'labels': ['01/2025', '02/2025'],
            'datasets': [
                {
                    'label': 'Exemplo',
                    'data': [0, 0]
                }
            ],
            'has_follicle_data': False
        }

        return render_template('dashboard.html', data=dashboard_data)

    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}\n{traceback.format_exc()}")
        return render_template('dashboard.html', data={}, 
                            error="Erro ao carregar dashboard")

if __name__ == '__main__':
    try:
        port = 8080
        logger.info(f"Starting Flask server on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {str(e)}\n{traceback.format_exc()}")
        raise
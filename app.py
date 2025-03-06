import os
import logging
from flask import Flask
from flask_cors import CORS

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = os.urandom(24)

@app.route('/health')
def health():
    """Rota simples para verificação de saúde do servidor"""
    return "OK"

@app.route('/')
def index():
    """Rota principal - resposta simplificada para teste"""
    logger.info("Accessing index route")
    return "ICB Transplante Capilar - Sistema Online"

if __name__ == "__main__":
    try:
        logger.info("Starting Flask server on port 5000...")
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except Exception as e:
        logger.exception("Server encountered an error during startup:")
        raise
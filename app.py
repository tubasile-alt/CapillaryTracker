import os
import logging
from flask import Flask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app first
logger.info("Creating Flask application instance")
app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return "Application is running!", 200

@app.route('/health')
def health():
    """Health check endpoint"""
    logger.info("Health check endpoint accessed")
    return "OK", 200

@app.route('/ping')
def ping():
    """Simple ping endpoint for testing"""
    logger.info("Ping endpoint accessed")
    return "pong", 200

if __name__ == '__main__':
    try:
        port = 5000
        host = '0.0.0.0'

        logger.info("========================")
        logger.info("Starting Flask Server")
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info("========================")

        app.run(host=host, port=port)
    except Exception as e:
        logger.error("Failed to start server:")
        logger.error(str(e))
        raise
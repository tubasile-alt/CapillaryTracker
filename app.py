import os
import logging
from flask import Flask
from flask_cors import CORS

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Secret key for sessions and CSRF protection
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

@app.route('/health')
def health():
    """Health check endpoint for deployment monitoring"""
    return {"status": "healthy", "service": "ICB Transplante Capilar API"}

@app.route('/')
def index():
    """Main route for the application"""
    logger.info("Access to main route")
    return {
        "message": "ICB Transplante Capilar API",
        "version": "1.0.0",
        "status": "online"
    }

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))

    try:
        logger.info(f"Starting ICB Transplante Capilar server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.exception("Failed to start server:")
        raise
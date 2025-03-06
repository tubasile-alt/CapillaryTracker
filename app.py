from flask import Flask
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/")
def home():
    logger.info("Home route accessed")
    return "Flask server is running!"

if __name__ == "__main__":
    try:
        import os
        # Use PORT environment variable with fallback to 8080
        port = int(os.environ.get("PORT", 8080))
        logger.info(f"Starting Flask server on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise

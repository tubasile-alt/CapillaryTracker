
from app import app, db
from sqlalchemy import inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with app.app_context():
    inspector = inspect(db.engine)
    columns = inspector.get_columns('surgery')
    
    logger.info("Surgery table columns:")
    for column in columns:
        logger.info(f"{column['name']}: {column['type']}")

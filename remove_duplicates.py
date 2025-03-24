from app import app, db, Surgery
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_specific_duplicates():
    try:
        with app.app_context():
            # Get initial count
            initial_count = Surgery.query.count()
            logger.info(f"Initial count: {initial_count}")

            # Get duplicates for Adnan Jamil El Homoui
            duplicates = Surgery.query.filter(
                Surgery.nome.ilike('%adnan%jamil%el%homoui%')
            ).order_by(Surgery.data).all()

            if duplicates:
                # Keep first record, delete others
                first_record = duplicates[0]
                for record in duplicates[1:]:
                    db.session.delete(record)
                    logger.info(f"Deleting duplicate for {record.nome}")

                # Commit changes
                db.session.commit()

            # Get final count
            final_count = Surgery.query.count()
            logger.info(f"Final count: {final_count}")
            logger.info(f"Removed {initial_count - final_count} duplicate entries")

            return True

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    remove_specific_duplicates()
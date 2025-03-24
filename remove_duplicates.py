
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

            # Get duplicates
            duplicates = Surgery.query.filter(
                Surgery.nome.in_(['Luiz Henrique de Oliveira Pádua', 
                                'Adriano Augusto Ferreira Miqueleto'])
            ).order_by(Surgery.data).all()

            # Group by name
            by_name = {}
            for record in duplicates:
                if record.nome not in by_name:
                    by_name[record.nome] = []
                by_name[record.nome].append(record)

            # Keep first record for each name, delete others
            for name, records in by_name.items():
                if len(records) > 1:
                    # Keep first record (oldest)
                    keep = records[0]
                    # Delete others
                    for record in records[1:]:
                        db.session.delete(record)
                        logger.info(f"Deleting duplicate for {name}")

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

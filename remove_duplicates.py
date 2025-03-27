
from app import app, db, Surgery
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def remove_specific_duplicates():
    try:
        with app.app_context():
            initial_count = Surgery.query.count()
            logger.info(f"Initial count: {initial_count}")

            # Process Marco Aurélio duplicates - force delete keeping only earliest record
            marco_duplicates = Surgery.query.filter(
                Surgery.nome == 'Marco Aurélio Abel Da Silva',
                Surgery.data == datetime(2025, 3, 24).date()
            ).order_by(Surgery.created_at.asc()).all()

            if len(marco_duplicates) > 1:
                earliest = marco_duplicates[0]
                # Delete all other records
                for record in marco_duplicates[1:]:
                    logger.info(f"Deleting duplicate for {record.nome} (ID: {record.id}) from {record.data}")
                    db.session.delete(record)
                db.session.commit()
                logger.info(f"Kept earliest record (ID: {earliest.id})")

            # Handle Luiz Henrique case (similar names)
            luiz_records = Surgery.query.filter(
                Surgery.data == datetime(2025, 3, 20).date(),
                db.or_(
                    Surgery.nome == 'Luiz Henrique de Oliveira',
                    Surgery.nome == 'Luiz Henrique de Oliveira Pádua'
                )
            ).all()

            if len(luiz_records) > 1:
                # Keep the more complete name version
                keep_record = next(r for r in luiz_records if r.nome == 'Luiz Henrique de Oliveira Pádua')
                for record in luiz_records:
                    if record.id != keep_record.id:
                        logger.info(f"Deleting duplicate for {record.nome} from {record.data}")
                        db.session.delete(record)

            # Commit all changes
            db.session.commit()

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


from app import app, db

def drop_all_tables():
    with app.app_context():
        db.drop_all()
        print("✅ Todas as tabelas foram removidas")

if __name__ == "__main__":
    drop_all_tables()

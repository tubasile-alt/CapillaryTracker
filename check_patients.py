
import pandas as pd
from app import app, Surgery, db

# Check Excel file
excel_df = pd.read_excel("cirurgias.xlsx")
excel_count = len(excel_df)
print(f"Pacientes no arquivo Excel: {excel_count}")

# Check database
with app.app_context():
    db_count = Surgery.query.count()
    print(f"Pacientes no banco de dados: {db_count}")

if excel_count != db_count:
    print("\nDiscrepância detectada! Vamos importar os dados do Excel para o banco:")
    
    # Import data from Excel to DB
    with app.app_context():
        # Clear existing data
        Surgery.query.delete()
        
        # Import from Excel
        for _, row in excel_df.iterrows():
            surgery = Surgery(
                data=pd.to_datetime(row['data']).date(),
                nome=row['nome'],
                unidade=row['unidade'],
                medico=row['medico'],
                equipe=row['equipe'],
                hora_cirurgia=row['hora_cirurgia'],
                tempo_cirurgia=float(row['tempo_cirurgia']) if pd.notna(row['tempo_cirurgia']) else 0,
                total_foliculos=int(row['total_foliculos']) if pd.notna(row['total_foliculos']) else 0,
                frente=int(row['frente']) if pd.notna(row['frente']) else 0,
                densidade_scketh=float(row['densidade_scketh']) if pd.notna(row['densidade_scketh']) else 0,
                coroa=int(row['coroa']) if pd.notna(row['coroa']) else 0,
                scalpe=int(row['scalpe']) if pd.notna(row['scalpe']) else 0,
                peninsula_direita=int(row['peninsula_direita']) if pd.notna(row['peninsula_direita']) else 0,
                peninsula_esquerda=int(row['peninsula_esquerda']) if pd.notna(row['peninsula_esquerda']) else 0
            )
            db.session.add(surgery)
        db.session.commit()
        print("✅ Dados importados com sucesso! Por favor, recarregue a página do dashboard.")

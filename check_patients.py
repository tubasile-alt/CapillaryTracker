
import pandas as pd

def check_patients():
    # Lista de pacientes a verificar
    patients_to_check = [
        "Carlos Eduardo Milani",
        "Jonas Galatti Carbonera", 
        "adnan jamil el homoui",
        "Hygor Henrique Bonfante",
        "Eduardo Roncaglia de Carvalho",
        "Weslei Diego Pavini",
        "Mauricio Ronaldo Ribeiro",
        "José Antônio Tonetto Neto"
    ]
    
    try:
        # Carregar banco de dados atual
        df = pd.read_excel("cirurgias.xlsx")
        
        print("\n=== Verificação de Pacientes ===\n")
        
        # Verificar cada paciente
        for patient in patients_to_check:
            # Buscar de forma case-insensitive
            found = df['nome'].str.lower() == patient.lower()
            if found.any():
                print(f"✅ {patient} - Encontrado")
            else:
                print(f"❌ {patient} - Não encontrado")
                
        print("\n=============================")
        
    except Exception as e:
        print(f"Erro ao verificar pacientes: {str(e)}")

if __name__ == "__main__":
    check_patients()

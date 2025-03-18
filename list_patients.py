
import pandas as pd

def list_patients():
    try:
        df = pd.read_excel("cirurgias.xlsx")
        print("\n=== Lista de Pacientes Atuais ===\n")
        for i, row in df.iterrows():
            nome = row['nome']
            data = row['data']
            unidade = row['unidade']
            print(f"{i+1}. {nome} ({unidade}) - {data}")
        print("\n===============================")
    except Exception as e:
        print(f"Erro ao listar pacientes: {str(e)}")

if __name__ == "__main__":
    list_patients()

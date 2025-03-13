
import requests
import os
import pandas as pd
from io import BytesIO

# URL da versão implantada do aplicativo
DEPLOYED_URL = "https://seudominiopublicado.repl.co"  # Substitua pelo URL real

def download_excel(path):
    """Baixa arquivo Excel da versão implantada"""
    try:
        # Endpoint para download do Excel
        url = f"{DEPLOYED_URL}/{path}"
        response = requests.get(url)
        
        if response.status_code == 200:
            return BytesIO(response.content)
        else:
            print(f"Erro ao fazer download do arquivo {path}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Erro na requisição: {str(e)}")
        return None

def import_data():
    # Importar dados de cirurgias
    cirurgias_data = download_excel("download_excel")
    if cirurgias_data:
        # Salvar o arquivo baixado
        df = pd.read_excel(cirurgias_data)
        df.to_excel("cirurgias.xlsx", index=False)
        print(f"✅ Arquivo cirurgias.xlsx importado com sucesso! ({len(df)} registros)")
    else:
        print("❌ Não foi possível importar os dados de cirurgias.")
    
    # A mesma coisa poderia ser feita para necroses.xlsx se necessário

if __name__ == "__main__":
    import_data()
    print("Processo de importação concluído.")

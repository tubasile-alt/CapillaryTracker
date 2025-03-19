
import pandas as pd

df = pd.read_excel("attached_assets/relatorio_cirurgias.xlsx")
total_patients = len(df)
print(f"Total de pacientes no arquivo: {total_patients}")

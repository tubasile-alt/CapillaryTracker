
from app import app, Surgery
from fuzzywuzzy import fuzz
from collections import defaultdict

def find_duplicate_patients():
    print("\n=== Procurando pacientes possivelmente duplicados ===\n")
    
    with app.app_context():
        # Get all patients
        patients = Surgery.query.all()
        
        # Create dict to store similar names
        similar_names = defaultdict(list)
        
        # Compare each pair of names
        for i, p1 in enumerate(patients):
            for p2 in patients[i+1:]:
                # Calculate similarity ratio
                ratio = fuzz.ratio(p1.nome.lower(), p2.nome.lower())
                
                # If names are very similar (>85% match)
                if ratio > 85:
                    key = p1.nome if p1.id < p2.id else p2.nome
                    similar_names[key].extend([
                        (p1.nome, p1.data, p1.unidade),
                        (p2.nome, p2.data, p2.unidade)
                    ])
        
        # Print results
        if similar_names:
            print("Possíveis duplicatas encontradas:")
            for _, entries in similar_names.items():
                print("\nGrupo de registros similares:")
                for nome, data, unidade in sorted(set(entries)):
                    print(f"- {nome} ({unidade}) - {data.strftime('%d/%m/%Y')}")
        else:
            print("Nenhuma duplicata encontrada!")

if __name__ == "__main__":
    find_duplicate_patients()

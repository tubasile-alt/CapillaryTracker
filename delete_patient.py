
import pandas as pd
import shutil
from datetime import datetime
import os

def delete_first_patient():
    try:
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"data_backup/cirurgias_{timestamp}.xlsx"
        os.makedirs("data_backup", exist_ok=True)
        shutil.copy2("cirurgias.xlsx", backup_path)
        print(f"✅ Backup created at {backup_path}")
        
        # Read and modify data
        df = pd.read_excel("cirurgias.xlsx")
        df = df.iloc[1:]  # Remove first row
        df.to_excel("cirurgias.xlsx", index=False)
        print("✅ First patient deleted successfully")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    delete_first_patient()


import pandas as pd
import shutil
from datetime import datetime
import os

def delete_specific_patients():
    try:
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"data_backup/cirurgias_{timestamp}.xlsx"
        os.makedirs("data_backup", exist_ok=True)
        shutil.copy2("cirurgias.xlsx", backup_path)
        print(f"✅ Backup created at {backup_path}")
        
        # Read data
        df = pd.read_excel("cirurgias.xlsx")
        
        # Remove Arthur and keep only first Douglas
        initial_count = len(df)
        df = df[df['nome'].str.lower() != 'arthur']
        df = df.drop_duplicates(subset=['nome'], keep='first')
        final_count = len(df)
        
        # Save changes
        df.to_excel("cirurgias.xlsx", index=False)
        print(f"✅ Removed {initial_count - final_count} entries")
        print(f"✅ Current total patients: {final_count}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    delete_specific_patients()


import pandas as pd
from datetime import datetime
import os
import shutil

def remove_specific_duplicates():
    try:
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"data_backup/cirurgias_{timestamp}.xlsx"
        os.makedirs("data_backup", exist_ok=True)
        shutil.copy2("cirurgias.xlsx", backup_path)
        print(f"✅ Backup created at {backup_path}")
        
        # Read data
        df = pd.read_excel("cirurgias.xlsx")
        initial_count = len(df)
        
        # Remove duplicates for specific patients
        df = df.sort_values('data').drop_duplicates(
            subset=['nome'], 
            keep='first',
            inplace=False
        )
        
        # Save changes
        df.to_excel("cirurgias.xlsx", index=False)
        final_count = len(df)
        
        print(f"✅ Removed {initial_count - final_count} duplicate entries")
        print(f"✅ Current total patients: {final_count}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    remove_specific_duplicates()

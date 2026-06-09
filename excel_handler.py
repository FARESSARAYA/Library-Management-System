import pandas as pd
from tkinter import filedialog, messagebox
import os
from datetime import datetime

EXCEL_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
os.makedirs(EXCEL_FOLDER, exist_ok=True)

class ExcelHandler:
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
    
    def export_table_to_excel(self, table_name, db_connection):
        try:
            query = f"SELECT * FROM {table_name}"
            df = pd.read_sql_query(query, db_connection)
            
            if df.empty:
                messagebox.showwarning("Warning", "No data found")
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{table_name}_{timestamp}.xlsx"
            file_path = os.path.join(EXCEL_FOLDER, file_name)
            
            df.to_excel(file_path, index=False, engine='openpyxl')
            messagebox.showinfo("Success", f"Exported to:\n{file_path}")
            return file_path
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return None
    
    def import_excel_to_table(self, table_name, db_connection, if_exists='append'):
        try:
            file_path = filedialog.askopenfilename(
                title="Select Excel file",
                filetypes=[("Excel files", "*.xlsx *.xls")]
            )
            
            if not file_path:
                return None, "No file selected"
            
            df = pd.read_excel(file_path, sheet_name=0)
            
            if not messagebox.askyesno("Confirm", f"Rows: {len(df)}\nContinue?"):
                return None, "Cancelled"
            
            df.to_sql(table_name, db_connection, if_exists=if_exists, index=False)
            return len(df), f"Imported {len(df)} rows"
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    def backup_all_tables(self, db_connection):
        tables = ['materials', 'sales', 'purchases', 'traders']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(EXCEL_FOLDER, f"backup_{timestamp}.xlsx")
        
        try:
            with pd.ExcelWriter(backup_file, engine='openpyxl') as writer:
                for table in tables:
                    try:
                        df = pd.read_sql_query(f"SELECT * FROM {table}", db_connection)
                        if not df.empty:
                            df.to_excel(writer, sheet_name=table, index=False)
                    except:
                        continue
            
            messagebox.showinfo("Success", f"Backup saved to:\n{backup_file}")
            return backup_file
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return None
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime
import os
from utils import validate_date, validate_time, validate_numeric, validate_range

class HairSurgeryForm:
    def __init__(self, root):
        self.root = root
        self.root.title("Formulário de Cirurgia Capilar")
        self.root.geometry("800x900")

        # Create main frame with scrollbar
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas with scrollbar
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack scrollbar components
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Initialize form fields
        self.initialize_form()

    def initialize_form(self):
        # Dictionary to store entry widgets
        self.entries = {}
        
        # Basic information section
        ttk.Label(self.scrollable_frame, text="Informações Básicas", font=('Helvetica', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        fields = [
            ("Data (DD/MM/AAAA)", "date"),
            ("Paciente", "text"),
            ("Médico", "text"),
            ("Equipe", "text"),
            ("Hora da Cirurgia (HH:MM)", "time"),
            ("Tempo de Cirurgia (horas)", "numeric"),
            ("Total de Folículos", "numeric"),
            ("Frente", "numeric"),
            ("Densidade Scketh", "numeric"),
            ("Coroa", "numeric"),
            ("Scalpe", "numeric"),
            ("Península Direita", "numeric"),
            ("Península Esquerda", "numeric"),
            ("Punch", "numeric"),
            ("Solução Frente (ml)", "numeric"),
            ("Solução Coroa (ml)", "numeric"),
            ("Solução Xilo Frente (ml)", "numeric"),
            ("LE", "numeric"),
            ("ME", "numeric"),
            ("MD", "numeric"),
            ("LD", "numeric"),
            ("Infiltração (1-3)", "range"),
            ("Sedação (1-3)", "range"),
            ("Sangramento (1-3)", "range")
        ]

        # Create entry fields
        for idx, (field, field_type) in enumerate(fields):
            ttk.Label(self.scrollable_frame, text=field).grid(row=idx+1, column=0, padx=5, pady=2, sticky="e")
            entry = ttk.Entry(self.scrollable_frame, width=30)
            entry.grid(row=idx+1, column=1, padx=5, pady=2)
            self.entries[field] = entry

        # Yes/No questions section
        ttk.Label(self.scrollable_frame, text="Informações Adicionais", font=('Helvetica', 12, 'bold')).grid(row=len(fields)+1, column=0, columnspan=2, pady=10)
        
        yes_no_fields = [
            "Safira?",
            "Implante Secundário?",
            "Transamin?",
            "Tadalafila?",
            "Diprospam/Beta 30?",
            "Fumante?"
        ]

        # Create comboboxes for Yes/No questions
        for idx, field in enumerate(yes_no_fields):
            ttk.Label(self.scrollable_frame, text=field).grid(row=len(fields)+idx+2, column=0, padx=5, pady=2, sticky="e")
            combo = ttk.Combobox(self.scrollable_frame, values=["Sim", "Não"], width=27, state="readonly")
            combo.set("Não")
            combo.grid(row=len(fields)+idx+2, column=1, padx=5, pady=2)
            self.entries[field] = combo

        # Text areas for additional information
        ttk.Label(self.scrollable_frame, text="Antecedentes Pessoais").grid(row=len(fields)+len(yes_no_fields)+2, column=0, padx=5, pady=2, sticky="e")
        self.entries["Antecedentes Pessoais"] = tk.Text(self.scrollable_frame, height=3, width=30)
        self.entries["Antecedentes Pessoais"].grid(row=len(fields)+len(yes_no_fields)+2, column=1, padx=5, pady=2)

        ttk.Label(self.scrollable_frame, text="Comentários").grid(row=len(fields)+len(yes_no_fields)+3, column=0, padx=5, pady=2, sticky="e")
        self.entries["Comentários"] = tk.Text(self.scrollable_frame, height=3, width=30)
        self.entries["Comentários"].grid(row=len(fields)+len(yes_no_fields)+3, column=1, padx=5, pady=2)

        # Save button
        ttk.Button(self.scrollable_frame, text="Salvar Dados", command=self.save_data).grid(row=len(fields)+len(yes_no_fields)+4, column=0, columnspan=2, pady=20)

    def validate_fields(self):
        # Validate date
        date_value = self.entries["Data (DD/MM/AAAA)"].get()
        if not validate_date(date_value):
            messagebox.showerror("Erro", "Data inválida. Use o formato DD/MM/AAAA")
            return False

        # Validate time
        time_value = self.entries["Hora da Cirurgia (HH:MM)"].get()
        if not validate_time(time_value):
            messagebox.showerror("Erro", "Hora inválida. Use o formato HH:MM")
            return False

        # Validate numeric fields
        numeric_fields = [
            "Tempo de Cirurgia (horas)", "Total de Folículos", "Frente", "Densidade Scketh",
            "Coroa", "Scalpe", "Península Direita", "Península Esquerda", "Punch",
            "Solução Frente (ml)", "Solução Coroa (ml)", "Solução Xilo Frente (ml)",
            "LE", "ME", "MD", "LD"
        ]
        
        for field in numeric_fields:
            value = self.entries[field].get()
            if value and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False

        # Validate range fields (1-3)
        range_fields = ["Infiltração (1-3)", "Sedação (1-3)", "Sangramento (1-3)"]
        for field in range_fields:
            value = self.entries[field].get()
            if value and not validate_range(value, 1, 3):
                messagebox.showerror("Erro", f"O campo {field} deve estar entre 1 e 3")
                return False

        return True

    def save_data(self):
        if not self.validate_fields():
            return

        # Prepare data for saving
        data = {}
        for field, widget in self.entries.items():
            if isinstance(widget, tk.Text):
                data[field] = widget.get("1.0", tk.END).strip()
            else:
                data[field] = widget.get()

        # Create DataFrame
        df_new = pd.DataFrame([data])

        # Check if file exists and append or create new
        filename = "cirurgias.xlsx"
        if os.path.exists(filename):
            df_existing = pd.read_excel(filename)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_excel(filename, index=False)
        else:
            df_new.to_excel(filename, index=False)

        messagebox.showinfo("Sucesso", "Dados salvos com sucesso!")
        self.clear_form()

    def clear_form(self):
        for widget in self.entries.values():
            if isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
            elif isinstance(widget, ttk.Combobox):
                widget.set("Não")
            else:
                widget.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = HairSurgeryForm(root)
    root.mainloop()

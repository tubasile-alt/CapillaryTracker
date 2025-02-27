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
        self.root.geometry("800x600")

        # Dictionary to store all entry widgets
        self.entries = {}

        # Create and store all frames
        self.frames = {}
        self.current_frame = None
        self.create_frames()

        # Show first frame
        self.show_frame("Dados Gerais")

    def create_frames(self):
        # Create all frames but only show the first one
        frame_configs = {
            "Dados Gerais": {
                "fields": [
                    ("Data (DD/MM/AAAA)", "date"),
                    ("Paciente", "text"),
                    ("Médico", "text"),
                    ("Equipe", "text"),
                    ("Hora da Cirurgia (HH:MM)", "time"),
                    ("Tempo de Cirurgia (horas)", "numeric")
                ],
                "required": ["Data (DD/MM/AAAA)", "Paciente", "Médico", "Equipe", 
                           "Hora da Cirurgia (HH:MM)", "Tempo de Cirurgia (horas)"]
            },
            "Informações do Implante": {
                "fields": [
                    ("Total de Folículos", "numeric"),
                    ("Frente", "numeric"),
                    ("Densidade Scketh", "numeric"),
                    ("Coroa", "numeric"),
                    ("Scalpe", "numeric"),
                    ("Península Direita", "numeric"),
                    ("Península Esquerda", "numeric")
                ],
                "required": ["Total de Folículos"]
            },
            "Procedimentos": {
                "fields": [
                    ("Safira?", "yesno"),
                    ("Punch", "numeric"),
                    ("Solução Frente (ml)", "numeric"),
                    ("Solução Coroa (ml)", "numeric"),
                    ("Solução Xilo Frente (ml)", "numeric")
                ],
                "required": ["Punch"]
            },
            "Distribuição": {
                "fields": [
                    ("LE", "numeric"),
                    ("ME", "numeric"),
                    ("MD", "numeric"),
                    ("LD", "numeric")
                ],
                "required": ["LE", "ME", "MD", "LD"]
            },
            "Avaliação": {
                "fields": [
                    ("Infiltração (1-3)", "range"),
                    ("Sedação (1-3)", "range"),
                    ("Sangramento (1-3)", "range")
                ],
                "required": ["Infiltração (1-3)", "Sedação (1-3)", "Sangramento (1-3)"]
            },
            "Histórico": {
                "fields": [
                    ("Implante Secundário?", "yesno"),
                    ("Transamin?", "yesno"),
                    ("Tadalafila?", "yesno"),
                    ("Diprospam/Beta 30?", "yesno"),
                    ("Fumante?", "yesno"),
                    ("Antecedentes Pessoais", "text_area")
                ],
                "required": ["Implante Secundário?", "Fumante?"]
            },
            "Finalização": {
                "fields": [
                    ("Comentários", "text_area")
                ],
                "required": []
            }
        }

        for frame_name, config in frame_configs.items():
            frame = ttk.Frame(self.root)
            frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

            # Title
            ttk.Label(frame, text=frame_name, font=('Helvetica', 12, 'bold')).grid(
                row=0, column=0, columnspan=2, pady=10)

            # Create fields
            for idx, (field, field_type) in enumerate(config["fields"]):
                ttk.Label(frame, text=field).grid(row=idx+1, column=0, padx=5, pady=2, sticky="e")

                if field_type == "yesno":
                    widget = ttk.Combobox(frame, values=["Sim", "Não"], width=27, state="readonly")
                    widget.set("Não")
                elif field_type == "text_area":
                    widget = tk.Text(frame, height=3, width=30)
                else:
                    widget = ttk.Entry(frame, width=30)

                widget.grid(row=idx+1, column=1, padx=5, pady=2)
                self.entries[field] = widget

            # Navigation buttons
            button_frame = ttk.Frame(frame)
            button_frame.grid(row=len(config["fields"])+1, column=0, columnspan=2, pady=20)

            if frame_name != "Dados Gerais":
                ttk.Button(button_frame, text="Anterior", 
                          command=lambda name=frame_name: self.previous_frame(name)).pack(side=tk.LEFT, padx=5)

            if frame_name == "Finalização":
                ttk.Button(button_frame, text="Salvar Dados", 
                          command=self.save_data).pack(side=tk.LEFT, padx=5)
            else:
                ttk.Button(button_frame, text="Próximo", 
                          command=lambda name=frame_name: self.next_frame(name)).pack(side=tk.LEFT, padx=5)

            self.frames[frame_name] = {"frame": frame, "config": config}
            frame.grid_remove()  # Hide frame initially

    def show_frame(self, frame_name):
        if self.current_frame:
            self.frames[self.current_frame]["frame"].grid_remove()
        self.frames[frame_name]["frame"].grid()
        self.current_frame = frame_name

    def validate_current_frame(self):
        config = self.frames[self.current_frame]["config"]

        for field in config["required"]:
            widget = self.entries[field]
            if isinstance(widget, tk.Text):
                value = widget.get("1.0", tk.END).strip()
            else:
                value = widget.get()

            if not value:
                messagebox.showerror("Erro", f"O campo {field} é obrigatório!")
                return False

            # Validate specific field types
            if field.endswith("(DD/MM/AAAA)") and not validate_date(value):
                messagebox.showerror("Erro", "Data inválida. Use o formato DD/MM/AAAA")
                return False
            elif field.endswith("(HH:MM)") and not validate_time(value):
                messagebox.showerror("Erro", "Hora inválida. Use o formato HH:MM")
                return False
            elif field.endswith("(1-3)") and not validate_range(value, 1, 3):
                messagebox.showerror("Erro", f"O campo {field} deve estar entre 1 e 3")
                return False
            elif field.endswith(" (horas)") and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False
            elif field.endswith("(ml)") and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False
            elif field.endswith("Folículos") and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False
            elif field.endswith("Scketh") and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False
            elif field.endswith("Coroa") and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False
            elif field.endswith("Scalpe") and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False
            elif field.endswith("Direita") and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False
            elif field.endswith("Esquerda") and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False
            elif field.endswith("Punch") and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False
            elif field.endswith("LE") and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False
            elif field.endswith("ME") and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False
            elif field.endswith("MD") and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False
            elif field.endswith("LD") and not validate_numeric(value):
                messagebox.showerror("Erro", f"O campo {field} deve ser numérico")
                return False




        return True

    def next_frame(self, current_frame):
        if not self.validate_current_frame():
            return

        frame_order = list(self.frames.keys())
        next_idx = frame_order.index(current_frame) + 1
        if next_idx < len(frame_order):
            self.show_frame(frame_order[next_idx])

    def previous_frame(self, current_frame):
        frame_order = list(self.frames.keys())
        prev_idx = frame_order.index(current_frame) - 1
        if prev_idx >= 0:
            self.show_frame(frame_order[prev_idx])

    def save_data(self):
        if not self.validate_current_frame():
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
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = HairSurgeryForm(root)
    root.mainloop()
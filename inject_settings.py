import os
import re

ui_path = 'ui.py'
with open(ui_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace specific imports with module import to support live reloading
text = text.replace(
    'from config import DEFAULT_TVA, COMPANY, DOC_TYPES, DEFAULT_COLUMNS',
    'import config\nfrom config import COMPANY, DOC_TYPES, DEFAULT_COLUMNS\nfrom config import save_settings'
)

# Fix DEFAULT_TVA usage
text = text.replace(
    'str(DEFAULT_TVA)',
    'str(config.DEFAULT_TVA)'
)

# Provide the SettingsWindow class code
settings_gui_code = '''
# ==========================================
# Fenêtre : Paramètres (Settings)
# ==========================================
class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("⚙ Paramètres de l'application")
        self.geometry("600x650")
        self.grab_set()
        self.resizable(False, False)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Tab 1: Informations Entreprise ──
        tab_company = ttk.Frame(notebook)
        notebook.add(tab_company, text="  Informations Entreprise  ")
        
        self.comp_entries = {}
        comp_fields = [
            ("Nom d'Entreprise", "name"), ("Slogan", "slogan"), ("Dirigeant", "manager"),
            ("Adresse", "address"), ("Ville", "city"), ("Téléphone", "phone"),
            ("Email", "email"), ("RC", "rc"), ("Patente", "patente"),
            ("Num. IF", "if_num"), ("ICE", "ice"),
            ("Banque", "rib_bank"), ("RIB", "rib")
        ]
        
        for i, (label, key) in enumerate(comp_fields):
            ttk.Label(tab_company, text=label + " :").grid(row=i, column=0, padx=10, pady=6, sticky="e")
            e = ttk.Entry(tab_company, width=45)
            e.insert(0, config.COMPANY.get(key, ""))
            e.grid(row=i, column=1, padx=10, pady=6, sticky="w")
            self.comp_entries[key] = e

        # ── Tab 2: Devis & Factures ──
        tab_docs = ttk.Frame(notebook)
        notebook.add(tab_docs, text="  Devis & Factures  ")
        
        ttk.Label(tab_docs, text="TVA par défaut (%) :").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.e_tva = ttk.Entry(tab_docs, width=15)
        self.e_tva.insert(0, str(config.DEFAULT_TVA))
        self.e_tva.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(tab_docs, text="Validité Devis (Jours) :").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.e_valid = ttk.Entry(tab_docs, width=15)
        self.e_valid.insert(0, str(config.DEVIS_VALIDITY_DAYS))
        self.e_valid.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(tab_docs, text="Conditions Devis :").grid(row=2, column=0, padx=10, pady=10, sticky="ne")
        self.t_cond_devis = tk.Text(tab_docs, width=45, height=5, font=("Helvetica", 9))
        self.t_cond_devis.insert("1.0", "\\n".join(config.DOC_TYPES["devis"].get("conditions", [])))
        self.t_cond_devis.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(tab_docs, text="Conditions Facture :").grid(row=3, column=0, padx=10, pady=10, sticky="ne")
        self.t_cond_fac = tk.Text(tab_docs, width=45, height=5, font=("Helvetica", 9))
        self.t_cond_fac.insert("1.0", "\\n".join(config.DOC_TYPES["facture"].get("conditions", [])))
        self.t_cond_fac.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # ── Bottom Bar ──
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Annuler", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="💾 Enregistrer", command=self.save).pack(side="right", padx=5)

    def save(self):
        # Update Company
        for k, e in self.comp_entries.items():
            config.COMPANY[k] = e.get().strip()
        
        # Update TVA and Validity
        try:
            config.DEFAULT_TVA = int(self.e_tva.get().strip())
        except ValueError:
            pass
        try:
            config.DEVIS_VALIDITY_DAYS = int(self.e_valid.get().strip())
            config.DOC_TYPES["devis"]["validity_line"] = f"Validité : {config.DEVIS_VALIDITY_DAYS} Jours"
        except ValueError:
            pass
            
        # Update conditions
        c_devis = [c.strip() for c in self.t_cond_devis.get("1.0", "end-1c").split("\\n") if c.strip()]
        c_fac = [c.strip() for c in self.t_cond_fac.get("1.0", "end-1c").split("\\n") if c.strip()]
        
        config.DOC_TYPES["devis"]["conditions"] = c_devis
        config.DOC_TYPES["facture"]["conditions"] = c_fac
        
        # Persist and close
        config.save_settings()
        from tkinter import messagebox
        messagebox.showinfo("Succès", "Paramètres mis à jour avec succès !", parent=self)
        self.destroy()

'''

# Inject SettingsWindow before AppDevis
text = text.replace(
    '# Fenêtre principale\n# ==========================================\n\nclass AppDevis(tk.Tk):',
    settings_gui_code + '# ==========================================\n# Fenêtre principale\n# ==========================================\n\nclass AppDevis(tk.Tk):'
)

# Inject the button into AppDevis UI
btn_code = '''
        # Bouton Paramètres
        btn_settings = ttk.Button(self, text="⚙ Paramètres", command=lambda: SettingsWindow(self))
        btn_settings.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne")
'''

text = text.replace(
    'ttk.Style().theme_use("clam")',
    'ttk.Style().theme_use("clam")\n' + btn_code
)

with open(ui_path, 'w', encoding='utf-8') as f:
    f.write(text)

print('ui.py successfully updated with SettingsWindow.')

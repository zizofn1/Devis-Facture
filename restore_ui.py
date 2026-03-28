import os

with open('ui.py', 'r', encoding='utf-8') as f:
    text = f.read()

prefix_end = text.find('    def save(self):')
if prefix_end != -1:
    clean_prefix = text[:prefix_end]
else:
    print('save(self) not found')
    os._exit(1)

new_tail = """    def save(self):
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

# ==========================================
# Fenêtre : Guide d'utilisation et Aide
# ==========================================
class HelpWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("📖 Guide d'utilisation & FAQ")
        self.geometry("650x550")
        self.grab_set()
        
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        guides = {
            "Articles & Calculs": (
                "• Utiliser le bouton [＋ Ajouter] pour insérer un produit/service.\\n\\n"
                "• [Double-Clic] sur n'importe quelle ligne pour modifier ses quantités ou son prix.\\n\\n"
                "• Sélectionner une ou plusieurs lignes et cliquer sur [✕ Supprimer] pour les effacer.\\n\\n"
                "• Le montant Total, la TVA, et le TTC se mettent à jour automatiquement à chaque modification."
            ),
            "Colonnes du Tableau": (
                "• [Clic Droit] sur l'en-tête d'une colonne permet de l'Afficher, la Masquer du PDF, ou la Renommer.\\n\\n"
                "• La Désignation et le Total HT sont obligatoires pour un Devis valide et ne peuvent être masqués.\\n\\n"
                "• Utilisez [⊞ Nouvelle colonne] pour ajouter une colonne personnalisée au PDF, utile pour afficher l'Unité ou la Remise."
            ),
            "Numérotation": (
                "• Le Numéro (N° Devis/Facture) est auto-généré sur la base du nom du Client.\\n\\n"
                "• Remplissez simplement le champ 'Nom Client' et cliquez ailleurs, le numéro prendra les initiales du client automatiquement.\\n\\n"
                "• Vous pouvez toujours cliquer sur [🔄 Générer N°] ou modifier le champ manuellement à votre guise."
            ),
            "Génération PDF": (
                "• Cliquez sur le grand bouton [📄 GÉNÉRER LA FACTURE/DEVIS] en bas à droite.\\n\\n"
                "• Le système vous demandera où vous souhaitez l'enregistrer (Il propose automatiquement le nom du client avec le bon titre).\\n\\n"
                "• Après l'enregistrement, l'application tentera d'ouvrir le fichier PDF immédiatement."
            ),
            "FAQ & Problèmes": (
                "❓ Problème : Le devis n'est pas enregistré lorsque je ferme l'application ?\\n"
                "💡 Solution : L'application n'enregistre pas automatiquement les anciens devis, elle vous permet de générer des PDF. Assurez-vous d'avoir enregistré le PDF final sur votre ordinateur.\\n\\n"
                
                "❓ Problème : Mon logo d'entreprise ne s'affiche pas sur le PDF !\\n"
                "💡 Solution : Placez une image nommée 'logo.png' dans le même dossier que l'application, sinon le logiciel le désactivera automatiquement pour éviter un crash.\\n\\n"
                
                "❓ Problème : J'ai modifié les Paramètres mais rien n'a changé sur mon PDF.\\n"
                "💡 Solution : Êtes-vous sûr d'avoir cliqué sur [💾 Enregistrer] à l'intérieur de la fenêtre Paramètres ? Sinon, vos modifications seront ignorées."
            )
        }
        
        for title, text in guides.items():
            frame = ttk.Frame(notebook, padding=10)
            notebook.add(frame, text=f" {title} ")
            
            txt = tk.Text(frame, wrap="word", font=("Helvetica", 10), bg=self.cget('bg'), relief="flat")
            txt.insert("1.0", text)
            txt.config(state="disabled") # Lecture seule
            txt.pack(fill="both", expand=True)
            
        ttk.Button(self, text="Fermer l'aide", command=self.destroy).pack(pady=10)


# ==========================================
# Fenêtre principale
# ==========================================

class AppDevis(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(f"Générateur Devis & Factures — {config.COMPANY['name']}")
        self.geometry("900x700")
        self.configure(padx=8, pady=8)

        ttk.Style().theme_use("clam")

        # ==========================================
        # Barre de Menus (Aide)
        # ==========================================
        menubar = tk.Menu(self)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="📖 Guide d'utilisation", command=lambda: HelpWindow(self))
        help_menu.add_separator()
        from tkinter import messagebox
        help_menu.add_command(label="À propos", command=lambda: messagebox.showinfo("À propos", f"Générateur Devis & Factures v2.0\\nDéveloppé pour {config.COMPANY.get('name', 'Fun Design')}"))
        
        menubar.add_cascade(label="Aide (?)", menu=help_menu)
        self.config(menu=menubar)
        
        # Colonnes partagées entre les deux onglets
        self._columns = load_columns()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        for doc_type in ("devis", "facture"):
            tab = DocumentTab(notebook, doc_type, self._columns)
            notebook.add(tab, text=f"  {config.DOC_TYPES[doc_type]['label']}  ")

        ttk.Label(
            self,
            text="💡 Clic droit sur un en-tête pour renommer/masquer · ⊞ Nouvelle colonne pour en ajouter une",
            foreground="#64748b", font=("Helvetica", 9),
        ).pack(side="bottom", pady=4)

        # Bouton Paramètres (Placé en haut à droite, au dessus du notebook)
        btn_settings = ttk.Button(self, text="⚙ Paramètres", command=lambda: SettingsWindow(self))
        btn_settings.place(relx=1.0, rely=0.0, x=-12, y=6, anchor="ne")
        btn_settings.lift()
"""

with open('ui.py', 'w', encoding='utf-8') as f:
    f.write(clean_prefix + new_tail)

print('Cleaned and rebuilt ui.py fully!')

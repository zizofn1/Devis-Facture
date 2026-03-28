import os

ui_path = 'ui.py'
with open(ui_path, 'r', encoding='utf-8') as f:
    text = f.read()

MENU_CODE = '''
        # ==========================================
        # Barre de Menus (Aide)
        # ==========================================
        menubar = tk.Menu(self)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="📖 Guide d'utilisation", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="À propos", command=lambda: messagebox.showinfo("À propos", f"Générateur Devis & Factures v2.0\\nDéveloppé pour {config.COMPANY.get('name', 'Fun Design')}"))
        
        menubar.add_cascade(label="Aide (?)", menu=help_menu)
        self.config(menu=menubar)
        
    def show_help(self):
        help_msg = """📖 GUIDE D'UTILISATION :\\n
1. ARTICLES & LIGNES
 • [＋ Ajouter] : Ajouter une nouvelle ligne (produit/service).
 • [Double-Clic] sur une ligne pour la modifier.
 • Sélectionnez une ligne et cliquez sur [✕ Supprimer] pour l'effacer.
 • Les calculs (Total, TVA, TTC) se font tous seuls !\\n
2. COLONNES & TABLEAU
 • [Clic Droit] sur le titre d'une colonne : Permet de la renommer ou de la masquer pour qu'elle n'apparaisse pas sur le PDF.
 • [⊞ Nouvelle colonne] : Créez de nouvelles colonnes si besoin (ex: Unité, Remise).\\n
3. CLIENT & N° DEVIS
 • Remplissez le 'Nom Client' : le Numéro de Devis/Facture prendra automatiquement ses initiales.
 • Appuyez sur [🔄 Générer N°] pour en créer un nouveau.\\n
4. ⚙ PARAMÈTRES (En haut à droite)
 • Changez vos informations d'entreprise à tout instant (Nom, ICE, RIB, Banque, Adresse).
 • Mettez à jour vos Conditions Générales et délais. Tout est sauvegardé automatiquement !\\n
5. PDF FINAL
 • Cliquiez sur [📄 GÉNÉRER]. Renommez si besoin, et le PDF d'une qualité professionnelle s'ouvrira sous vos yeux.
"""
        messagebox.showinfo("Guide d'utilisation", help_msg, parent=self)
'''

# Find the place to inject
target = '        ttk.Style().theme_use("clam")\n'
if 'Barre de Menus' not in text:
    text = text.replace(target, target + MENU_CODE)
    with open(ui_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Help menu injected!")
else:
    print("Help menu already exists.")


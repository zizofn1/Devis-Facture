# ==========================================
# CONFIG.PY — Paramètres & Constantes
# ==========================================

import os
import json
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Informations de l'entreprise
COMPANY = {
    "name":    "Fun Design F&Z",
    "slogan":  "Tous travaux d'aménagement d'intérieur",
    "manager": "Dirigée par Zouhair",
    "address": "77 rue mohamed smiha",
    "city":    "10etg apt57, Casablanca",
    "phone":   "06 56 56 43 13",
    "email":   "contact@fundesignfz.ma",
    "rc":      "642625",
    "patente": "3210587651",
    "if_num":  "66070424",
    "ice":     "003570825000002",
    "logo":    resource_path("logo.png"),
    "rib_bank":"Crédit Agricole",
    "rib":     "000 000 0000000000000000 00",
}

# Couleurs PDF
COLORS = {
    "primary":   "#9a7f85",
    "dark":      "#1e293b",
    "muted":     "#475569",
    "border":    "#e2e8f0",
    "footer":    "#94a3b8",
}

# Conditions générales (affiché sur le devis)
CONDITIONS = [
    "Acompte de 50% à la validation.",
    "Solde de 50% à la livraison.",
    "Délai : 2 semaines après acompte.",
]

# TVA par défaut (%)
DEFAULT_TVA = 20

# Validité du devis (jours)
DEVIS_VALIDITY_DAYS = 30

# ==========================================
# TYPES DE DOCUMENTS
# ==========================================
# Chaque type définit : prefix N°, labels UI, et texte PDF
DOC_TYPES = {
    "devis": {
        "prefix":        "DEV",
        "label":         "DEVIS",
        "title_pdf":     "DEVIS",
        "validity_line": f"Validité : {DEVIS_VALIDITY_DAYS} Jours",
        "sign_left":     "Cachet et Signature",
        "sign_right":    "Bon pour accord\nDate et Signature du Client",
        "conditions":    CONDITIONS,
    },
    "facture": {
        "prefix":        "FAC",
        "label":         "FACTURE",
        "title_pdf":     "FACTURE",
        "validity_line": "",           # pas de validité sur une facture
        "sign_left":     "Cachet et Signature",
        "sign_right":    "Acquitté le :\nSignature du Client",
        "conditions":    [
            "Paiement à réception de facture.",
            "Tout retard entraîne des pénalités de 1,5% par mois.",
            "Escompte pour paiement anticipé : néant.",
        ],
    },
}

# Colonnes du tableau articles — ordre et labels par défaut
# Chaque entrée : (clé interne, label affiché, largeur px, largeur PDF mm, ancre)
DEFAULT_COLUMNS = [
    {"key": "ref",   "label": "Réf.",       "width": 50,  "pdf_mm": 20, "anchor": "center", "visible": True},
    {"key": "desc",  "label": "Désignation","width": 340, "pdf_mm": 80, "anchor": "w",      "visible": True},
    {"key": "qte",   "label": "Qté",        "width": 50,  "pdf_mm": 20, "anchor": "center", "visible": True},
    {"key": "pu",    "label": "P.U (MAD)",  "width": 80,  "pdf_mm": 30, "anchor": "e",      "visible": True},
    {"key": "total", "label": "Total HT",   "width": 80,  "pdf_mm": 30, "anchor": "e",      "visible": True},
]

# ==========================================
# GESTION DES PARAMETRES (SETTINGS)
# ==========================================
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'app_settings.json')

def load_settings():
    global DEVIS_VALIDITY_DAYS, DEFAULT_TVA
    if not os.path.exists(SETTINGS_FILE):
        return
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'COMPANY' in data:
            COMPANY.update(data['COMPANY'])
        if 'COLORS' in data:
            COLORS.update(data['COLORS'])
        if 'CONDITIONS_DEVIS' in data:
            DOC_TYPES['devis']['conditions'] = data['CONDITIONS_DEVIS']
        if 'CONDITIONS_FACTURE' in data:
            DOC_TYPES['facture']['conditions'] = data['CONDITIONS_FACTURE']
        if 'DEVIS_VALIDITY_DAYS' in data:
            DEVIS_VALIDITY_DAYS = int(data['DEVIS_VALIDITY_DAYS'])
            DOC_TYPES['devis']['validity_line'] = f"Validité : {DEVIS_VALIDITY_DAYS} Jours"
        if 'DEFAULT_TVA' in data:
            DEFAULT_TVA = int(data['DEFAULT_TVA'])
    except Exception as e:
        print("Erreur chargement settings:", e)

def save_settings():
    data = {
        'COMPANY': COMPANY,
        'COLORS': COLORS,
        'CONDITIONS_DEVIS': DOC_TYPES['devis'].get('conditions', []),
        'CONDITIONS_FACTURE': DOC_TYPES['facture'].get('conditions', []),
        'DEVIS_VALIDITY_DAYS': DEVIS_VALIDITY_DAYS,
        'DEFAULT_TVA': DEFAULT_TVA,
    }
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print("Paramètres enregistrés avec succès.")
    except Exception as e:
        print("Erreur sauvegarde settings:", e)

# On charge automatiquement au démarrage
load_settings()

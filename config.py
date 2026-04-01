# ==========================================
# CONFIG.PY — Paramètres & Constantes
# ==========================================

APP_VERSION = "1.4.0"
GITHUB_REPO = "zizofn1/Devis-Facture"

import os
import json
import sys

def resource_path(relative_path):
    """ Get absolute path to resource (images), works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_data_dir():
    """ Retourne le dossier persistant dans Documents/Devis/Data. """
    data_dir = os.path.join(os.path.expanduser("~"), "Documents", "Devis", "Data")
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
        except Exception as e:
            # Fallback en cas d'erreur de permission sur Documents
            print(f"Erreur création dossier data: {e}. Fallback vers le répertoire actuel.")
            fallback_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data")
            os.makedirs(fallback_dir, exist_ok=True)
            return fallback_dir
    return data_dir

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
# ==========================================
# GESTION DES PARAMETRES (SETTINGS)
# ==========================================
SETTINGS_FILE = os.path.join(get_data_dir(), 'settings.json')

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
    # Toujours lire d'abord pour ne pas écraser les autres clés (comme 'columns')
    data = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            pass
            
    data.update({
        'COMPANY': COMPANY,
        'COLORS': COLORS,
        'CONDITIONS_DEVIS': DOC_TYPES['devis'].get('conditions', []),
        'CONDITIONS_FACTURE': DOC_TYPES['facture'].get('conditions', []),
        'DEVIS_VALIDITY_DAYS': DEVIS_VALIDITY_DAYS,
        'DEFAULT_TVA': DEFAULT_TVA,
    })
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print("Paramètres enregistrés avec succès.")
    except Exception as e:
        print("Erreur sauvegarde settings:", e)

import copy

def load_columns() -> list[dict]:
    if not os.path.exists(SETTINGS_FILE):
        return copy.deepcopy(DEFAULT_COLUMNS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f).get("columns", [])
        saved_map = {c["key"]: c for c in saved}
        merged = []
        for col in DEFAULT_COLUMNS:
            base = copy.deepcopy(col)
            if col["key"] in saved_map:
                base["label"]   = saved_map[col["key"]].get("label",   col["label"])
                base["visible"] = saved_map[col["key"]].get("visible", col["visible"])
            merged.append(base)
        # Ajouter les colonnes custom non-existantes dans DEFAULT_COLUMNS
        default_keys = {c["key"] for c in DEFAULT_COLUMNS}
        for c in saved:
            if c["key"] not in default_keys:
                c["custom"] = True
                if "width" not in c: c["width"] = 100
                if "pdf_mm" not in c: c["pdf_mm"] = 26
                if "anchor" not in c: c["anchor"] = "w"
                merged.append(c)
        return merged
    except (json.JSONDecodeError, KeyError):
        return copy.deepcopy(DEFAULT_COLUMNS)

def save_columns(columns: list[dict]) -> None:
    data = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            pass
            
    # Ne sauvegarder que les infos essentielles des colonnes
    data["columns"] = []
    for c in columns:
        save_col = {"key": c["key"], "label": c["label"], "visible": c["visible"]}
        if c.get("custom"):
            save_col.update({"custom": True, "width": c.get("width", 100), "pdf_mm": c.get("pdf_mm", 26), "anchor": c.get("anchor", "w")})
        data["columns"].append(save_col)
        
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("Erreur sauvegarde colonnes:", e)

# On charge automatiquement au démarrage
load_settings()

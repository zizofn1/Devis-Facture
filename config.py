# ==========================================
# CONFIG.PY — Paramètres & Constantes
# ==========================================

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
    "logo":    "logo.png",
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

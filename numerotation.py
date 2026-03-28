# ==========================================
# NUMEROTATION.PY — Générateur de N° unique
# ==========================================
# Format : PREFIX-YYYYMMDD-HHMMSS-XX
#   PREFIX  → DEV ou FAC (selon le type de document)
#   DATE    → date du jour  (YYYYMMDD)
#   HEURE   → heure exacte  (HHMMSS)
#   XX      → initiales du client (2 lettres majuscules)
#
# Exemples :
#   DEV-20250327-143022-ZB   (devis pour Zouhair Belkadi)
#   FAC-20250327-091500-MC   (facture pour Mohamed Chakir)

from datetime import datetime


def _extract_initials(client_name: str, fallback: str = "XX") -> str:
    """
    Extrait les initiales du nom client (max 2 lettres, majuscules).
    Exemples :
        "Zakaria Benali"  → "ZB"
        "SARL Amine"      → "SA"
        ""                → "XX"
    """
    words = [w for w in client_name.strip().split() if w.isalpha()]
    if not words:
        return fallback
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def generate_number(doc_type: str, client_name: str = "") -> str:
    """
    Génère un numéro de document unique.

    :param doc_type:    "devis" ou "facture"
    :param client_name: nom du client (pour les initiales)
    :return:            ex. "DEV-20250327-143022-ZB"
    """
    prefix     = "DEV" if doc_type == "devis" else "FAC"
    now        = datetime.now()
    date_part  = now.strftime("%Y%m%d")
    time_part  = now.strftime("%H%M%S")
    initials   = _extract_initials(client_name)

    return f"{prefix}-{date_part}-{time_part}-{initials}"

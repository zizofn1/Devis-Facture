# ==========================================
# NUMEROTATION.PY — Générateur de N° unique
# ==========================================
# Format V3.1 : PREFIX-YYMMDD-XX-XXX
#   PREFIX  → DEV ou FAC (selon le type de document)
#   YYMMDD  → Date compacte
#   XX      → Initiales Client (1ère lettre Prénom + 1ère lettre Nom)
#   XXX     → Numéro séquentiel
#

from datetime import datetime
import database

def _extract_initials(client_name: str) -> str:
    """Extraie les initiales : 1ère lettre du 1er mot et du 2ème mot."""
    words = [w for w in client_name.strip().split() if w.strip()]
    if not words:
        return "XX"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()

def generate_number(doc_type: str, client_name: str = "") -> str:
    """
    Génère un numéro : PREFIX-YYMMDD-XX-XXX
    """
    prefix = "DEV" if doc_type == "devis" else "FAC"
    now = datetime.now()
    yy = now.strftime("%y")
    mm = now.strftime("%m")
    dd = now.strftime("%d")
    initials = _extract_initials(client_name)
    next_num = database.peek_next_sequence(doc_type)
    
    return f"{prefix}-{yy}{mm}{dd}-{initials}-{next_num:03d}"

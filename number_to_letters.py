# ==========================================
# NUMBER_TO_LETTERS.PY
# ==========================================

def int_to_letters(n):
    unites = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
              "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
    dizaines = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]

    if n < 20:
        return unites[n]
    if n < 100:
        d, u = divmod(n, 10)
        if d in (7, 9):
            d -= 1
            u += 10
        res = dizaines[d]
        if u > 0:
            if u == 1 or u == 11:
                res += " et " + unites[u]
            else:
                res += "-" + unites[u]
        else:
            if d == 8: res += "s" # quatre-vingts
        return res
    if n < 1000:
        c, u = divmod(n, 100)
        res = ""
        if c == 1:
            res = "cent"
        else:
            res = unites[c] + " cent"
            if u == 0: res += "s"
        if u > 0:
            res += " " + int_to_letters(u)
        return res
    if n < 1000000:
        m, u = divmod(n, 1000)
        res = ""
        if m == 1:
            res = "mille"
        else:
            res = int_to_letters(m) + " mille"
        if u > 0:
            res += " " + int_to_letters(u)
        return res
    if n < 1000000000:
        m, u = divmod(n, 1000000)
        res = int_to_letters(m) + " million" + ("s" if m > 1 else "")
        if u > 0:
            res += " " + int_to_letters(u)
        return res
    
    return str(n)

def amount_to_letters(amount) -> str:
    """Convertit un montant en toutes lettres (Dirhams et Centimes)."""
    try:
        val = float(amount)
        if val < 0:
            return "Montant négatif invalide"
        
        entier = int(val)
        centimes = int(round((val - entier) * 100))
        
        res = int_to_letters(entier) + " Dirham" + ("s" if entier > 1 else "")
        
        if centimes > 0:
            res += " et " + int_to_letters(centimes) + " Centime" + ("s" if centimes > 1 else "")
            
        return res.capitalize()
    except Exception:
        return ""

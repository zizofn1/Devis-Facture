# ==========================================
# SETTINGS.PY — Persistence des préférences
# ==========================================
# Sauvegarde les colonnes personnalisées dans settings.json
# à côté du script, pour les retrouver à la prochaine session.

import json
import copy
import os

from config import DEFAULT_COLUMNS

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")


def load_columns() -> list[dict]:
    """
    Retourne la liste des colonnes.
    Si settings.json existe, on fusionne avec DEFAULT_COLUMNS
    (pour ajouter d'éventuelles nouvelles colonnes sans casser l'existant).
    """
    if not os.path.exists(SETTINGS_FILE):
        return copy.deepcopy(DEFAULT_COLUMNS)

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f).get("columns", [])

        # Index par clé pour la fusion
        saved_map = {c["key"]: c for c in saved}
        merged = []
        for col in DEFAULT_COLUMNS:
            base = copy.deepcopy(col)
            if col["key"] in saved_map:
                # On récupère seulement label et visible (l'utilisateur peut modifier ces 2)
                base["label"]   = saved_map[col["key"]].get("label",   col["label"])
                base["visible"] = saved_map[col["key"]].get("visible", col["visible"])
            merged.append(base)
        return merged

    except (json.JSONDecodeError, KeyError):
        return copy.deepcopy(DEFAULT_COLUMNS)


def save_columns(columns: list[dict]) -> None:
    """Sauvegarde la liste des colonnes dans settings.json."""
    data = {"columns": [{"key": c["key"], "label": c["label"], "visible": c["visible"]} for c in columns]}
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

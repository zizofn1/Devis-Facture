import os
import json

config_path = 'config.py'
with open(config_path, 'r', encoding='utf-8') as f:
    text = f.read()

if 'import json' not in text:
    text = 'import json\nimport os\n\n' + text

additions = '''
# ==========================================
# GESTION DES PARAMETRES (SETTINGS)
# ==========================================
SETTINGS_FILE = 'app_settings.json'

def load_settings():
    global DEVIS_VALIDITY_DAYS, DEFAULT_TVA
    if not os.path.exists(SETTINGS_FILE):
        return
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'COMPANY' in data:
            COMPANY.update(data['COMPANY'])
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
'''

if 'load_settings()' not in text:
    text += additions

with open(config_path, 'w', encoding='utf-8') as f:
    f.write(text)

print('config.py updated with settings functions.')

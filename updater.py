# ==========================================
# UPDATER.PY — Gestionnaire de mises à jour
# ==========================================

import os
import shutil
import urllib.request
import json
import zipfile
import tempfile
from logger import get_logger

logger = get_logger("updater")

def check_online(current_version, repo):
    """
    Vérifie la dernière release sur GitHub.
    Retourne un dict avec les infos, ou None si on est à jour.
    """
    res = get_latest_releases(repo, limit=1)
    if isinstance(res, list) and len(res) > 0:
        latest = res[0]
        try:
            curr = float(current_version)
            lat = float(latest["version"])
            if lat > curr:
                return latest
        except ValueError:
            if latest["version"] != current_version:
                return latest
    return None

def get_latest_releases(repo, limit=5):
    """
    Récupère les dernières releases de GitHub.
    """
    url = f"https://api.github.com/repos/{repo}/releases?per_page={limit}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            releases = []
            for item in data:
                releases.append({
                    "version": item.get("tag_name", "").lstrip("vV"),
                    "date": item.get("published_at", "")[:10], # YYYY-MM-DD
                    "changelog": item.get("body", "Aucune description."),
                    "zip_url": item.get("zipball_url")
                })
            return releases
    except Exception as e:
        logger.error(f"Erreur récupération releases: {e}")
        return f"Erreur de connexion : {e}"

def apply_update_from_zip(zip_url, dest_dir):
    """
    Télécharge, extrait et applique la mise à jour depuis un .zip de GitHub.
    """
    tmp_path = ""
    try:
        req = urllib.request.Request(zip_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                shutil.copyfileobj(response, tmp)
                tmp_path = tmp.name
        
        # Extraction
        with tempfile.TemporaryDirectory() as extract_dir:
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # GitHub enveloppe le code dans un dossier racine portant le nom du repo
            contents = os.listdir(extract_dir)
            if len(contents) == 1 and os.path.isdir(os.path.join(extract_dir, contents[0])):
                root_folder = os.path.join(extract_dir, contents[0])
            else:
                root_folder = extract_dir
                
            _copy_py_files(root_folder, dest_dir)
            
        os.remove(tmp_path)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour depuis ZIP: {e}")
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass
        return str(e)

def apply_update_from_folder(src_folder, dest_dir):
    """
    Met à jour l'application à partir d'un dossier local contenant le code source.
    """
    try:
        if not os.path.exists(os.path.join(src_folder, "main.py")):
            return "Le dossier sélectionné ne contient pas 'main.py' (source invalide)."
            
        _copy_py_files(src_folder, dest_dir)
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la copie depuis {src_folder}: {e}")
        return str(e)

def _copy_py_files(src, dst):
    """
    Écrase uniquement les fichiers Python critiques de l'application
    pour éviter de supprimer la DB (data.db) ou les backups/settings.
    """
    for file in os.listdir(src):
        # On ne copie que nos scripts et dépendances, on évite config.json ou data.db
        if file.endswith(".py") or file in ["requirements.txt"]:
            src_file = os.path.join(src, file)
            dst_file = os.path.join(dst, file)
            
            # Sauvegarder l'ancien fichier au cas où (optionnel, mais pratique)
            if os.path.exists(dst_file):
                backup_file = dst_file + ".bak"
                shutil.copy2(dst_file, backup_file)
                
            shutil.copy2(src_file, dst_file)

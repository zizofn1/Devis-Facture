# ==========================================
# UPDATER.PY — Gestionnaire de mises à jour
# ==========================================

import os
import ssl
import shutil
import urllib.request
import json
import zipfile
import tempfile
from logger import get_logger

logger = get_logger("updater")

# Contexte SSL permissif pour compatibilité Windows 7/8/10 avec des certificats anciens
def _ssl_ctx():
    try:
        return ssl._create_unverified_context()
    except AttributeError:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

def parse_version(v_str):
    """ Extraire uniquement les nombres séparés par des points (ex: 'v1.4.1' -> [1, 4, 1]). """
    try:
        return [int(x) for x in str(v_str).replace('v', '').replace('V', '').split('.') if x.strip().isdigit()]
    except Exception:
        return []

def check_online(current_version, repo):
    """
    Vérifie la dernière release sur GitHub.
    Retourne un dict avec les infos, ou None si on est à jour.
    """
    res = get_latest_releases(repo, limit=1)
    if isinstance(res, list) and len(res) > 0:
        latest = res[0]
        try:
            curr = parse_version(current_version)
            lat = parse_version(latest["version"])
            
            # Python compare automatiquement les listes élément par élément
            if lat and curr and lat > curr:
                return latest
        except Exception as e:
            logger.error(f"Erreur parsing version: {e}")
            if str(latest.get("version", "")) != str(current_version):
                return latest
    return None

def get_latest_releases(repo, limit=5):
    """
    Récupère les dernières releases de GitHub.
    """
    url = f"https://api.github.com/repos/{repo}/releases?per_page={limit}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=_ssl_ctx()) as response:
            data = json.loads(response.read().decode())
            releases = []
            for item in data:
                exe_url = None
                for asset in item.get("assets", []):
                    if asset.get("name", "").endswith(".exe"):
                        exe_url = asset.get("browser_download_url")
                        break
                        
                releases.append({
                    "version": item.get("tag_name", "").lstrip("vV"),
                    "date": item.get("published_at", "")[:10], # YYYY-MM-DD
                    "changelog": item.get("body", "Aucune description."),
                    "zip_url": item.get("zipball_url"),
                    "exe_url": exe_url
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
            except Exception as rem_e:
                pass
        return str(e)

def apply_update_exe(exe_url):
    """
    Lance l'updater externe pour remplacer l'exécutable courant.
    """
    import sys
    import subprocess
    
    current_exe = sys.executable
    updater_exe = os.path.join(os.path.dirname(current_exe), "updater.exe")
    
    if not os.path.exists(updater_exe):
        # Fallback au cas où l'updater.exe est manquant (ex: dev mode)
        logger.error("updater.exe introuvable dans le dossier de l'application.")
        return "Erreur : le programme de mise à jour (updater.exe) est introuvable."

    try:
        # Lancer l'updater avec les arguments nécessaires
        # On passe le PID actuel pour que l'updater attende qu'on soit fermé
        cmd = [
            updater_exe,
            "--url", exe_url,
            "--dest", current_exe,
            "--pid", str(os.getpid())
        ]
        
        logger.info(f"Lancement de l'updater : {' '.join(cmd)}")
        subprocess.Popen(cmd, shell=False, creationflags=subprocess.DETACHED_PROCESS)
        return True
    except Exception as e:
        logger.error(f"Erreur lors du lancement de l'updater: {e}")
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
    Copie les fichiers Python dans des fichiers .new (contourne le lock Windows).
    Un script 'apply_update.bat' est créé pour finaliser la copie après fermeture de l'app.
    """
    pending = []
    
    for file in os.listdir(src):
        # Sécurité maximale : blocage explicite des fichiers de données
        if file.endswith(".db") or file.endswith(".json") or file.endswith(".sqlite"):
            continue
            
        # On valide les fichiers sources nécessaires
        if file.endswith(".py") or file in ["requirements.txt", "logo.png", "logo.ico"]:
            src_file = os.path.join(src, file)
            dst_file = os.path.join(dst, file)
            new_file = dst_file + ".new"
            
            try:
                shutil.copy2(src_file, new_file)
                pending.append((new_file, dst_file))
                logger.info(f"Fichier {file} prêt pour installation.")
            except Exception as e:
                logger.error(f"Échec de la copie de {file}: {e}")

    # Créer un script batch qui applique les renommages APRÈS fermeture de l'app
    if pending:
        bat_path = os.path.join(dst, "apply_update.bat")
        lines = ["@echo off", "timeout /t 2 /nobreak >nul"]
        for new_file, dst_file in pending:
            bak_file = dst_file + ".bak"
            lines.append(f'if exist "{dst_file}" copy /Y "{dst_file}" "{bak_file}" >nul')
            lines.append(f'move /Y "{new_file}" "{dst_file}" >nul')
        lines.append("del \"%~f0\"")  # auto-suppression du .bat
        with open(bat_path, "w") as f:
            f.write("\n".join(lines))
        
        # Lancer le script en arrière-plan (après fermeture de l'app)
        # Lancement natif Windows fiable
        import os
        os.startfile(bat_path)
        logger.info(f"Script apply_update.bat lancé ({len(pending)} fichiers à installer).")

import os
import sys
import ssl
import time
import shutil
import urllib.request
import argparse
import subprocess
import traceback
import tempfile


# Fix SSL pour Windows 10 avec certificats anciens
def _ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def log(msg):
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "updater_log.txt"), "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except:
        pass

def main():
    parser = argparse.ArgumentParser(description="Updater pour Devis-Facture F&Z")
    parser.add_argument("--url", required=True, help="URL de téléchargement du nouvel EXE")
    parser.add_argument("--dest", required=True, help="Chemin du fichier EXE à remplacer")
    parser.add_argument("--pid", type=int, help="PID de l'application à attendre")
    
    args = parser.parse_args()
    log(f"--- Démarrage mise à jour de l'application ---")
    log(f"Cible : {args.dest}")
    log(f"URL : {args.url}")
    
    # 1. Attendre que l'application principale soit fermée
    if args.pid:
        log(f"Attente de la fermeture de l'application (PID: {args.pid})...")
        while True:
            try:
                os.kill(args.pid, 0)
                time.sleep(1)
            except OSError:
                break
    else:
        time.sleep(3) # Attente par défaut
    
    # 2. Téléchargement de l'installateur externe
    tmp_dir = tempfile.gettempdir()
    setup_file = os.path.join(tmp_dir, "DevisFacture_Installer.exe")
    log(f"Téléchargement de l'installateur vers {setup_file}...")
    
    download_success = False
    try:
        req = urllib.request.Request(args.url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60, context=_ssl_ctx()) as response:
            with open(setup_file, 'wb') as f:
                shutil.copyfileobj(response, f)
        download_success = True
    except Exception as e:
        log(f"Erreur téléchargement : {e}")
        time.sleep(2)
        
    # 3. Lancer l'installateur (il s'occupe de remplacer tous les fichiers de l'app)
    if download_success:
        log(f"Lancement de l'installateur...")
        try:
            # /SP- désactive la confirmation initiale
            # /SILENT fait la mise à jour sans obliger de cliquer sur 'Suivant'
            # /CLOSEAPPLICATIONS force la libération des fichiers restants bloqués
            cmd = [setup_file, "/SP-", "/SILENT", "/CLOSEAPPLICATIONS"]
            subprocess.Popen(cmd, shell=False, creationflags=subprocess.DETACHED_PROCESS)
        except Exception as e:
            log(f"Erreur lors du lancement du setup: {e}")
            
    log("Fin de l'updater. L'installateur va prendre le relais.")
    time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"Crash critique: {traceback.format_exc()}")
        time.sleep(5)

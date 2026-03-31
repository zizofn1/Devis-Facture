import os
import sys
import time
import shutil
import urllib.request
import argparse
import subprocess
import traceback

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
    
    # 2. Téléchargement du nouveau fichier
    tmp_file = args.dest + ".tmp"
    log(f"Téléchargement du nouvel exécutable...")
    download_success = False
    try:
        req = urllib.request.Request(args.url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            with open(tmp_file, 'wb') as f:
                shutil.copyfileobj(response, f)
        download_success = True
    except Exception as e:
        log(f"Erreur téléchargement : {e}")
        time.sleep(2)
        
    # 3. Remplacement du fichier (avec retries) si le téléchargement a réussi
    replace_success = False
    if download_success:
        log(f"Remplacement des fichiers...")
        for i in range(5):
            try:
                if os.path.exists(args.dest):
                    os.remove(args.dest)
                os.rename(tmp_file, args.dest)
                replace_success = True
                log("Fichier remplacé avec succès.")
                break
            except Exception as e:
                log(f"Tentative {i+1} : Impossible de remplacer le fichier ({e}). Nouvel essai...")
                time.sleep(2)
                
        if not replace_success:
            log("ERREUR : Impossible de terminer la mise à jour du fichier.")
            # Nettoyage si on a raté le remplacement
            if os.path.exists(tmp_file):
                try: os.remove(tmp_file)
                except: pass

    # 4. Toujours redémarrer l'application (même si la mise à jour a échoué)
    log(f"Redémarrage de l'application...")
    try:
        if os.path.exists(args.dest):
            subprocess.Popen([args.dest], shell=False)
        else:
            log("Le fichier cible n'existe plus pour redémarrer !")
    except Exception as e:
        log(f"Erreur redémarrage : {e}")
        
    log("Fin de l'updater.")
    time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"Crash critique: {traceback.format_exc()}")
        time.sleep(5)

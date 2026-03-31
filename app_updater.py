import os
import sys
import time
import shutil
import urllib.request
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Updater pour Devis-Facture F&Z")
    parser.add_argument("--url", required=True, help="URL de téléchargement du nouvel EXE")
    parser.add_argument("--dest", required=True, help="Chemin du fichier EXE à remplacer")
    parser.add_argument("--pid", type=int, help="PID de l'application à attendre")
    
    args = parser.parse_args()
    
    print(f"--- Mise à jour de l'application ---")
    print(f"Cible : {args.dest}")
    
    # 1. Attendre que l'application principale soit fermée
    if args.pid:
        print(f"Attente de la fermeture de l'application (PID: {args.pid})...")
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
    print(f"Téléchargement du nouvel exécutable...")
    try:
        req = urllib.request.Request(args.url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as response:
            with open(tmp_file, 'wb') as f:
                shutil.copyfileobj(response, f)
    except Exception as e:
        print(f"Erreur téléchargement : {e}")
        time.sleep(5)
        sys.exit(1)
        
    # 3. Remplacement du fichier (avec retries)
    print(f"Remplacement des fichiers...")
    success = False
    for i in range(5):
        try:
            if os.path.exists(args.dest):
                os.remove(args.dest)
            os.rename(tmp_file, args.dest)
            success = True
            break
        except Exception as e:
            print(f"Tentative {i+1} : Impossible de remplacer le fichier ({e}). Nouvel essai...")
            time.sleep(2)
            
    if not success:
        print("ERREUR : Impossible de terminer la mise à jour.")
        time.sleep(5)
        sys.exit(1)
        
    # 4. Relancer l'application
    print(f"Redémarrage de l'application...")
    try:
        subprocess.Popen([args.dest], shell=False)
    except Exception as e:
        print(f"Erreur redémarrage : {e}")
        
    print("Mise à jour terminée avec succès.")
    time.sleep(1)
    # Le programme se ferme tout seul.

if __name__ == "__main__":
    main()

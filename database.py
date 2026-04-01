import sqlite3
import json
import os
import shutil
from datetime import datetime
from logger import get_logger
import config

logger = get_logger("database")

# Chemin vers la base de données
DB_PATH = os.path.join(config.get_data_dir(), "data.db")

def _get_connection():
    # check_same_thread=False is generally safe for SQLite in UI apps like this
    conn = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    # Use WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def _backup_db():
    if not os.path.exists(DB_PATH):
        return
    backup_dir = os.path.join(config.get_data_dir(), "backups")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    backup_path = os.path.join(backup_dir, f"data_backup_{datetime.now().strftime('%Y%m%d')}.db")
    if not os.path.exists(backup_path):
        try:
            shutil.copy2(DB_PATH, backup_path)
            # Retain only last 7 days of backups
            backups = sorted([f for f in os.listdir(backup_dir) if f.startswith("data_backup_")], reverse=True)
            for old in backups[7:]:
                os.remove(os.path.join(backup_dir, old))
            logger.info(f"Database backup created: {backup_path}")
        except Exception as e:
            logger.error(f"Database backup failed: {e}")

def init_db():
    """Initialise la base de données et crée la table documents si elle n'existe pas."""
    _backup_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_type TEXT NOT NULL,
            doc_num TEXT NOT NULL,
            doc_date TEXT NOT NULL,
            client_name TEXT NOT NULL,
            total_ht REAL NOT NULL,
            total_ttc REAL NOT NULL,
            is_auto_entrepreneur INTEGER DEFAULT 0,
            client_data_json TEXT NOT NULL,
            items_data_json TEXT NOT NULL,
            columns_json TEXT NOT NULL,
            totals_data_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Pour des recherches rapides
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_doc_type_num ON documents(doc_type, doc_num)')

    # Table Clients
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            ice TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_name ON clients(name)')

    # Table Sequences pour numérotation auto
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sequences (
            doc_type TEXT PRIMARY KEY,
            last_number INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('INSERT OR IGNORE INTO sequences (doc_type, last_number) VALUES ("devis", 0)')
    cursor.execute('INSERT OR IGNORE INTO sequences (doc_type, last_number) VALUES ("facture", 0)')

    conn.commit()
    conn.close()

def save_document(doc_type: str, doc_num: str, doc_date: str, client_name: str, 
                  total_ht: float, total_ttc: float, is_auto_entrepreneur: bool,
                  client_data: dict, items_data: list, columns: list, totals_data: dict) -> int:
    """
    Sauvegarde un document. Si un document avec le même type et le même numéro
    existe déjà, il le met à jour. Sinon, il crée une nouvelle entrée.
    """
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        
        # Sérialisation des objets riches en JSON
        client_json = json.dumps(client_data, ensure_ascii=False)
        items_json = json.dumps(items_data, ensure_ascii=False)
        columns_json = json.dumps(columns, ensure_ascii=False)
        totals_json = json.dumps(totals_data, ensure_ascii=False)
        is_auto = 1 if is_auto_entrepreneur else 0
        
        # Vérifier l'existence
        cursor.execute("SELECT id FROM documents WHERE doc_type = ? AND doc_num = ?", (doc_type, doc_num))
        row = cursor.fetchone()
        
        if row:
            doc_id = row[0]
            cursor.execute('''
                UPDATE documents SET 
                    doc_date = ?, client_name = ?, total_ht = ?, total_ttc = ?, 
                    is_auto_entrepreneur = ?, client_data_json = ?, items_data_json = ?, 
                    columns_json = ?, totals_data_json = ?
                WHERE id = ?
            ''', (doc_date, client_name, total_ht, total_ttc, is_auto, 
                  client_json, items_json, columns_json, totals_json, doc_id))
        else:
            cursor.execute('''
                INSERT INTO documents (
                    doc_type, doc_num, doc_date, client_name, total_ht, total_ttc, 
                    is_auto_entrepreneur, client_data_json, items_data_json, columns_json, totals_data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (doc_type, doc_num, doc_date, client_name, total_ht, total_ttc, is_auto,
                  client_json, items_json, columns_json, totals_json))
            doc_id = cursor.lastrowid
            # Update sequence within the same transaction to avoid locking
            cursor.execute("UPDATE sequences SET last_number = last_number + 1 WHERE doc_type = ?", (doc_type,))
            
        conn.commit()
        return doc_id
    finally:
        conn.close()

def get_all_documents(doc_type=None):
    """
    Récupère la liste des documents (métadonnées) pour l'affichage dans l'historique.
    Si doc_type est fourni (ex: "devis"), filtre par ce type.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    
    if doc_type:
        cursor.execute('''
            SELECT id, doc_type, doc_num, doc_date, client_name, total_ttc, is_auto_entrepreneur
            FROM documents WHERE doc_type = ? ORDER BY doc_date DESC, id DESC
        ''', (doc_type,))
    else:
        cursor.execute('''
            SELECT id, doc_type, doc_num, doc_date, client_name, total_ttc, is_auto_entrepreneur
            FROM documents ORDER BY doc_date DESC, id DESC
        ''')
        
    rows = cursor.fetchall()
    conn.close()
    
    # Retourner sous forme de liste de dictionnaires
    return [{
        "id": r[0],
        "doc_type": r[1],
        "doc_num": r[2],
        "doc_date": r[3],
        "client_name": r[4],
        "total_ttc": r[5],
        "is_auto_entrepreneur": bool(r[6])
    } for r in rows]

def get_document_by_id(doc_id: int) -> dict:
    """
    Récupère un document complet (avec ses données JSON désérialisées).
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT doc_type, is_auto_entrepreneur, client_data_json, items_data_json, columns_json, totals_data_json
        FROM documents WHERE id = ?
    ''', (doc_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    return {
        "doc_type": row[0],
        "is_auto_entrepreneur": bool(row[1]),
        "client_data": json.loads(row[2]),
        "items_data": json.loads(row[3]),
        "columns": json.loads(row[4]),
        "totals_data": json.loads(row[5])
    }

def delete_document(doc_id: int):
    """Supprime un document par son ID."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

# ==========================================
# CLIENTS
# ==========================================

def save_client(name: str, ice: str = "", address: str = "", phone: str = "", email: str = ""):
    """Enregistre ou met à jour un client (basé sur le nom)."""
    if not name or name.strip() == "" or name.strip() == "-":
        return
        
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM clients WHERE name = ?", (name.strip(),))
    row = cursor.fetchone()
    
    if row:
        cursor.execute('''
            UPDATE clients SET ice = ?, address = ?, phone = ?, email = ?
            WHERE id = ?
        ''', (ice, address, phone, email, row[0]))
    else:
        cursor.execute('''
            INSERT INTO clients (name, ice, address, phone, email)
            VALUES (?, ?, ?, ?, ?)
        ''', (name.strip(), ice, address, phone, email))
        
    conn.commit()
    conn.close()

def get_all_clients() -> list[dict]:
    """Récupère tous les clients."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, ice, address, phone, email FROM clients ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        "id": r[0], "name": r[1], "ice": r[2], 
        "address": r[3], "phone": r[4], "email": r[5]
    } for r in rows]

# ==========================================
# SEQUENCES
# ==========================================

def peek_next_sequence(doc_type: str) -> int:
    """Récupère le prochain numéro sans l'incrémenter."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_number FROM sequences WHERE doc_type = ?", (doc_type,))
    row = cursor.fetchone()
    conn.close()
    return (row[0] + 1) if row else 1

def consume_sequence(doc_type: str):
    """Incrémente la séquence pour le type donné."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sequences SET last_number = last_number + 1 WHERE doc_type = ?", (doc_type,))
    conn.commit()
    conn.close()

# Toujours initialiser la base lors de l'import
try:
    init_db()
except Exception as e:
    logger.error(f"Erreur init_db: {e}")
    print(f"Erreur init_db: {e}")

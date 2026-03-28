import sqlite3
import json
import os
from datetime import datetime

# Chemin vers la base de données
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

def _get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialise la base de données et crée la table documents si elle n'existe pas."""
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
        
    conn.commit()
    conn.close()
    return doc_id

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

# Toujours initialiser la base lors de l'import
try:
    init_db()
except Exception as e:
    print(f"Erreur init_db: {e}")

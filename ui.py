# -*- coding: utf-8 -*-
# ==========================================
# UI.PY — Interface graphique Tkinter
# ==========================================

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

import config
from config import COMPANY, DOC_TYPES, DEFAULT_COLUMNS
from config import save_settings, load_columns, save_columns
from pdf_generator import create_pdf
from numerotation import generate_number
import database
from tkinter import colorchooser
import csv


# ==========================================
# Utilitaires de formatage
# ==========================================

def _format_thousands(val):
    """Formate un nombre avec espace pour les milliers et 2 décimales."""
    try:
        return f"{float(val):,.2f}".replace(",", " ")
    except (ValueError, TypeError):
        return str(val)


# ==========================================
# Utilitaire : ouvrir un fichier (cross-platform)
# ==========================================

def _open_file(path: str):
    """Ouvre le fichier avec l'application par défaut, toutes plateformes."""
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')
    except Exception:
        pass  # Si ça échoue, on ignore — le PDF est quand même créé

# ==========================================
# Utilitaire : Tri de colonnes Treeview
# ==========================================

def _treeview_sort_column(tv, col, reverse):
    """Trie une colonne d'un Treeview lors d'un clic sur l'en-tête."""
    l = [(tv.set(k, col), k) for k in tv.get_children('')]
    
    try:
        def parse_val(v):
            v_clean = v.replace(" MAD", "").replace(" ", "").strip()
            # Gérer le format date jj/mm/aaaa
            if "/" in v_clean and len(v_clean) >= 10:
                parts = v_clean.split()[0].split("/")
                if len(parts) == 3:
                    return float(f"{parts[2]}{parts[1]}{parts[0]}")
            return float(v_clean)
        l.sort(key=lambda t: parse_val(t[0]), reverse=reverse)
    except ValueError:
        # Fallback au tri alphabétique (insensible à la casse)
        l.sort(key=lambda t: t[0].lower(), reverse=reverse)

    # Réorganiser les éléments
    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)

    # Inverser le tri pour le prochain clic
    tv.heading(col, command=lambda _col=col: _treeview_sort_column(tv, _col, not reverse))


# ==========================================
# Fenêtre : édition d'une ligne article
# ==========================================

class ArticleWindow(tk.Toplevel):
    """Popup pour ajouter ou modifier une ligne article."""

    def __init__(self, parent, columns, on_validate, initial=None):
        super().__init__(parent)
        self.title("Ajouter une ligne" if initial is None else "Modifier la ligne")
        self.resizable(False, False)
        self.grab_set()

        self._entries = {}
        # On affiche TOUTES les colonnes visibles sauf 'total' (calculé auto)
        editable = [c for c in columns if c["visible"] and c["key"] != "total"]

        for i, col in enumerate(editable):
            ttk.Label(self, text=f"{col['label']} :").grid(
                row=i, column=0, padx=12, pady=6, sticky="e")
            width = 38 if col["key"] == "desc" else 18
            e = ttk.Entry(self, width=width)
            if initial:
                e.insert(0, str(initial.get(col["key"], "")))
            e.grid(row=i, column=1, padx=12, pady=6, sticky="w")
            self._entries[col["key"]] = e

        def _valider():
            try:
                values = {}
                for col in editable:
                    raw = self._entries[col["key"]].get().strip().replace(",", ".")
                    if col["key"] in ("qte", "pu"):
                        values[col["key"]] = float(raw) if raw else 0.0
                    else:
                        values[col["key"]] = raw
                # Calcul automatique total = qte × pu (si les deux colonnes existent)
                qte = values.get("qte", 0.0)
                pu  = values.get("pu",  0.0)
                values["total"] = qte * pu
                on_validate(values)
                self.destroy()
            except ValueError:
                messagebox.showerror("Erreur",
                    "Quantité et Prix Unitaire doivent être des nombres.", parent=self)

        ttk.Button(self, text="✔  Valider", command=_valider).grid(
            row=len(editable), column=0, columnspan=2, pady=14)

        # Ajuster la hauteur dynamiquement
        self.update_idletasks()
        self.geometry(f"420x{max(200, len(editable) * 42 + 80)}")


# ==========================================
# Fenêtre : personnalisation d'une colonne
# ==========================================

class ColumnEditorWindow(tk.Toplevel):
    """
    Clic droit sur un en-tête → renommer, masquer/afficher une colonne.
    """

    def __init__(self, parent, col_index, columns, on_apply):
        super().__init__(parent)
        col = columns[col_index]
        self.title(f"Colonne « {col['label']} »")
        self.geometry("400x200")
        self.grab_set()
        self.resizable(False, False)

        ttk.Label(self, text="Nouveau nom :").grid(row=0, column=0, padx=12, pady=10, sticky="e")
        self._e_label = ttk.Entry(self, width=24)
        self._e_label.insert(0, col["label"])
        self._e_label.grid(row=0, column=1, padx=12, pady=10)

        self._visible_var = tk.BooleanVar(value=col["visible"])
        ttk.Checkbutton(self, text="Colonne visible", variable=self._visible_var).grid(
            row=1, column=0, columnspan=2, pady=4)

        def _apply():
            new_label   = self._e_label.get().strip() or col["label"]
            new_visible = self._visible_var.get()
            # 'desc' et 'total' sont obligatoires pour le PDF
            if col["key"] in ("desc", "total") and not new_visible:
                messagebox.showwarning("Attention",
                    f"La colonne « {col['label']} » est obligatoire pour le PDF.",
                    parent=self)
                return
            on_apply(col_index, new_label, new_visible)
            self.destroy()

        ttk.Button(self, text="Appliquer", command=_apply).grid(
            row=2, column=0, columnspan=2, pady=8)


# ==========================================
# Fenêtre : ajouter une nouvelle colonne
# ==========================================

class AddColumnWindow(tk.Toplevel):
    """
    Permet d'ajouter une colonne personnalisée au tableau.
    La clé interne est générée automatiquement depuis le label.
    """

    def __init__(self, parent, existing_keys: list[str], on_add):
        super().__init__(parent)
        self.title("Ajouter une colonne")
        self.geometry("400x290")
        self.grab_set()
        self.resizable(False, False)
        self._existing_keys = existing_keys
        self._on_add = on_add

        ttk.Label(self, text="Nom de la colonne :").grid(row=0, column=0, padx=12, pady=12, sticky="e")
        self._e_name = ttk.Entry(self, width=22)
        self._e_name.grid(row=0, column=1, padx=12, pady=12)

        ttk.Label(self, text="Largeur (px) :").grid(row=1, column=0, padx=12, pady=6, sticky="e")
        self._e_width = ttk.Entry(self, width=8)
        self._e_width.insert(0, "100")
        self._e_width.grid(row=1, column=1, padx=12, pady=6, sticky="w")

        self._numeric_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Valeur numérique (MAD)", variable=self._numeric_var).grid(
            row=2, column=0, columnspan=2, pady=6)

        ttk.Button(self, text="✔  Ajouter", command=self._confirm).grid(
            row=3, column=0, columnspan=2, pady=10)

    def _confirm(self):
        name = self._e_name.get().strip()
        if not name:
            messagebox.showwarning("Attention", "Entrez un nom de colonne.", parent=self)
            return

        # Générer une clé unique depuis le nom (lettres/chiffres/underscore)
        import re
        base_key = re.sub(r"[^a-z0-9_]", "_", name.lower())[:20]
        key = base_key
        n = 2
        while key in self._existing_keys:
            key = f"{base_key}_{n}"
            n += 1

        try:
            width = max(40, int(self._e_width.get()))
        except ValueError:
            width = 100

        new_col = {
            "key":     key,
            "label":   name,
            "width":   width,
            "pdf_mm":  round(width * 0.264583),   # px → mm approximatif
            "anchor":  "e" if self._numeric_var.get() else "w",
            "visible": True,
            "custom":  True,   # flag pour distinguer des colonnes système
        }
        self._on_add(new_col)
        self.destroy()


# ==========================================
# Onglet principal (Devis ou Facture)
# ==========================================

class DocumentTab(ttk.Frame):
    """Un onglet = un type de document (devis ou facture)."""

    def __init__(self, parent, doc_type: str, columns: list[dict]):
        super().__init__(parent)
        self.doc_type = doc_type
        self.columns  = columns          # référence partagée entre les 2 onglets
        self._doc_cfg = DOC_TYPES[doc_type]
        # Cache interne : valeurs brutes des lignes (toujours toutes les clés)
        self._rows_cache: list[dict] = []

        self._build_top_frame()
        self._build_items_frame()
        self._build_bottom_bar()

        # Ligne d'exemple au démarrage
        self._rows_cache = [{
            "ref": "M-01", "desc": "Fabrication dressing sur mesure chêne",
            "qte": 1.0, "pu": 12500.0, "total": 12500.0
        }]
        self._refresh_tree()
        self.update_totals()

    # ── Construction ──────────────────────────────────────────────

    def _build_top_frame(self):
        lbl   = self._doc_cfg["label"]
        frame = ttk.LabelFrame(self, text=f"Informations {lbl} & Client")
        frame.pack(fill="x", padx=6, pady=6)

        default_num = generate_number(self.doc_type, "")
        left_fields = [
            (f"N° {lbl} :", "entry_num",   default_num),
            ("Date :",       "entry_date",  datetime.now().strftime("%d/%m/%Y")),
            ("Tél :",        "entry_phone", ""),
        ]
        for row, (label, attr, default) in enumerate(left_fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, padx=5, pady=5, sticky="e")
            e = ttk.Entry(frame)
            e.insert(0, default)
            e.grid(row=row, column=1, padx=5, pady=5)
            setattr(self, attr, e)

        ttk.Label(frame, text="Nom Client :").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.entry_client = ttk.Combobox(frame, width=28)
        self.entry_client.grid(row=0, column=3, padx=5, pady=5)
        
        right_fields = [
            ("ICE Client :", "entry_ice",     ""),
            ("Adresse :",    "entry_address", ""),
        ]
        for row, (label, attr, default) in enumerate(right_fields, start=1):
            ttk.Label(frame, text=label).grid(row=row, column=2, padx=5, pady=5, sticky="e")
            e = ttk.Entry(frame, width=30)
            e.insert(0, default)
            e.grid(row=row, column=3, padx=5, pady=5)
            setattr(self, attr, e)
            
        # Hook for autocompletion
        self._all_clients = database.get_all_clients()
        self.entry_client['values'] = [c["name"] for c in self._all_clients]
        
        def on_client_select(event):
            name = self.entry_client.get()
            for c in self._all_clients:
                if c["name"] == name:
                    self.entry_ice.delete(0, tk.END); self.entry_ice.insert(0, c["ice"] or "")
                    self.entry_address.delete(0, tk.END); self.entry_address.insert(0, c["address"] or "")
                    
                    if hasattr(self, "entry_phone"):
                        self.entry_phone.delete(0, tk.END)
                        self.entry_phone.insert(0, c["phone"] or "")
                    
                    self._regen_number()
                    break
                    
        self.entry_client.bind("<<ComboboxSelected>>", on_client_select)
        self.entry_client.bind("<KeyRelease>", lambda _: self._regen_number())

        ttk.Button(frame, text="🔄 Générer N°",
                   command=self._regen_number).grid(row=0, column=4, padx=8)
        self.entry_client.bind("<FocusOut>", lambda _: self._regen_number())

    def _build_items_frame(self):
        self._items_frame = ttk.LabelFrame(self, text="Articles / Prestations")
        self._items_frame.pack(fill="both", expand=True, padx=6, pady=6)

        self._build_treeview()

        btn_frame = ttk.Frame(self._items_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="+ Ajouter",    command=self._add_row).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="✎ Modifier",    command=self._edit_row).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="✕ Supprimer",   command=self._delete_row).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="↑ Monter",      command=self._move_up).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="↓ Descendre",   command=self._move_down).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="⧉ Dupliquer",   command=self._duplicate_row).pack(side="left", padx=2)
        ttk.Separator(btn_frame, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(btn_frame, text="⊞ Colonne", command=self._add_column).pack(side="left", padx=2)

        # Zone Droite : TVA et Remise
        options_frame = ttk.Frame(self._items_frame)
        options_frame.pack(fill="x", padx=5, pady=2, anchor="e")
        
        ttk.Label(options_frame, text="Remise (MAD) :").pack(side="right", padx=(10, 2))
        self.entry_remise = ttk.Entry(options_frame, width=8)
        self.entry_remise.insert(0, "0.00")
        self.entry_remise.pack(side="right")
        self.entry_remise.bind("<KeyRelease>", lambda _: self.update_totals())

        ttk.Label(options_frame, text="TVA (%) :").pack(side="right", padx=(20, 2))
        self.entry_tva = ttk.Entry(options_frame, width=5)
        self.entry_tva.insert(0, str(config.DEFAULT_TVA))
        self.entry_tva.pack(side="right")
        self.entry_tva.bind("<KeyRelease>", lambda _: self.update_totals())

        self.var_auto_entrepreneur = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame, text="Exonéré de TVA (0%)", 
            variable=self.var_auto_entrepreneur, 
            command=self._toggle_auto
        ).pack(side="right", padx=(15, 4))

    def _toggle_auto(self):
        if self.var_auto_entrepreneur.get():
            self.entry_tva.delete(0, tk.END)
            self.entry_tva.insert(0, "0")
            self.entry_tva.config(state="disabled")
        else:
            self.entry_tva.config(state="normal")
            self.entry_tva.delete(0, tk.END)
            self.entry_tva.insert(0, str(config.DEFAULT_TVA))
        self.update_totals()

    def _build_treeview(self):
        """(Re)construit le Treeview à partir de self.columns (colonnes visibles)."""
        # Détruire l'ancien treeview si existant
        for w in ("tree", "_tree_scroll"):
            if hasattr(self, w):
                getattr(self, w).destroy()

        visible    = [c for c in self.columns if c["visible"]]
        col_keys   = [c["key"] for c in visible]

        self.tree = ttk.Treeview(
            self._items_frame, columns=col_keys, show="headings", height=8)

        for col in visible:
            self.tree.heading(col["key"], text=col["label"])
            self.tree.column(col["key"], width=col["width"], anchor=col["anchor"])

        self.tree.bind("<Button-3>",  self._on_header_right_click)
        self.tree.bind("<Double-1>",  lambda _: self._edit_row())

        self._tree_scroll = ttk.Scrollbar(
            self._items_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self._tree_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self._tree_scroll.pack(side="right", fill="y", pady=5)

    def _build_bottom_bar(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=6, pady=12)

        self.lbl_totals = ttk.Label(
            frame,
            text="Total HT : 0.00 MAD  |  TVA : 0.00 MAD  |  TTC : 0.00 MAD",
            font=("Helvetica", 11, "bold"),
        )
        self.lbl_totals.pack(side="left", padx=5)

        lbl = self._doc_cfg["label"]
        ttk.Button(
            frame, text="💾 Enregistrer",
            command=self.save_to_db
        ).pack(side="right", padx=10, ipadx=10, ipady=8)

        ttk.Button(
            frame, text=f"📄  GÉNÉRER LA {lbl}",
            command=self.generate
        ).pack(side="right", ipadx=10, ipady=8)

    def save_to_db(self, show_msg=True):
        num_doc = self.entry_num.get().strip()
        if not num_doc or num_doc == "XXX":
            messagebox.showwarning("Attention", "Veuillez générer ou saisir un numéro de document valide.")
            return False

        client_data = {
            "num":     num_doc,
            "date":    self.entry_date.get()    or "-",
            "name":    self.entry_client.get()  or "-",
            "ice":     self.entry_ice.get()     or "-",
            "address": self.entry_address.get() or "-",
            "phone":   self.entry_phone.get()   or "-",
        }
        
        # Validation
        if client_data["name"] == "-" or client_data["name"] == "":
            if show_msg: messagebox.showwarning("Attention", "Le Nom du Client est obligatoire.")
            return False

        if not self._rows_cache:
            if show_msg: messagebox.showwarning("Attention", "Ajoutez au moins un article.")
            return False
            
        # Sauvegarde client en base
        database.save_client(client_data["name"], client_data["ice"], client_data["address"], client_data["phone"], "")
        
        # Rafraichir la liste locale des clients
        self._all_clients = database.get_all_clients()
        self.entry_client['values'] = [c["name"] for c in self._all_clients]

        items_data = []
        for row in self._rows_cache:
            item = dict(row)
            for k in ("qte", "pu", "total"):
                try:
                    item[k] = float(str(item.get(k, 0)).replace(" ", "").replace(",", "."))
                except (ValueError, TypeError):
                    item[k] = 0.0
            items_data.append(item)
            
        ht, tva_pct, tva_val, ttc, remise = self.update_totals()
        totals_data = {"ht": ht, "tva_percent": tva_pct, "tva_val": tva_val, "ttc": ttc, "remise": remise, "ht_net": ht - remise}
        is_auto = getattr(self, 'var_auto_entrepreneur', None)
        is_auto_val = is_auto.get() if is_auto else False
        
        try:
            database.save_document(
                doc_type=self.doc_type,
                doc_num=client_data["num"],
                doc_date=client_data["date"],
                client_name=client_data["name"],
                total_ht=ht,
                total_ttc=ttc,
                is_auto_entrepreneur=is_auto_val,
                client_data=client_data,
                items_data=items_data,
                columns=self.columns,
                totals_data=totals_data
            )
            if show_msg: messagebox.showinfo("Succès", "Document enregistré dans l'historique.")
            return True
        except Exception as e:
            if show_msg: messagebox.showerror("Erreur Base de Données", f"Impossible d'enregistrer :\n{e}")
            return False

    # ── Cache ↔ Treeview ──────────────────────────────────────────

    def _cache_to_tree_values(self, row: dict) -> tuple:
        """
        Convertit un dict (cache) en tuple pour le Treeview
        selon les colonnes VISIBLES actuelles.
        """
        visible = [c for c in self.columns if c["visible"]]
        result  = []
        for col in visible:
            val = row.get(col["key"], "")
            if col["key"] in ("pu", "total") and val != "":
                val = _format_thousands(val)
            result.append(val)
        return tuple(result)

    def _tree_values_to_cache(self, values: tuple) -> dict:
        """
        Convertit un tuple Treeview en dict (cache) selon les colonnes VISIBLES.
        """
        visible = [c for c in self.columns if c["visible"]]
        return {col["key"]: values[i] for i, col in enumerate(visible) if i < len(values)}

    def _refresh_tree(self):
        """
        Reconstruit le Treeview et réinsère toutes les lignes depuis _rows_cache.
        Appelé après tout changement de structure des colonnes.
        """
        self._build_treeview()
        for row in self._rows_cache:
            self.tree.insert("", "end", values=self._cache_to_tree_values(row))

    # ── Numérotation ─────────────────────────────────────────────

    def _regen_number(self):
        new_num = generate_number(self.doc_type, self.entry_client.get())
        self.entry_num.delete(0, tk.END)
        self.entry_num.insert(0, new_num)

    # ── Actions sur les lignes ────────────────────────────────────

    def _add_row(self):
        def on_validate(d):
            self._rows_cache.append(d)
            self.tree.insert("", "end", values=self._cache_to_tree_values(d))
            self.update_totals()
        ArticleWindow(self, self.columns, on_validate=on_validate)

    def _edit_row(self):
        sel = self.tree.selection()
        if not sel:
            return
        item     = sel[0]
        tree_idx = self.tree.get_children().index(item)
        current  = self._rows_cache[tree_idx]

        def apply(d):
            self._rows_cache[tree_idx] = d
            self.tree.item(item, values=self._cache_to_tree_values(d))
            self.update_totals()

        ArticleWindow(self, self.columns, on_validate=apply, initial=current)

    def _delete_row(self):
        for item in self.tree.selection():
            idx = self.tree.get_children().index(item)
            self._rows_cache.pop(idx)
            self.tree.delete(item)
        self.update_totals()

    def _move_up(self):
        selected = self.tree.selection()
        if not selected: return
        for item in selected:
            idx = self.tree.index(item)
            if idx > 0:
                self.tree.move(item, self.tree.parent(item), idx - 1)
                self._rows_cache[idx], self._rows_cache[idx-1] = self._rows_cache[idx-1], self._rows_cache[idx]

    def _move_down(self):
        selected = reversed(self.tree.selection())
        for item in selected:
            idx = self.tree.index(item)
            if idx < len(self.tree.get_children()) - 1:
                self.tree.move(item, self.tree.parent(item), idx + 1)
                self._rows_cache[idx], self._rows_cache[idx+1] = self._rows_cache[idx+1], self._rows_cache[idx]

    def _duplicate_row(self):
        selected = self.tree.selection()
        if not selected: return
        idx = self.tree.index(selected[0])
        item_copy = dict(self._rows_cache[idx])
        self._rows_cache.insert(idx + 1, item_copy)
        self._refresh_tree()
        self.update_totals()

    # ── Colonnes : clic droit ──────────────────────────────────────

    def _on_header_right_click(self, event):
        if self.tree.identify_region(event.x, event.y) != "heading":
            return
        col_id          = self.tree.identify_column(event.x)   # "#1", "#2", ...
        col_idx_visible = int(col_id.replace("#", "")) - 1
        visible_indices = [i for i, c in enumerate(self.columns) if c["visible"]]
        if col_idx_visible >= len(visible_indices):
            return
        global_idx = visible_indices[col_idx_visible]

        def on_apply(g_idx, new_label, new_visible):
            self.columns[g_idx]["label"]   = new_label
            self.columns[g_idx]["visible"] = new_visible
            save_columns(self.columns)
            self._refresh_tree()   # ← reconstruit APRÈS avoir mis à jour columns
            self.update_totals()

        ColumnEditorWindow(self, global_idx, self.columns, on_apply)

    # ── Colonnes : ajouter ────────────────────────────────────────

    def _add_column(self):
        existing_keys = [c["key"] for c in self.columns]

        def on_add(new_col):
            self.columns.append(new_col)
            save_columns(self.columns)
            self._refresh_tree()
            self.update_totals()

        AddColumnWindow(self, existing_keys, on_add)

    # ── Totaux ────────────────────────────────────────────────────

    def update_totals(self):
        """
        Calcule HT depuis _rows_cache. Applique la remise globale puis calcule TVA.
        """
        ht = sum(
            float(str(row.get("total", 0)).replace(" ", "").replace(",", ".") or 0)
            for row in self._rows_cache
        )
        try:
            remise = float(str(self.entry_remise.get()).replace(" ", "").replace(",", ".") or 0)
        except ValueError:
            remise = 0.0
            
        ht_net = max(0.0, ht - remise)

        try:
            if hasattr(self, 'var_auto_entrepreneur') and self.var_auto_entrepreneur.get():
                tva_pct = 0.0
            else:
                tva_pct = float(str(self.entry_tva.get()).replace(",", ".") or 0)
        except ValueError:
            tva_pct = float(config.DEFAULT_TVA)

        tva_val = ht_net * (tva_pct / 100)
        ttc     = ht_net + tva_val
        self.lbl_totals.config(
            text=(f"Total HT : {_format_thousands(ht)} MAD  |  Remise : {_format_thousands(remise)} MAD  |  TVA : {_format_thousands(tva_val)} MAD  |  TTC : {_format_thousands(ttc)} MAD")
        )
        return ht, tva_pct, tva_val, ttc, remise

    # ── Génération PDF ────────────────────────────────────────────

    def generate(self):
        num_doc = self.entry_num.get().strip()
        if not num_doc or num_doc == "XXX":
            messagebox.showwarning("Attention", "Veuillez générer ou saisir un numéro de document valide.")
            return
            
        client_data = {
            "num":     num_doc,
            "date":    self.entry_date.get()    or "-",
            "name":    self.entry_client.get()  or "-",
            "ice":     self.entry_ice.get()     or "-",
            "address": self.entry_address.get() or "-",
            "phone":   self.entry_phone.get()   or "-",
        }

        if not self._rows_cache:
            messagebox.showwarning("Attention", "Ajoutez au moins un article.")
            return

        # Construire items_data depuis le cache (toutes les clés disponibles)
        items_data = []
        for row in self._rows_cache:
            item = dict(row)
            for k in ("qte", "pu", "total"):
                try:
                    item[k] = float(str(item.get(k, 0)).replace(" ", "").replace(",", "."))
                except (ValueError, TypeError):
                    item[k] = 0.0
            items_data.append(item)

        ht, tva_pct, tva_val, ttc, remise = self.update_totals()
        totals_data = {"ht": ht, "tva_percent": tva_pct, "tva_val": tva_val, "ttc": ttc, "remise": remise, "ht_net": ht - remise}
        is_auto = getattr(self, 'var_auto_entrepreneur', None)
        is_auto_val = is_auto.get() if is_auto else False

        lbl = self._doc_cfg["label"]
        # Nom de fichier sécurisé (retire les caractères interdits)
        safe_num = "".join(c for c in client_data["num"] if c not in r'\/:*?"<>|')
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"{lbl}_{safe_num}.pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not filename:
            return

        # Sauvegarder dans la DB avant de générer
        self.save_to_db(show_msg=False)

        # ── Génération + ouverture séparées du try/except ──
        try:
            create_pdf(filename, client_data, items_data, totals_data,
                       doc_type=self.doc_type, columns=self.columns,
                       is_auto_entrepreneur=is_auto_val)
        except Exception as exc:
            messagebox.showerror("Erreur de génération PDF",
                                 f"Une erreur s'est produite :\n{exc}")
            return

        # PDF créé avec succès → on informe, puis on essaie d'ouvrir
        messagebox.showinfo("Succès", f"{lbl} générée avec succès !\n\n{filename}")
        _open_file(filename)   # cross-platform, erreur ignorée silencieusement


# ==========================================

# ==========================================
# Fenêtre : Paramètres (Settings)
# ==========================================
class SettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("⚙ Paramètres de l'application")
        self.geometry("600x650")
        self.grab_set()
        self.resizable(False, False)

        try:
            icon_path = config.resource_path("logo.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            from logger import get_logger
            get_logger("ui").warning(f"Impossible de charger le logo: {e}")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Tab 1: Informations Entreprise ──
        tab_company = ttk.Frame(notebook)
        notebook.add(tab_company, text="  Informations Entreprise  ")
        
        self.comp_entries = {}
        comp_fields = [
            ("Nom d'Entreprise", "name"), ("Slogan", "slogan"), ("Dirigeant", "manager"),
            ("Adresse", "address"), ("Ville", "city"), ("Téléphone", "phone"),
            ("Email", "email"), ("RC", "rc"), ("Patente", "patente"),
            ("Num. IF", "if_num"), ("ICE", "ice"),
            ("Banque", "rib_bank"), ("RIB", "rib")
        ]
        
        for i, (label, key) in enumerate(comp_fields):
            ttk.Label(tab_company, text=label + " :").grid(row=i, column=0, padx=10, pady=6, sticky="e")
            e = ttk.Entry(tab_company, width=45)
            e.insert(0, config.COMPANY.get(key, ""))
            e.grid(row=i, column=1, padx=10, pady=6, sticky="w")
            self.comp_entries[key] = e

        # ── Tab 2: Devis & Factures ──
        tab_docs = ttk.Frame(notebook)
        notebook.add(tab_docs, text="  Devis & Factures  ")
        
        ttk.Label(tab_docs, text="TVA par défaut (%) :").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.e_tva = ttk.Entry(tab_docs, width=15)
        self.e_tva.insert(0, str(config.DEFAULT_TVA))
        self.e_tva.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(tab_docs, text="Validité Devis (Jours) :").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.e_valid = ttk.Entry(tab_docs, width=15)
        self.e_valid.insert(0, str(config.DEVIS_VALIDITY_DAYS))
        self.e_valid.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(tab_docs, text="Conditions Devis :").grid(row=2, column=0, padx=10, pady=10, sticky="ne")
        self.t_cond_devis = tk.Text(tab_docs, width=45, height=5, font=("Helvetica", 9))
        self.t_cond_devis.insert("1.0", "\n".join(config.DOC_TYPES["devis"].get("conditions", [])))
        self.t_cond_devis.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        ttk.Label(tab_docs, text="Conditions Facture :").grid(row=3, column=0, padx=10, pady=10, sticky="ne")
        self.t_cond_fac = tk.Text(tab_docs, width=45, height=5, font=("Helvetica", 9))
        self.t_cond_fac.insert("1.0", "\n".join(config.DOC_TYPES["facture"].get("conditions", [])))
        self.t_cond_fac.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # ── Tab 3: Apparence (Couleurs) ──
        tab_colors = ttk.Frame(notebook)
        notebook.add(tab_colors, text="  Apparence  ")
        
        self.color_vars = {
            "primary": tk.StringVar(value=config.COLORS.get("primary", "#9a7f85")),
            "dark": tk.StringVar(value=config.COLORS.get("dark", "#1e293b"))
        }
        
        def _pick_color(key):
            currentColor = self.color_vars[key].get()
            color = colorchooser.askcolor(title="Choisir une couleur", initialcolor=currentColor)[1]
            if color:
                self.color_vars[key].set(color)
                # Mettre à jour l'aperçu du bouton
                self.color_btns[key].config(bg=color)
                
        self.color_btns = {}
        for i, (label, key) in enumerate([("Couleur Principale", "primary"), ("Couleur Sombre", "dark")]):
            ttk.Label(tab_colors, text=label + " :").grid(row=i, column=0, padx=10, pady=15, sticky="e")
            
            # Bouton coloré d'aperçu
            current_hex = self.color_vars[key].get()
            btn = tk.Button(tab_colors, width=15, bg=current_hex, command=lambda k=key: _pick_color(k))
            btn.grid(row=i, column=1, padx=10, pady=15, sticky="w")
            self.color_btns[key] = btn

        # ── Bottom Bar ──
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Annuler", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="💾 Enregistrer", command=self.save).pack(side="right", padx=5)

    def save(self):
        # Update Company
        for k, e in self.comp_entries.items():
            config.COMPANY[k] = e.get().strip()
        
        # Update TVA and Validity
        try:
            config.DEFAULT_TVA = int(self.e_tva.get().strip())
        except ValueError:
            pass
        try:
            config.DEVIS_VALIDITY_DAYS = int(self.e_valid.get().strip())
            config.DOC_TYPES["devis"]["validity_line"] = f"Validité : {config.DEVIS_VALIDITY_DAYS} Jours"
        except ValueError:
            pass
            
        # Update conditions
        c_devis = [c.strip() for c in self.t_cond_devis.get("1.0", "end-1c").split("\n") if c.strip()]
        c_fac = [c.strip() for c in self.t_cond_fac.get("1.0", "end-1c").split("\n") if c.strip()]
        
        config.DOC_TYPES["devis"]["conditions"] = c_devis
        config.DOC_TYPES["facture"]["conditions"] = c_fac
        
        # Update colors
        for key, var in self.color_vars.items():
            config.COLORS[key] = var.get()
        
        # Persist and close
        config.save_settings()
        from tkinter import messagebox
        messagebox.showinfo("Succès", "Paramètres mis à jour avec succès !", parent=self)
        self.destroy()

# ==========================================
# Fenêtre : Guide d'utilisation et Aide
# ==========================================
class HelpWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("📖 Guide d'utilisation & FAQ")
        self.geometry("650x550")
        self.grab_set()

        try:
            icon_path = config.resource_path("logo.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            from logger import get_logger
            get_logger("ui").warning(f"Impossible de charger le logo: {e}")
        
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        guides = {
            "Nouveautés V3.3": (
                "🚀 Version 3.3 — Améliorations :\n\n"
                "- Rollback & Historique : Vous pouvez consulter les anciennes versions et revenir en arrière.\n\n"
                "- Numérotation Intelligente : Plus besoin de cliquer sur [Générer N°]. Le numéro se met à jour en temps réel dès que vous tapez le nom du client.\n\n"
                "- Carnet Client Automatique : Les clients sont enregistrés dès que vous générez un document.\n\n"
                "- Conversion Devis ➔ Facture : Disponible dans l'Historique via le bouton dédié.\n\n"
                "- Sécurité MAX : Sauvegarde automatique de la base de données (Fichier data.db) tous les jours."
            ),
            "Articles & Calculs": (
                "- Utiliser le bouton [+ Ajouter] pour insérer un produit/service.\n\n"
                "- [Double-Clic] sur n'importe quelle ligne pour modifier ses quantités ou son prix.\n\n"
                "- Boutons ↑ / ↓ : Pour réorganiser l'ordre des articles sur le PDF.\n\n"
                "- Bouton ⧉ Dupliquer : Pour copier rapidement une ligne existante."
            ),
            "Numérotation": (
                "- Le numéro est auto-généré au format : PREFIX-YYMMDD-Initiales-Séquence.\n\n"
                "- Les initiales sont extraites automatiquement de 'Prénom Nom' (ex: Zouhair Belkadi -> ZB).\n\n"
                "- Tapez simplement le nom, le numéro s'adapte tout seul."
            ),
            "Génération PDF": (
                "- Cliquez sur [📄 GÉNÉRER...] en bas à droite.\n\n"
                "- Le montant en lettres est ajouté automatiquement en bas du document.\n\n"
                "- Le PDF s'ouvrira immédiatement après l'enregistrement."
            ),
            "FAQ & Problèmes": (
                "❓ Problème : Le devis n'est pas enregistré lorsque je ferme l'application ?\n"
                "💡 Solution : L'application n'enregistre pas automatiquement les anciens devis, elle vous permet de générer des PDF. Assurez-vous d'avoir enregistré le PDF final sur votre ordinateur.\n\n"
                
                "❓ Problème : Mon logo d'entreprise ne s'affiche pas sur le PDF !\n"
                "💡 Solution : Placez une image nommée 'logo.png' dans le même dossier que l'application, sinon le logiciel le désactivera automatiquement pour éviter un crash.\n\n"
                
                "❓ Problème : J'ai modifié les Paramètres mais rien n'a changé sur mon PDF.\n"
                "💡 Solution : Êtes-vous sûr d'avoir cliqué sur [💾 Enregistrer] à l'intérieur de la fenêtre Paramètres ? Sinon, vos modifications seront ignorées."
            )
        }
        
        for title, text in guides.items():
            frame = ttk.Frame(notebook, padding=10)
            notebook.add(frame, text=f" {title} ")
            
            txt = tk.Text(frame, wrap="word", font=("Helvetica", 10), bg=self.cget('bg'), relief="flat")
            txt.insert("1.0", text)
            txt.config(state="disabled") # Lecture seule
            txt.pack(fill="both", expand=True)
            
        ttk.Button(self, text="Fermer l'aide", command=self.destroy).pack(pady=10)


# ==========================================
# Fenêtre : Clients
# ==========================================

class ClientsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        top_bar = ttk.Frame(self)
        top_bar.pack(fill="x", padx=10, pady=(10, 5))
        ttk.Button(top_bar, text="🔄 Actualiser", command=self.refresh).pack(side="left", padx=5)
        
        self.tree = ttk.Treeview(self, columns=("name", "ice", "address", "phone", "email"), show="headings")
        for c, t in [("name", "Nom Client"), ("ice", "ICE"), ("address", "Adresse"), ("phone", "Téléphone"), ("email", "Email")]:
            self.tree.heading(c, text=t, command=lambda _c=c: _treeview_sort_column(self.tree, _c, False))
        
        self.tree.column("name", width=150)
        self.tree.column("ice", width=120)
        self.tree.column("address", width=200)
        self.tree.column("phone", width=100)
        self.tree.column("email", width=150)
        
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10), side="left")
        scroll.pack(fill="y", side="right", padx=(0,10), pady=(0, 10))
        self.refresh()
        
    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        clients = database.get_all_clients()
        for c in clients:
            self.tree.insert("", "end", values=(c["name"], c["ice"], c["address"], c["phone"], c["email"]))

# ==========================================
# Fenêtre : Historique
# ==========================================
class HistoryTab(ttk.Frame):
    def __init__(self, parent, on_open_doc):
        super().__init__(parent)
        self.on_open_doc = on_open_doc
        
        top_bar = ttk.Frame(self)
        top_bar.pack(fill="x", padx=10, pady=(10, 5))
        
        ttk.Button(top_bar, text="🔄 Actualiser", command=self.refresh).pack(side="left", padx=5)
        ttk.Button(top_bar, text="📂 Ouvrir", command=self.open_selected).pack(side="left", padx=5)
        ttk.Button(top_bar, text="✕ Supprimer", command=self.delete_selected).pack(side="left", padx=5)
        ttk.Button(top_bar, text="📝 Convertir en Facture", command=self.convert_to_invoice).pack(side="left", padx=5)
        ttk.Button(top_bar, text="📊 Exporter Excel", command=self.export_to_excel).pack(side="left", padx=5)
        
        filter_bar = ttk.LabelFrame(self, text="Filtres de recherche")
        filter_bar.pack(fill="x", padx=10, pady=(0, 10))
        
        # Type
        ttk.Label(filter_bar, text="Type :").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.filter_type_var = tk.StringVar(value="Tous")
        cb_type = ttk.Combobox(filter_bar, textvariable=self.filter_type_var, values=["Tous", "Devis", "Facture"], state="readonly", width=10)
        cb_type.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        cb_type.bind("<<ComboboxSelected>>", lambda _: self.refresh())
        
        # Date
        ttk.Label(filter_bar, text="Date :").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.filter_date_var = tk.StringVar()
        ent_date = ttk.Entry(filter_bar, textvariable=self.filter_date_var, width=15)
        ent_date.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        ent_date.bind("<KeyRelease>", lambda _: self.refresh())
        
        # Recherche globale (Client, Numéro)
        ttk.Label(filter_bar, text="Nom Client / N° :").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.filter_search_var = tk.StringVar()
        ent_search = ttk.Entry(filter_bar, textvariable=self.filter_search_var, width=25)
        ent_search.grid(row=0, column=5, padx=5, pady=5, sticky="w")
        ent_search.bind("<KeyRelease>", lambda _: self.refresh())

        # ID
        ttk.Label(filter_bar, text="ID (base) :").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.filter_id_var = tk.StringVar()
        ent_id = ttk.Entry(filter_bar, textvariable=self.filter_id_var, width=10)
        ent_id.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ent_id.bind("<KeyRelease>", lambda _: self.refresh())

        # Montant Min
        ttk.Label(filter_bar, text="Montant Min :").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.filter_min_var = tk.StringVar()
        ent_min = ttk.Entry(filter_bar, textvariable=self.filter_min_var, width=15)
        ent_min.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        ent_min.bind("<KeyRelease>", lambda _: self.refresh())

        # Montant Max
        ttk.Label(filter_bar, text="Montant Max :").grid(row=1, column=4, padx=5, pady=5, sticky="e")
        self.filter_max_var = tk.StringVar()
        ent_max = ttk.Entry(filter_bar, textvariable=self.filter_max_var, width=15)
        ent_max.grid(row=1, column=5, padx=5, pady=5, sticky="w")
        ent_max.bind("<KeyRelease>", lambda _: self.refresh())
        
        columns = ("id", "type", "num", "date", "client", "ttc")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        
        for c, t in [("id", "ID"), ("type", "Type"), ("num", "N° Document"), ("date", "Date"), ("client", "Client"), ("ttc", "Montant TTC")]:
            self.tree.heading(c, text=t, command=lambda _c=c: _treeview_sort_column(self.tree, _c, False))
        
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("type", width=100, anchor="center")
        self.tree.column("num", width=120, anchor="center")
        self.tree.column("date", width=100, anchor="center")
        self.tree.column("client", width=250, anchor="w")
        self.tree.column("ttc", width=120, anchor="e")
        
        self.tree.bind("<Double-1>", lambda _: self.open_selected())
        
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 10))
        scroll.pack(side="right", fill="y", padx=(0, 10), pady=(0, 10))
        
        self.refresh()
        
    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        f = self.filter_type_var.get()
        doc_type = None
        if f == "Devis": doc_type = "devis"
        elif f == "Facture": doc_type = "facture"
            
        docs = database.get_all_documents(doc_type=doc_type)

        date_q = self.filter_date_var.get().strip().lower()
        search_q = self.filter_search_var.get().strip().lower()
        id_q = self.filter_id_var.get().strip()

        try:
            min_t = float(self.filter_min_var.get().strip())
        except ValueError:
            min_t = None
            
        try:
            max_t = float(self.filter_max_var.get().strip())
        except ValueError:
            max_t = None

        for d in docs:
            # Check ID exact
            if id_q and id_q != str(d["id"]):
                continue
                
            # Check min/max TTC
            if min_t is not None and d["total_ttc"] < min_t:
                continue
            if max_t is not None and d["total_ttc"] > max_t:
                continue

            # Check date criteria
            if date_q and date_q not in d["doc_date"].lower():
                continue
                
            # Check search criteria (name or number)
            if search_q:
                n = d["client_name"].lower()
                num = d["doc_num"].lower()
                if search_q not in n and search_q not in num:
                    continue

            ttc_str = _format_thousands(d['total_ttc']) + " MAD"
            type_str = "DEVIS" if d["doc_type"] == "devis" else "FACTURE"
            self.tree.insert("", "end", values=(d["id"], type_str, d["doc_num"], d["doc_date"], d["client_name"], ttc_str))
            
    def export_to_excel(self):
        """Exporte la vue actuelle de l'historique vers un fichier CSV compatible Excel."""
        items = self.tree.get_children()
        if not items:
            messagebox.showwarning("Export", "Aucune donnée à exporter.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"Historique_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            filetypes=[("Fichier CSV (Excel)", "*.csv")],
        )
        if not filename:
            return

        try:
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                # En-têtes
                writer.writerow(["ID", "Type", "N° Document", "Date", "Client", "Montant TTC"])
                # Lignes
                for item in items:
                    writer.writerow(self.tree.item(item)["values"])
            
            messagebox.showinfo("Export", f"Fichier exporté avec succès !\n\n{filename}")
        except Exception as e:
            messagebox.showerror("Erreur Export", f"Impossible d'exporter le fichier :\n{e}")
            
    def open_selected(self):
        sel = self.tree.selection()
        if not sel: return
        doc_id = self.tree.item(sel[0])["values"][0]
        self.on_open_doc(doc_id)
        
    def delete_selected(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Confirmation", "Supprimer ce document de l'historique ?"):
            doc_id = self.tree.item(sel[0])["values"][0]
            database.delete_document(doc_id)
            self.refresh()

    def convert_to_invoice(self):
        sel = self.tree.selection()
        if not sel: return
        doc_id = self.tree.item(sel[0])["values"][0]
        doc = database.get_document_by_id(doc_id)
        if not doc or doc["doc_type"] != "devis":
            messagebox.showinfo("Info", "Seul un devis peut être converti en facture.")
            return
        
        if messagebox.askyesno("Convertir", "Créer une facture à partir de ce devis ?"):
            self.on_open_doc(doc_id, force_type="facture")

# ==========================================
# Fenêtre : Mise à jour (Updater)
# ==========================================
class UpdateWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("🔄 Mise à jour & Historique des versions")
        self.geometry("600x500")
        self.grab_set()

        try:
            icon_path = config.resource_path("logo.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception as e:
            from logger import get_logger
            get_logger("ui").warning(f"Impossible de charger le logo: {e}")
        
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ttk.Label(main_frame, text=f"Version actuelle : v{config.APP_VERSION}", 
                  font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(0, 10))
        
        # ── Liste des versions (GitHub) ──
        list_frame = ttk.LabelFrame(main_frame, text="Historique des 5 dernières versions (GitHub)")
        list_frame.pack(fill="both", expand=True, pady=5)
        
        columns = ("version", "date", "status")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=5)
        self.tree.heading("version", text="Version")
        self.tree.heading("date", text="Date")
        self.tree.heading("status", text="Statut")
        self.tree.column("version", width=100)
        self.tree.column("date", width=100)
        self.tree.column("status", width=100)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # ── Changelog ──
        log_frame = ttk.LabelFrame(main_frame, text="Notes de version")
        log_frame.pack(fill="both", expand=True, pady=10)
        self.text_log = tk.Text(log_frame, height=8, font=("Helvetica", 9), state="disabled", wrap="word")
        self.text_log.pack(fill="both", expand=True, padx=5, pady=5)
        
        # ── Boutons d'action ──
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=5)
        
        self.btn_install = ttk.Button(btn_frame, text="📥 Installer la version sélectionnée", state="disabled", command=self._install_selected)
        self.btn_install.pack(side="left", padx=5)
        
        self.btn_local = ttk.Button(btn_frame, text="📁 MAJ Local", command=self._do_local)
        self.btn_local.pack(side="left", padx=5)
        
        ttk.Label(main_frame, text="⚠️ Vos données (factures, clients) ne seront pas touchées.", 
                  foreground="#64748b", font=("Helvetica", 8)).pack(anchor="w", pady=5)
        
        self._releases = []
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        
        # Chargement initial
        import threading
        threading.Thread(target=self._load_releases, daemon=True).start()

    def _load_releases(self):
        import updater
        res = updater.get_latest_releases(config.GITHUB_REPO, limit=5)
        
        def update_ui():
            if isinstance(res, list):
                self._releases = res
                for r in res:
                    status = "Actuelle" if r["version"] == config.APP_VERSION else "Disponible"
                    self.tree.insert("", "end", values=(f"v{r['version']}", r["date"], status))
            else:
                messagebox.showerror("Erreur", f"Impossible de charger les versions :\n{res}")
        self.after(0, update_ui)

    def _on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        idx = self.tree.index(sel[0])
        rel = self._releases[idx]
        
        self.text_log.config(state="normal")
        self.text_log.delete("1.0", "end")
        self.text_log.insert("1.0", rel["changelog"])
        self.text_log.config(state="disabled")
        self.btn_install.config(state="normal")

    def _install_selected(self):
        sel = self.tree.selection()
        if not sel: return
        idx = self.tree.index(sel[0])
        rel = self._releases[idx]
        
        is_rollback = False
        import updater
        curr_v = updater.parse_version(config.APP_VERSION)
        target_v = updater.parse_version(rel["version"])
        if target_v and curr_v and target_v < curr_v:
            is_rollback = True
        
        msg = f"Confirmer l'installation de la version v{rel['version']} ?"
        if is_rollback:
            msg = f"⚠️ ATTENTION : Vous allez installer une version PLUS ANCIENNE (v{rel['version']}).\n\nConfirmer le retour en arrière ?"
            
        if not messagebox.askyesno("Confirmation", msg):
            return
            
        import updater
        import sys
        
        is_frozen = getattr(sys, 'frozen', False)
        
        if is_frozen:
            if not rel.get("exe_url"):
                messagebox.showerror("Impossible", "Cette version sur GitHub ne contient pas de fichier exécutable (.exe) !\n\nVeuillez télécharger la mise à jour manuellement.")
                return
            success = updater.apply_update_exe(rel["exe_url"])
        else:
            success = updater.apply_update_from_zip(rel["zip_url"], os.path.dirname(__file__))
            
        if success is True:
            messagebox.showinfo("Succès", "Version installée !\n\nL'application va redémarrer pour appliquer les changements.")
            self.master.destroy()
        else:
            messagebox.showerror("Erreur", f"Échec de l'installation :\n{success}")

    def _do_local(self):
        import updater
        folder = filedialog.askdirectory(title="Dossier source de la mise à jour")
        if folder:
            success = updater.apply_update_from_folder(folder, os.path.dirname(__file__))
            if success is True:
                 messagebox.showinfo("Succès", "Mise à jour locale appliquée.\n\nVeuillez redémarrer.")
                 self.master.destroy()
            else:
                 messagebox.showerror("Erreur", success)

# ==========================================
# Fenêtre principale
# ==========================================

class AppDevis(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title(f"Générateur Devis & Factures — {config.COMPANY['name']}")
        self.geometry("900x600")
        self.configure(padx=8, pady=8)
        
        # Définir l'icône — iconphoto() est la seule méthode fiable pour la barre des tâches
        try:
            from PIL import Image, ImageTk
            # Chercher le logo PNG (haute résolution) ou ICO
            possible_icons = [
                config.resource_path("logo.png"),
                os.path.join(os.path.dirname(sys.executable), "_internal", "logo.png"),
                config.resource_path("logo.ico"),
                os.path.join(os.path.dirname(sys.executable), "_internal", "logo.ico"),
                os.path.join(os.path.dirname(sys.executable), "logo.ico"),
            ]
            icon_loaded = False
            for p in possible_icons:
                if os.path.exists(p):
                    img = Image.open(p).convert("RGBA").resize((256, 256), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.iconphoto(True, photo)
                    self._icon_photo = photo  # Garder la référence en mémoire!
                    icon_loaded = True
                    break
            # Fallback: aussi definir iconbitmap si logo.ico est dispo
            if icon_loaded:
                for p in possible_icons:
                    if p.endswith('.ico') and os.path.exists(p):
                        try:
                            self.iconbitmap(p)
                        except Exception:
                            pass
                        break
        except Exception:
            pass

        ttk.Style().theme_use("clam")

        # ==========================================
        # Barre de Menus (Aide)
        # ==========================================
        menubar = tk.Menu(self)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="📖 Guide d'utilisation", command=lambda: HelpWindow(self))
        help_menu.add_separator()
        help_menu.add_command(label="🔄 Rechercher une mise à jour", command=lambda: UpdateWindow(self))
        help_menu.add_separator()
        from tkinter import messagebox
        help_menu.add_command(label="À propos", command=lambda: messagebox.showinfo("À propos", f"Générateur Devis & Factures v{config.APP_VERSION}\n\nOptimisé pour {config.COMPANY.get('name', 'Fun Design')}\n\nSystème de mise à jour intégré avec GitHub (v3.2)."))
        
        menubar.add_cascade(label="Aide (?)", menu=help_menu)
        self.config(menu=menubar)
        
        # Colonnes partagées entre les deux onglets
        self._columns = load_columns()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tabs = {}
        for doc_type in ("devis", "facture"):
            tab = DocumentTab(self.notebook, doc_type, self._columns)
            self.tabs[doc_type] = tab
            self.notebook.add(tab, text=f"  {config.DOC_TYPES[doc_type]['label']}  ")

        self.clients_tab = ClientsTab(self.notebook)
        self.notebook.add(self.clients_tab, text="  👥 Clients  ")

        self.history_tab = HistoryTab(self.notebook, self.open_document_from_history)
        self.notebook.add(self.history_tab, text="  🕒 Historique  ")
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.on_tab_changed())

        ttk.Label(
            self,
            text="💡 Clic droit sur un en-tête pour renommer/masquer · ⊞ Nouvelle colonne pour en ajouter une",
            foreground="#64748b", font=("Helvetica", 9),
        ).pack(side="bottom", pady=4)

        # Bouton Paramètres (Placé en haut à droite, au dessus du notebook)
        btn_settings = ttk.Button(self, text="⚙ Paramètres", command=lambda: SettingsWindow(self))
        btn_settings.place(relx=1.0, rely=0.0, x=-12, y=6, anchor="ne")
        btn_settings.lift()

    def on_tab_changed(self):
        # Actualiser l'historique et les clients lors de la sélection de cet onglet
        current = self.notebook.index("current")
        if current == 2:
            self.clients_tab.refresh()
        elif current == 3:
            self.history_tab.refresh()

    def open_document_from_history(self, doc_id, force_type=None):
        doc = database.get_document_by_id(doc_id)
        if not doc:
            messagebox.showerror("Erreur", "Document introuvable.")
            return
            
        doc_type = doc["doc_type"]
        target_type = force_type if force_type else doc_type
        tab = self.tabs[target_type]
        
        tab_idx = 0 if target_type == "devis" else 1
        self.notebook.select(tab_idx)
        
        # Remplir les champs
        c_data = doc["client_data"]
        tab.entry_client.delete(0, tk.END); tab.entry_client.insert(0, c_data.get("name", ""))
        tab.entry_ice.delete(0, tk.END); tab.entry_ice.insert(0, c_data.get("ice", ""))
        tab.entry_address.delete(0, tk.END); tab.entry_address.insert(0, c_data.get("address", ""))
        
        if hasattr(tab, "entry_phone"):
            tab.entry_phone.delete(0, tk.END); tab.entry_phone.insert(0, c_data.get("phone", ""))
        
        if force_type:
            # Conversion : nouveau N° et date du jour
            tab.entry_date.delete(0, tk.END); tab.entry_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
            tab._regen_number()
        else:
            tab.entry_num.delete(0, tk.END); tab.entry_num.insert(0, c_data.get("num", ""))
            tab.entry_date.delete(0, tk.END); tab.entry_date.insert(0, c_data.get("date", ""))
        
        # Gérer l'auto-entrepreneur
        is_auto = doc.get("is_auto_entrepreneur", False)
        if hasattr(tab, "var_auto_entrepreneur"):
            tab.var_auto_entrepreneur.set(is_auto)
            tab._toggle_auto()
            
        # TVA
        tva_pct = doc["totals_data"].get("tva_percent", config.DEFAULT_TVA)
        if not is_auto:
            tab.entry_tva.config(state="normal")
            tab.entry_tva.delete(0, tk.END)
            tab.entry_tva.insert(0, str(tva_pct))
        
        # Lignes
        tab._rows_cache = doc["items_data"]
        tab._refresh_tree()
        tab.update_totals()

# ==========================================
# MAIN.PY — Point d'entrée de l'application
# ==========================================

def _check_dependencies():
    try:
        import reportlab  # noqa: F401
    except ImportError:
        import sys
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Bibliothèque manquante",
            "L'application nécessite 'reportlab'.\n\n"
            "Installez-la avec :\n    pip install reportlab",
        )
        sys.exit(1)


if __name__ == "__main__":
    _check_dependencies()
    from ui import AppDevis
    app = AppDevis()
    app.mainloop()

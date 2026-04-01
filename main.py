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
    import sys
    if sys.platform == "win32":
        try:
            import ctypes
            # Enable High DPI Awareness (Windows 8.1+)
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1) # PROCESS_SYSTEM_DPI_AWARE
            except Exception:
                # Fallback for older Windows versions (Windows Vista/7)
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass
            
            myappid = 'dz.fundesign.devisfacture.app.1_4_0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    from ui import AppDevis
    app = AppDevis()
    app.mainloop()

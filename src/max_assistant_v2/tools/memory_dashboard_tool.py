# src/max_assistant_v2/tools/memory_dashboard_tool.py
import tkinter as tk

from max_assistant_v2.memory.profile import ProfileMemory
from max_assistant_v2.ui.memory_dashboard import MemoryDashboardWindow


# Pour éviter d'ouvrir 10 fenêtres si tu répètes la commande
_DASH_OPEN = {"open": False}


def open_memory_dashboard():
    """
    Tool callable: ouvre une fenêtre Tkinter (Toplevel) en lecture seule.
    IMPORTANT: la création UI est schedulée sur le thread Tk via root.after().
    """
    root = tk._default_root  # root Tk existant (celui du SpeakingHUD)
    if root is None:
        return "Impossible d'ouvrir le dashboard: root Tk introuvable."

    def _open_on_ui_thread():
        if _DASH_OPEN["open"]:
            return

        _DASH_OPEN["open"] = True

        profile = ProfileMemory()

        win = MemoryDashboardWindow(root, profile)

        # quand la fenêtre est détruite, on libère le flag
        def _on_close():
            _DASH_OPEN["open"] = False
            try:
                win.win.destroy()
            except Exception:
                pass

        win.win.protocol("WM_DELETE_WINDOW", _on_close)

    root.after(0, _open_on_ui_thread)
    return "Dashboard mémoire ouvert."

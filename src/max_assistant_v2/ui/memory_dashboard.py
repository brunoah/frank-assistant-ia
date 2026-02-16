# src/max_assistant_v2/ui/memory_dashboard.py
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Any, Dict, Optional


def _age_days(ts: Optional[float]) -> str:
    try:
        if not ts:
            return "—"
        days = (datetime.now().timestamp() - float(ts)) / 86400.0
        return f"{max(0.0, days):.1f} j"
    except Exception:
        return "—"


class MemoryDashboardWindow:
    """
    Fenêtre UI (Toplevel) pour visualiser data/profile.json (ProfileMemory).
    Ne modifie rien, lecture seule.
    """

    def __init__(self, root: tk.Tk, profile_obj):
        self.root = root
        self.profile = profile_obj  # ProfileMemory
        self.win = tk.Toplevel(root)
        self.win.title("🧠 FRANK — Memory Dashboard")
        self.win.geometry("780x520")
        self.win.attributes("-topmost", True)

        self._build_style()
        self._build_ui()
        self.refresh()

        # si tu fermes la fenêtre, on détruit proprement
        self.win.protocol("WM_DELETE_WINDOW", self.win.destroy)

    def _build_style(self):
        self.win.configure(bg="#121212")

        style = ttk.Style(self.win)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background="#121212")
        style.configure("TLabel", background="#121212", foreground="#EAEAEA")
        style.configure("TButton", background="#1f1f1f", foreground="#EAEAEA")
        style.configure("TNotebook", background="#121212", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1b1b1b", foreground="#EAEAEA", padding=(10, 6))
        style.map("TNotebook.Tab", background=[("selected", "#2a2a2a")])

        style.configure("Treeview",
                        background="#161616",
                        fieldbackground="#161616",
                        foreground="#EAEAEA",
                        rowheight=24)
        style.map("Treeview", background=[("selected", "#2d2d2d")])

    def _build_ui(self):
        top = ttk.Frame(self.win)
        top.pack(fill="x", padx=12, pady=10)

        title = ttk.Label(top, text="🧠 Memory Dashboard", font=("Segoe UI", 14, "bold"))
        title.pack(side="left")

        refresh_btn = ttk.Button(top, text="🔄 Rafraîchir", command=self.refresh)
        refresh_btn.pack(side="right")

        self.nb = ttk.Notebook(self.win)
        self.nb.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Tabs
        self.tab_identity = ttk.Frame(self.nb)
        self.tab_relations = ttk.Frame(self.nb)
        self.tab_projects = ttk.Frame(self.nb)
        self.tab_prefs = ttk.Frame(self.nb)
        self.tab_patterns = ttk.Frame(self.nb)

        self.nb.add(self.tab_identity, text="Identité")
        self.nb.add(self.tab_relations, text="Relations")
        self.nb.add(self.tab_projects, text="Projets")
        self.nb.add(self.tab_prefs, text="Préférences")
        self.nb.add(self.tab_patterns, text="Emotion patterns")

        # Layout trees
        self.identity_text = tk.Text(self.tab_identity, bg="#161616", fg="#EAEAEA", insertbackground="#EAEAEA",
                                     relief="flat", height=8)
        self.identity_text.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree_rel = self._make_tree(self.tab_relations, cols=("type", "value", "importance", "age"))
        self.tree_proj = self._make_tree(self.tab_projects, cols=("value", "importance", "age"))
        self.tree_prefs = self._make_tree(self.tab_prefs, cols=("key", "value", "importance", "age"))
        self.tree_patterns = self._make_tree(self.tab_patterns, cols=("keyword", "emotion", "count", "age"))

    def _make_tree(self, parent, cols):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tree = ttk.Treeview(frame, columns=cols, show="headings")
        tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        vsb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=vsb.set)

        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="w", width=140)

        return tree

    def _clear_tree(self, tree: ttk.Treeview):
        for i in tree.get_children():
            tree.delete(i)

    def refresh(self):
        # recharge depuis le ProfileMemory (déjà géré par lui)
        data: Dict[str, Any] = getattr(self.profile, "data", {}) or {}

        # Identité
        self.identity_text.config(state="normal")
        self.identity_text.delete("1.0", "end")
        name = data.get("name")
        loc = data.get("location")
        self.identity_text.insert("end", "Nom:\n")
        self.identity_text.insert("end", f"  - {name.get('value') if isinstance(name, dict) else '—'}\n")
        self.identity_text.insert("end", "\nLocation:\n")
        self.identity_text.insert("end", f"  - {loc.get('value') if isinstance(loc, dict) else '—'}\n")
        self.identity_text.config(state="disabled")

        # Relations
        self._clear_tree(self.tree_rel)
        rels = data.get("relations", {}) or {}
        for rtype, item in rels.items():
            if not isinstance(item, dict):
                continue
            self.tree_rel.insert("", "end", values=(
                rtype,
                item.get("value", ""),
                f"{item.get('importance', 0.0):.2f}",
                _age_days(item.get("timestamp")),
            ))

        # Projets
        self._clear_tree(self.tree_proj)
        projs = data.get("projects", []) or []
        for p in projs:
            if not isinstance(p, dict):
                continue
            self.tree_proj.insert("", "end", values=(
                p.get("value", ""),
                f"{p.get('importance', 0.0):.2f}",
                _age_days(p.get("timestamp")),
            ))

        # Préférences
        self._clear_tree(self.tree_prefs)
        prefs = data.get("preferences", {}) or {}
        for k, item in prefs.items():
            if not isinstance(item, dict):
                continue
            self.tree_prefs.insert("", "end", values=(
                k,
                item.get("value", ""),
                f"{item.get('importance', 0.0):.2f}",
                _age_days(item.get("timestamp")),
            ))

        # Emotion patterns
        self._clear_tree(self.tree_patterns)
        patterns = data.get("emotion_patterns", {}) or {}
        for keyword, emo_map in patterns.items():
            if not isinstance(emo_map, dict):
                continue
            for emo, meta in emo_map.items():
                if not isinstance(meta, dict):
                    continue
                self.tree_patterns.insert("", "end", values=(
                    keyword,
                    emo,
                    meta.get("count", 0),
                    _age_days(meta.get("last_seen")),
                ))

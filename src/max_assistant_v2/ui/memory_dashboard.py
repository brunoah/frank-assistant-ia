import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from typing import Any, Dict, Optional
from max_assistant_v2.core.project_manager import ProjectManager

def _age_days(ts: Optional[float]) -> str:
    try:
        if not ts:
            return "—"
        days = (datetime.now().timestamp() - float(ts)) / 86400.0
        return f"{max(0.0, days):.1f} j"
    except Exception:
        return "—"

def _importance_color(value: float) -> str:
    if value >= 0.8:
        return "#ff4c4c"  # rouge
    elif value >= 0.6:
        return "#ff944d"  # orange
    elif value >= 0.3:
        return "#ffd11a"  # jaune
    else:
        return "#4dff88"  # vert

def _emotion_value(emotion: str) -> int:
    mapping = {
        "CALME": 1,
        "FOCUS": 2,
        "REFLEXION": 3,
        "ERREUR": 4
    }
    return mapping.get(emotion.upper(), 0)


def _emotion_color(emotion: str) -> str:
    e = (emotion or "").strip().upper()

    # Mets ici TES émotions USER connues si tu en as (exemples)
    colors = {
        "JOIE": "#4dff88",
        "TRISTESSE": "#4d88ff",
        "COLERE": "#ff4c4c",
        "PEUR": "#ffaa00",
        "SURPRISE": "#00ccff",
        "NEUTRE": "#aaaaaa",
    }

    return colors.get(e, "#888888")



class MemoryDashboardWindow:

    def __init__(self, root: tk.Tk, profile_obj):
        self.root = root
        self.profile = profile_obj
        self.project_manager = ProjectManager()
        self.win = tk.Toplevel(root)
        self.win.title("🧠 FRANK — Memory Dashboard")
        self.win.geometry("900x550")
        self.win.configure(bg="#121212")

        self._build_style()
        self._build_ui()
        self.refresh()

    def _build_style(self):
        style = ttk.Style(self.win)
        try:
            style.theme_use("clam")
        except:
            pass

        style.configure("Treeview",
                        background="#161616",
                        fieldbackground="#161616",
                        foreground="#EAEAEA",
                        rowheight=24)
    

    def _build_timeline_tab(self):

        container = ttk.Frame(self.tab_timeline)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        self.timeline_canvas = tk.Canvas(
            container,
            bg="#111111",
            height=350,
            highlightthickness=0
        )
        self.timeline_canvas.pack(fill="both", expand=True)

        self.animate_timeline()

    
    def _build_ui(self):

        top = ttk.Frame(self.win)
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="🧠 Memory Dashboard", font=("Segoe UI", 14, "bold")).pack(side="left")

        ttk.Button(top, text="🔄 Rafraîchir", command=self.refresh).pack(side="right")

        self.nb = ttk.Notebook(self.win)
        self.nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_projects = ttk.Frame(self.nb)
        self.tab_prefs = ttk.Frame(self.nb)

        self.nb.add(self.tab_projects, text="Projets")
        self.nb.add(self.tab_prefs, text="Préférences")
        self.tab_timeline = ttk.Frame(self.nb)
        self.nb.add(self.tab_timeline, text="Timeline émotionnelle")
        self._build_timeline_tab()


        self._build_projects_tab()
        self._build_prefs_tab()

    def animate_timeline(self):

        data = getattr(self.profile, "data", {}) or {}
        history = data.get("emotion_history", [])
        history = history[-30:]

        self.timeline_canvas.delete("all")

        if not history:
            self.timeline_canvas.create_text(
                400, 175,
                text="Aucune donnée émotionnelle",
                fill="#888888",
                font=("Segoe UI", 12)
            )
            self.win.after(1500, self.animate_timeline)
            return

        width = self.timeline_canvas.winfo_width()
        height = self.timeline_canvas.winfo_height()

        # =========================
        # AXE VERTICAL DYNAMIQUE (émotions USER réelles)
        # =========================
        SPACING = 60  # même espacement que ta courbe

        # liste des émotions réellement présentes (ordre d’apparition)
        emotions = []
        seen = set()
        for e in history:
            emo = (e.get("emotion") or "").strip()
            if not emo:
                continue
            if emo not in seen:
                seen.add(emo)
                emotions.append(emo)

        # fallback si vide
        if not emotions:
            emotions = ["(aucune)"]

        # map émotion -> niveau (1..N)
        emo_level = {emo: idx + 1 for idx, emo in enumerate(emotions)}

        # dessiner lignes + labels
        for emo, lvl in emo_level.items():
            y = height - (lvl * SPACING)

            self.timeline_canvas.create_line(
                90, y,
                width - 20, y,
                fill="#222222"
            )

            self.timeline_canvas.create_text(
                10, y,
                text=emo,
                anchor="w",
                fill=_emotion_color(emo),
                font=("Segoe UI", 9, "bold")
            )



        max_points = 30
        history = history[-max_points:]

        step_x = width / max(1, len(history))

        previous = None

        for i, entry in enumerate(history):

            emotion = (entry.get("emotion") or "").strip()
            intensity = float(entry.get("intensity", 0.5))

            lvl = emo_level.get(emotion, 1)
            x = i * step_x + 110   # on décale à droite pour laisser la place aux labels
            y = height - (lvl * SPACING)

            r = 3 + int(6 * max(0.0, min(1.0, intensity)))  # rayon 3..9
            color = _emotion_color(emotion)
            
            # Point
            self.timeline_canvas.create_oval(
                x - r, y - r, x + r, y + r,
                fill=color,
                outline=""
            )

            # Ligne
            if previous:
                self.timeline_canvas.create_line(
                    previous[0], previous[1],
                    x, y,
                    fill=color,
                    width=2,
                    smooth=True
                )

            previous = (x, y)

        self.win.after(1500, self.animate_timeline)


    # =============================
    # PROJECTS
    # =============================

    def _build_projects_tab(self):
        frame = ttk.Frame(self.tab_projects)
        frame.pack(fill="both", expand=True)

        self.tree_proj = ttk.Treeview(frame, columns=("title", "created_at", "theme"), show="headings")
        self.tree_proj.pack(fill="both", expand=True, padx=10, pady=10)

        for c in ("title", "created_at", "theme"):
            self.tree_proj.heading(c, text=c)

        btn_frame = ttk.Frame(self.tab_projects)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="➕ Ajouter", command=self.add_project).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑 Supprimer", command=self.delete_project).pack(side="left", padx=5)

    def add_project(self):
        title = simpledialog.askstring("Nouveau Projet", "Titre du projet :")
        if not title:
            return

        description = simpledialog.askstring("Description", "Description (optionnel) :") or ""
        theme = simpledialog.askstring("Thème", "Thème (optionnel) :") or ""

        try:
            self.project_manager.add_project(title, description, theme)
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
            return

        self.refresh()


    def delete_project(self):
        selected = self.tree_proj.selection()
        if not selected:
            return

        item = self.tree_proj.item(selected[0])
        title = item["values"][0]

        project = self.project_manager.find_by_title(title)
        if not project:
            return

        confirm = messagebox.askyesno("Confirmation", f"Supprimer le projet '{title}' ?")
        if not confirm:
            return

        self.project_manager.delete_project(project["id"])
        self.refresh()


        self.profile.data["projects"] = [
            p for p in self.profile.data.get("projects", [])
            if p.get("value") != value
        ]
        self.profile.save()
        self.refresh()

    # =============================
    # PREFERENCES
    # =============================

    def _build_prefs_tab(self):
        frame = ttk.Frame(self.tab_prefs)
        frame.pack(fill="both", expand=True)

        self.tree_prefs = ttk.Treeview(frame, columns=("key", "value", "importance", "age"), show="headings")
        self.tree_prefs.pack(fill="both", expand=True, padx=10, pady=10)

        for c in ("key", "value", "importance", "age"):
            self.tree_prefs.heading(c, text=c)

        btn_frame = ttk.Frame(self.tab_prefs)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="✏️ Modifier", command=self.edit_preference).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑 Supprimer", command=self.delete_preference).pack(side="left", padx=5)

    def edit_preference(self):
        selected = self.tree_prefs.selection()
        if not selected:
            return

        item = self.tree_prefs.item(selected[0])
        key, old_value = item["values"][0], item["values"][1]

        new_value = simpledialog.askstring("Modifier Préférence", f"Nouvelle valeur pour '{key}' :", initialvalue=old_value)
        if not new_value:
            return

        self.profile.set_preference(key, new_value)
        self.refresh()

    def delete_preference(self):
        selected = self.tree_prefs.selection()
        if not selected:
            return

        item = self.tree_prefs.item(selected[0])
        key = item["values"][0]

        confirm = messagebox.askyesno("Confirmation", f"Supprimer la préférence '{key}' ?")
        if not confirm:
            return

        if key in self.profile.data.get("preferences", {}):
            del self.profile.data["preferences"][key]
            self.profile.save()

        self.refresh()

    # =============================
    # REFRESH
    # =============================

    def refresh(self):
        data: Dict[str, Any] = getattr(self.profile, "data", {}) or {}

        # Projects (via ProjectManager)
        for i in self.tree_proj.get_children():
            self.tree_proj.delete(i)

        projects = self.project_manager.list_projects()

        for p in projects:
            item_id = self.tree_proj.insert("", "end", values=(
                p.get("title", ""),
                p.get("created_at", ""),
                p.get("theme", "")
            ))


        # Preferences
        # Preferences
        for i in self.tree_prefs.get_children():
            self.tree_prefs.delete(i)

        prefs = data.get("preferences", {})

        for k, item in prefs.items():

            if not isinstance(item, dict):
                continue

            importance = float(item.get("importance", 0.0))
            color = _importance_color(importance)

            item_id = self.tree_prefs.insert("", "end", values=(
                k,
                item.get("value"),
                f"{importance:.2f}",
                _age_days(item.get("timestamp"))
            ))

            self.tree_prefs.tag_configure(str(item_id), foreground=color)
            self.tree_prefs.item(item_id, tags=(str(item_id),))


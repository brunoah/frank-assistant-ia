import json
from pathlib import Path
from typing import Dict, Callable
from max_assistant_v2.core.agenda_manager import AgendaManager

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.apps = self._load_apps()

        self.agenda = AgendaManager()
        self.register("agenda", self._agenda_tool)

    def _load_apps(self):
        # remonte jusqu'à la racine du projet
        project_root = Path(__file__).resolve().parents[3]

        path = project_root / "data" / "apps.json"

        if not path.exists():
            print(f"[ToolRegistry] apps.json non trouvé à {path}")
            return {}

        # print(f"[ToolRegistry] apps.json chargé depuis {path}")

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


    def register(self, name: str, func: Callable):
        self.tools[name] = func

    def execute(self, name: str, **kwargs):
        if name not in self.tools:
            return f"Outil inconnu: {name}"

        try:
            return self.tools[name](**kwargs)
        except Exception as e:
            return f"Erreur lors de l'exécution de {name}: {e}"

    def list_apps(self):
        return list(self.apps.keys())

    def _agenda_tool(self, action=None, title=None, raw_text=None, **kwargs):

        text = (raw_text or "").lower()

        # 🔎 Détection automatique si action absente
        if not action:
            if "liste" in text or "mes rendez" in text or "agenda" in text:
                action = "list"

            elif "supprime" in text:
                action = "delete"

            else:
                action = "add"

        # 🟢 Add
        if action == "add":
            return self.agenda.add_event_from_text(title, raw_text)

        # 📅 List
        if action == "list":
            return self.agenda.list_events()

        # ❌ Delete
        if action == "delete":
            return self.agenda.delete_event(title)

        return "Action agenda inconnue."


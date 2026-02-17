import json
from pathlib import Path
from datetime import datetime


class AgendaManager:
    def __init__(self):
        project_root = Path(__file__).resolve().parents[3]
        self.path = project_root / "data" / "agenda.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self):
        if not self.path.exists():
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _load(self):
        try:
            if not self.path.exists() or self.path.stat().st_size == 0:
                return []

            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)

        except json.JSONDecodeError:
            return []

    def _save(self, data):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_event(self, title, date, time):
        data = self._load()

        event = {
            "title": title,
            "date": date,
            "time": time,
            "created_at": datetime.now().isoformat()
        }

        data.append(event)
        self._save(data)

        return f"Événement ajouté : {title} le {date} à {time}"

    def list_events(self):
        data = self._load()

        if not data:
            return "Aucun événement enregistré."

        formatted = []
        for e in data:
            formatted.append(f"{e['date']} {e['time']} - {e['title']}")

        return "\n".join(formatted)

    def delete_event(self, title):
        data = self._load()
        new_data = [e for e in data if e["title"].lower() != title.lower()]

        if len(new_data) == len(data):
            return "Aucun événement trouvé avec ce titre."

        self._save(new_data)
        return f"Événement supprimé : {title}"

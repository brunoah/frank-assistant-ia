import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class ProjectManager:
    def __init__(self, path: str | Path = "data/projects.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._save({"projects": []})

    def _load(self) -> Dict:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: Dict) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def list_projects(self) -> List[Dict]:
        return (self._load().get("projects") or [])

    def add_project(self, title: str, description: str = "", theme: str = "") -> Dict:
        title = (title or "").strip()
        description = (description or "").strip()
        theme = (theme or "").strip()

        if len(title) < 2:
            raise ValueError("Le titre du projet est trop court.")

        data = self._load()

        project = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "theme": theme,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

        data["projects"].append(project)
        self._save(data)
        return project

    def set_current_project(self, project_id):
        data = self._load()
        data["current_project_id"] = project_id
        self._save(data)


    def get_current_project(self):
        data = self._load()
        current_id = data.get("current_project_id")

        if not current_id:
            return None

        for p in data["projects"]:
            if p["id"] == current_id:
                return p

        return None
    
    def update_project(self, project_id: str, field: str, value: str):
        data = self._load()

        for p in data["projects"]:
            if p["id"] == project_id:
                p[field] = value
                self._save(data)
                return p

        return None
    
    def delete_project(self, project_id: str) -> bool:
        data = self._load()
        before = len(data["projects"])
        data["projects"] = [p for p in data["projects"] if p.get("id") != project_id]
        self._save(data)
        return len(data["projects"]) != before

    def find_by_title(self, title: str) -> Optional[Dict]:
        t = (title or "").strip().lower()
        for p in self.list_projects():
            if (p.get("title") or "").strip().lower() == t:
                return p
        return None

    def search(self, query: str) -> List[Dict]:
        q = (query or "").strip().lower()
        if not q:
            return []

        results = []
        for p in self.list_projects():
            hay = " ".join([
                p.get("title", ""),
                p.get("description", ""),
                p.get("theme", "")
            ]).lower()

            if q in hay:
                results.append(p)

        return results

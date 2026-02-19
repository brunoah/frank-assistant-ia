import json
import os
import shutil
from pathlib import Path
from typing import Optional

from max_assistant_v2.utils.logger import get_logger

log = get_logger(__name__)


class SystemResetTools:
    """
    RESET TOTAL FRANK :
    - profile.json (mémoire profil / prefs / relations / patterns / métriques)
    - agenda.json (rdv)
    - projects.json (projets + projet actif)
    - long_term.jsonl (mémoire long terme)
    - vector_store/ (faiss + meta)
    """

    def __init__(self, registry, profile=None, projects_manager=None):
        self.registry = registry
        self.profile = profile                  # instance ProfileMemory (si fournie)
        self.projects_manager = projects_manager  # instance ProjectManager (si fournie)

        self.registry.register("system_full_reset", self.system_full_reset)

        # Racine projet -> .../src/max_assistant_v2/tools/system_reset_tools.py -> parents[3] = root
        self.project_root = Path(__file__).resolve().parents[3]
        self.data_dir = self.project_root / "data"

        self.profile_path = self.data_dir / "profile.json"
        self.agenda_path = self.data_dir / "agenda.json"
        self.projects_path = self.data_dir / "projects.json"
        self.long_term_path = self.data_dir / "long_term.jsonl"
        self.vector_store_dir = self.data_dir / "vector_store"

    def _write_json(self, path: Path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _truncate_file(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("")

    def _delete_dir(self, path: Path):
        if path.exists() and path.is_dir():
            shutil.rmtree(path, ignore_errors=True)

    def system_full_reset(self):
        try:
            # 1) Reset PROFILE (structure par défaut)
            default_profile = {
                "name": None,
                "location": None,
                "relations": {},
                "projects": [],
                "preferences": {},
                "emotion_patterns": {},
                "behavior_metrics": {},
                "emotional_state": {"value": None, "intensity": 0.0, "timestamp": 0.0},
            }
            self._write_json(self.profile_path, default_profile)

            # Met à jour l'instance mémoire en RAM si on l'a
            if self.profile is not None:
                try:
                    self.profile.data = default_profile
                    self.profile.save()
                except Exception as e:
                    log.warning(f"ProfileMemory RAM refresh failed: {e}")

            # 2) Reset AGENDA (RDV)
            self._write_json(self.agenda_path, [])

            # 3) Reset PROJECTS (projets + current_project_id)
            self._write_json(self.projects_path, {"projects": [], "current_project_id": None})

            # 4) Reset LONG TERM
            self._truncate_file(self.long_term_path)

            # 5) Reset VECTOR STORE
            self._delete_dir(self.vector_store_dir)

            log.critical("🔥 RESET TOTAL FRANK : mémoire + rdv + projets + long terme + vector store")

            return (
                "Réinitialisation totale effectuée : mémoire, rendez-vous, projets, long terme et index supprimés. "
                "Je repars sur une base vierge."
            )

        except Exception as e:
            log.error(f"Erreur reset total: {e}")
            return "Erreur lors de la réinitialisation complète."

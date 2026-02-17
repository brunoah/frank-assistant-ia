import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, List


PROFILE_PATH = Path("data/profile.json")


def _now() -> float:
    return time.time()


def _is_item_dict(x: Any) -> bool:
    return isinstance(x, dict) and "value" in x


def _to_item(value: str, importance: float) -> Dict[str, Any]:
    return {"value": value, "timestamp": _now(), "importance": float(importance)}


def _age_days(ts: float) -> float:
    return max(0.0, (_now() - float(ts)) / 86400.0)


def _decay_factor(ts: float, half_life_days: float) -> float:
    # score divisé par 2 tous les half_life_days
    if half_life_days <= 0:
        return 1.0
    return 0.5 ** (_age_days(ts) / half_life_days)


class ProfileMemory:
    """
    Schéma final:
    {
      "name": {"value": "...", "timestamp": ..., "importance": ...} | null,
      "location": {...} | null,
      "relations": { "femme": {...}, ... },
      "projects": [ {...}, ... ],
      "preferences": { "style": {...}, ... }
    }
    """

    def __init__(self):
        PROFILE_PATH.parent.mkdir(exist_ok=True)

        default_structure = {
            "name": None,
            "location": None,
            "relations": {},
            "projects": [],
            "preferences": {},
            "emotion_patterns": {},
            "behavior_metrics": {}
        }

        if not PROFILE_PATH.exists():
            PROFILE_PATH.write_text(json.dumps(default_structure, indent=2), encoding="utf-8")

        self.data = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

        # 1) Réparer clés manquantes
        for k, v in default_structure.items():
            if k not in self.data:
                self.data[k] = v

        # 2) Migration depuis anciens formats (strings)
        self._migrate()

        self.save()

    def save(self):
        PROFILE_PATH.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---------------- MIGRATION ----------------

    def _migrate(self):
        # name: "" -> None, "Bruno" -> item dict
        name = self.data.get("name")
        if isinstance(name, str):
            name = name.strip()
            self.data["name"] = _to_item(name, 1.0) if name else None

        # location: "" -> None, "Lyon" -> item dict
        loc = self.data.get("location")
        if isinstance(loc, str):
            loc = loc.strip()
            self.data["location"] = _to_item(loc, 0.9) if loc else None

        # relations: {"femme": "Lorie"} -> {"femme": item}
        rels = self.data.get("relations", {})
        if isinstance(rels, dict):
            new_rels = {}
            for k, v in rels.items():
                if isinstance(v, str):
                    vv = v.strip()
                    if vv:
                        new_rels[k] = _to_item(vv, 0.9)
                elif _is_item_dict(v):
                    new_rels[k] = v
            self.data["relations"] = new_rels
        else:
            self.data["relations"] = {}

        # projects: ["x"] -> [item], [{"value":...}] -> ok
        projs = self.data.get("projects", [])
        new_projs: List[Dict[str, Any]] = []
        if isinstance(projs, list):
            for p in projs:
                if isinstance(p, str):
                    pp = p.strip()
                    if pp:
                        new_projs.append(_to_item(pp, 0.8))
                elif _is_item_dict(p):
                    new_projs.append(p)
        self.data["projects"] = new_projs

        # preferences: {"style":"court"} -> {"style": item}
        prefs = self.data.get("preferences", {})
        new_prefs = {}
        if isinstance(prefs, dict):
            for k, v in prefs.items():
                if isinstance(v, str):
                    vv = v.strip()
                    if vv:
                        new_prefs[k] = _to_item(vv, 0.7)
                elif _is_item_dict(v):
                    new_prefs[k] = v
        self.data["preferences"] = new_prefs

        # Dédup projets (mêmes value)
        self._dedup_projects()

    def _dedup_projects(self):
        seen = set()
        dedup = []
        for p in self.data.get("projects", []):
            val = (p.get("value") or "").strip().lower()
            if not val or val in seen:
                continue
            seen.add(val)
            dedup.append(p)
        self.data["projects"] = dedup

    def update_emotion_pattern(self, user_text: str, emotion: str):
        emotion = (emotion or "").strip().lower()
        if not emotion:
            return

        text = (user_text or "").lower()

        keywords = ["travail", "boulot", "projet", "code", "assistant", "lm studio", "python"]
        patterns = self.data.setdefault("emotion_patterns", {})

        now = _now()
        cooldown_sec = 60  # 1 minute anti-spam

        for k in keywords:
            if k not in text:
                continue

            domain = patterns.setdefault(k, {})
            emo_data = domain.setdefault(emotion, {"count": 0, "last_seen": 0})

            last_seen = float(emo_data.get("last_seen", 0.0))
            if now - last_seen < cooldown_sec:
                # trop récent → on ne compte pas, mais on refresh last_seen
                emo_data["last_seen"] = now
                self.save()
                return

            # decay du count si vieux (stabilise les tendances)
            age_days = (now - last_seen) / 86400.0 if last_seen > 0 else 0.0
            if last_seen > 0 and age_days > 14:
                # on affaiblit progressivement au fil du temps
                emo_data["count"] = max(0, int(emo_data["count"] * 0.8))

            emo_data["count"] += 1
            emo_data["last_seen"] = now

            self.save()
            return



    # ---------------- SETTERS / GETTERS ----------------
    def bump_metric(self, key: str, inc: int = 1):
        metrics = self.data.setdefault("behavior_metrics", {})
        metrics[key] = int(metrics.get(key, 0)) + int(inc)
        self.save()

    def set_last_mode(self, mode: str):
        metrics = self.data.setdefault("behavior_metrics", {})
        metrics["last_mode"] = (mode or "").lower().strip()
        metrics["last_mode_ts"] = _now()
        self.save()


    def set_name(self, name: str):
        name = (name or "").strip()
        if len(name) < 2:
            return
        self.data["name"] = _to_item(name.capitalize(), 1.0)
        self.save()

    def get_name(self) -> Optional[str]:
        item = self.data.get("name")
        return item.get("value") if _is_item_dict(item) else None

    def set_location(self, location: str):
        location = (location or "").strip()
        if len(location) < 2:
            return
        self.data["location"] = _to_item(location.capitalize(), 0.9)
        self.save()

    def get_location(self) -> Optional[str]:
        item = self.data.get("location")
        return item.get("value") if _is_item_dict(item) else None

    def set_relation(self, relation_type: str, name: str):
        relation_type = (relation_type or "").strip().lower()
        name = (name or "").strip()
        if not relation_type or len(name) < 2:
            return
        self.data["relations"][relation_type] = _to_item(name.capitalize(), 0.9)
        self.save()

    def get_relation(self, relation_type: str) -> Optional[str]:
        item = self.data.get("relations", {}).get((relation_type or "").strip().lower())
        return item.get("value") if _is_item_dict(item) else None

    def add_project(self, project: str):
        project = (project or "").strip()

        INVALID_VALUES = {
            "inconnu",
            "aucun",
            "aucune",
            "rien",
            "à personne",
            "personne",
            "je ne sais pas",
            "non",
            "n/a",
            "none",
        }

        if len(project) < 3:
            return

        if project.lower() in INVALID_VALUES:
            return


    
    def get_preference(self, key: str, default: str | None = None):
        prefs = self.data.get("preferences") or {}
        item = prefs.get(key)
        if isinstance(item, dict):
            return item.get("value", default)
        return default

    
    def set_preference(self, key: str, value: str, importance: float = 0.7):
        key = (key or "").strip().lower()
        value = (value or "").strip()
        if not key or len(value) < 1:
            return
        self.data["preferences"][key] = _to_item(value, float(importance))
        self.save()

    def set_emotion(self, emotion: str, intensity: float = 0.8):
        emotion = (emotion or "").strip().lower()
        if not emotion:
            return

        # 🔥 NORMALISATION GLOBALE
        NORMALIZED_EMOTIONS = {
            "stress": "stressé",
            "fatigu": "fatigué",
            "frustr": "frustré",
            "motiv": "motivé",
            "heureu": "heureux",
        }

        for key, val in NORMALIZED_EMOTIONS.items():
            if emotion.startswith(key):
                emotion = val
                break


        cur = self.data.get("emotional_state") or {
            "value": None,
            "intensity": 0.0,
            "timestamp": 0.0,
        }

        cur_value = cur.get("value")
        cur_intensity = float(cur.get("intensity", 0.0))
        cur_ts = float(cur.get("timestamp", 0.0))

        age_sec = max(0.0, _now() - cur_ts)

        # 🔁 Cooldown intelligent
        if cur_value == emotion and age_sec < 30:
            new_intensity = min(1.0, cur_intensity + 0.10)
            cur["intensity"] = new_intensity
            cur["timestamp"] = _now()
            self.data["emotional_state"] = cur
            self.save()
            return

        # 🆕 Nouveau set propre
        self.data["emotional_state"] = {
            "value": emotion,
            "intensity": float(max(0.0, min(1.0, intensity))),
            "timestamp": _now(),
        }

        self.save()




    def get_emotion(self):
        emo = self.data.get("emotional_state") or {}

        value = emo.get("value")
        if not value:
            return None, 0.0

        ts = float(emo.get("timestamp", 0.0))
        base_intensity = float(emo.get("intensity", 0.0))

        # demi-vie (en heures) : plus bas = retombe plus vite
        half_life_hours = 3.0
        age_hours = max(0.0, (_now() - ts) / 3600.0)

        # decay exponentiel via half-life
        decay = 0.5 ** (age_hours / half_life_hours)
        intensity = base_intensity * decay

        # seuil de disparition
        if intensity < 0.15:
            self.data["emotional_state"] = {"value": None, "intensity": 0.0, "timestamp": 0.0}
            self.save()
            return None, 0.0

        # option: on met à jour l’intensité décroit dans le JSON (stabilité)
        emo["intensity"] = float(intensity)
        self.data["emotional_state"] = emo
        self.save()

        return value, intensity



    # ---------------- SCORING / CONTEXT ----------------
    def cleanup(self):
        # Supprime éléments trop faibles
        threshold = 0.05

        for section in ["projects"]:
            cleaned = []
            for item in self.data.get(section, []):
                if self._score(item, 90) > threshold:
                    cleaned.append(item)
            self.data[section] = cleaned

        prefs = self.data.get("preferences", {})
        to_delete = []
        for k, v in prefs.items():
            if self._score(v, 180) < threshold:
                to_delete.append(k)
        for k in to_delete:
            del prefs[k]

        self.save()

    def _score(self, item: Dict[str, Any], half_life_days: float) -> float:
        imp = float(item.get("importance", 0.5))
        ts = float(item.get("timestamp", _now()))
        return imp * _decay_factor(ts, half_life_days)

    def build_context(self, hint_text: str = "") -> str:
        hint = (hint_text or "").lower()

        need_location = any(w in hint for w in ["météo", "meteo", "où", "ou ", "adresse", "ville", "localisation"])
        need_projects = any(w in hint for w in ["projet", "code", "assistant", "python"])
        need_rel = any(w in hint for w in ["femme", "mari", "enfant", "frère", "soeur", "sœur", "parents"])

        lines = []

        # ---------------- Nom (toujours)
        name_item = self.data.get("name")
        if _is_item_dict(name_item):
            lines.append(f"- Nom: {name_item['value']}")

        # ---------------- Top Projet (toujours si existe)
        projs = self.data.get("projects", [])
        scored_projects = []
        for p in projs:
            if _is_item_dict(p):
                scored_projects.append((self._score(p, half_life_days=90), p))

        sorted_projects = sorted(scored_projects, reverse=True)

        if sorted_projects:
            lines.append(f"- Projet principal: {sorted_projects[0][1]['value']}")

        # Injecter projets supplémentaires seulement si hint lié
        if need_projects:
            for _, p in sorted_projects[1:3]:
                lines.append(f"- Projet: {p['value']}")

        # ---------------- Préférences (toujours top 2)
        prefs = self.data.get("preferences", {})
        scored_prefs = []

        if isinstance(prefs, dict):
            for k, v in prefs.items():
                if _is_item_dict(v):
                    scored_prefs.append((self._score(v, half_life_days=180), k, v))

        sorted_prefs = sorted(scored_prefs, reverse=True)

        for _, k, v in sorted_prefs[:2]:
            lines.append(f"- Préférence ({k}): {v['value']}")

        # ---------------- Location (conditionnel)
        if need_location:
            loc_item = self.data.get("location")
            if _is_item_dict(loc_item):
                lines.append(f"- Ville: {loc_item['value']}")
                
         # ---------------- Emotion (conditionnel)
        emotion = self.data.get("emotional_state")
        if isinstance(emotion, dict):
            score = self._score(emotion, half_life_days=7)
            if score > 0.2:
                lines.append(f"- État émotionnel récent: {emotion['value']}")


        # ---------------- Relations (conditionnel)
        if need_rel:
            rels = self.data.get("relations", {})
            if isinstance(rels, dict):
                scored = []
                for k, v in rels.items():
                    if _is_item_dict(v):
                        scored.append((self._score(v, half_life_days=365), k, v))
                for _, k, v in sorted(scored, reverse=True)[:3]:
                    lines.append(f"- Relation ({k}): {v['value']}")

        patterns = self.data.get("emotion_patterns", {})

        for domain, emos in patterns.items():
            if domain in hint:
                for emo, data in emos.items():
                    if data.get("count", 0) >= 3:
                        lines.append(
                            f"- Tendance émotionnelle: souvent {emo} quand il parle de {domain}"
                        )


        if not lines:
            return ""

        return "Mémoire utilisateur:\n" + "\n".join(lines)


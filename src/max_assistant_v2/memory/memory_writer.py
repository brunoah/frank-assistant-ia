import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class MemoryDecision:
    should_write: bool
    confidence: float
    memory_text: str
    tags: list[str]
    profile_patch: Dict[str, Any]

class MemoryWriter:
    """
    Demande au LLM s'il faut stocker un souvenir durable.
    Retourne une décision structurée (JSON).
    """

    def __init__(self, llm_client):
        self.llm = llm_client  # ton client LM Studio

    def decide(self, user_text: str, assistant_text: str, user_profile: Optional[dict] = None) -> MemoryDecision:
        profile_hint = ""
        if user_profile:
            # On garde léger : pas besoin de tout injecter
            profile_hint = json.dumps({
                "name": user_profile.get("name"),
                "projects": user_profile.get("projects", [])[:5],
                "preferences": user_profile.get("preferences", {}) if isinstance(user_profile.get("preferences", {}), dict) else {},
            }, ensure_ascii=False)

        system = (
            "Tu es un filtre de mémoire (memory writer) pour un assistant.\n"
            "Décide si l'on doit enregistrer une information DURABLE sur l'utilisateur.\n"
            "IMPORTANT:\n"
            "- NE JAMAIS créer/ajouter un 'projet' ou un fait nouveau si l'utilisateur pose une QUESTION.\n"
            "- NE PAS stocker de contenu éphémère (salutations, petites confirmations, demandes de rappel).\n"
            "- Stocker uniquement: préférences stables, identité, contraintes, projets explicitement annoncés, décisions durables.\n"
            "- Si tu n'es pas sûr, réponds should_write=false.\n"
            "Tu dois répondre UNIQUEMENT en JSON valide, sans texte autour.\n"
        )

        user = (
            f"Profil résumé: {profile_hint}\n\n"
            f"USER: {user_text}\n"
            f"ASSISTANT: {assistant_text}\n\n"
            "Réponds au format:\n"
            "{\n"
            '  "should_write": true|false,\n'
            '  "confidence": 0.0-1.0,\n'
            '  "memory_text": "texte court du souvenir à stocker (1-2 lignes, pas de dialogue)",\n'
            '  "tags": ["preference"|"project"|"identity"|"constraint"|"other"],\n'
            '  "profile_patch": { ... }  // ex: {"name":"Bruno"} ou {"projects":[{"name":"FRANK","note":"assistant IA local"}]}\n'
            "}\n"
        )

        # Appel LLM “froid” (important)
        raw = self.llm.chat_json(
            system_prompt=system,
            user_prompt=user,
            temperature=0.0,
            max_tokens=220,
        )

        # Parsing robuste
        try:
            data = json.loads(raw)
        except Exception:
            # Si le modèle dévie -> on stocke rien
            return MemoryDecision(False, 0.0, "", [], {})

        should = bool(data.get("should_write", False))
        conf = float(data.get("confidence", 0.0) or 0.0)
        mem = str(data.get("memory_text", "") or "").strip()
        tags = data.get("tags", []) or []
        patch = data.get("profile_patch", {}) or {}

        


        # garde-fous
        if not should or conf < 0.55 or not mem:
            return MemoryDecision(False, conf, "", [], {})

        # anti-boulette: si c'est manifestement une question, on bloque même si le LLM se trompe
        t = user_text.strip()
        if t.endswith("?"):
            return MemoryDecision(False, conf, "", [], {})

        
        user_clean = user_text.strip()

        if user_clean.endswith("?"):
            return MemoryDecision(False, conf, "", [], {})
    
            
        return MemoryDecision(True, conf, mem, list(tags), dict(patch))

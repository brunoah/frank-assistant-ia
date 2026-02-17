# src/max_assistant_v2/core/behavior_analyzer.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple

# Petit lexique FR simple (tu pourras enrichir)
URGENT_WORDS = [
    "urgent", "vite", "rapidement", "stp", "svp", "maintenant", "asap", "now",
]
FRUSTRATION_WORDS = [
    "ça marche pas", "ca marche pas", "ça fonctionne pas", "encore", "ras le bol",
    "j'en ai marre", "marre", "wtf", "bordel", "putain", "merde",
]
CONFUSION_WORDS = [
    "j'ai pas compris", "je ne comprends pas", "explique", "détaille", "detaille",
    "comment", "pourquoi", "c'est quoi", "je suis perdu", "ça veut dire quoi",
]
MOTIVATION_WORDS = [
    "let's go", "go", "on y va", "nickel", "parfait", "super", "génial", "genial",
]

TECH_HINTS = [
    "traceback", "error", "exception", "stack", "python", "pip", "venv", "import",
    "src/", "requirements", ".py", "json", "lm studio", "router", "orchestrator",
]


@dataclass
class BehaviorResult:
    emotion: Optional[str] = None
    intensity: float = 0.0          # 0..1
    mode: str = "calme"             # calme/focus/reflexion/erreur
    policy: Dict[str, Any] = None   # temperature/top_p/max_tokens/style


class BehaviorAnalyzer:
    """
    Analyse comportementale déterministe (pas LLM) :
    - Lit les signaux du message
    - Retourne un état (mode HUD), une émotion + intensité, et une policy de réponse
    """

    def __init__(self, profile_memory=None):
        self.profile = profile_memory

    def _contains_any(self, text: str, words: list[str]) -> bool:
        t = (text or "").lower()
        return any(w in t for w in words)

    def _punctuation_score(self, text: str) -> float:
        t = text or ""
        ex = t.count("!")
        qu = t.count("?")
        multi_q = 1 if qu >= 2 else 0
        caps = 1 if len(re.findall(r"\b[A-Z]{4,}\b", t)) > 0 else 0
        # score plafonné
        score = min(1.0, 0.10 * ex + 0.12 * qu + 0.25 * multi_q + 0.25 * caps)
        return score

    def _tech_score(self, text: str) -> float:
        t = (text or "").lower()
        score = 0.0
        for h in TECH_HINTS:
            if h in t:
                score += 0.12
        return min(1.0, score)

    def analyze(self, user_text: str, last_error: Optional[str] = None) -> BehaviorResult:
        t = (user_text or "").strip()
        low = t.lower()

        urgent = self._contains_any(low, URGENT_WORDS)
        frustr = self._contains_any(low, FRUSTRATION_WORDS)
        confus = self._contains_any(low, CONFUSION_WORDS)
        motiv = self._contains_any(low, MOTIVATION_WORDS)

        pscore = self._punctuation_score(t)
        tscore = self._tech_score(t)

        # intensité de base = mix punctuation + densité
        intensity = min(1.0, 0.25 + 0.55 * pscore + 0.35 * tscore)

        # Si on vient d’avoir une erreur out-of-band (planner/tool), ça pèse fort
        if last_error:
            intensity = min(1.0, max(intensity, 0.75))

        emotion = None
        mode = "calme"

        # =========================
        # Décision priorisée
        # =========================

        # 1️⃣ ERREUR (priorité absolue)
        if last_error:
            emotion = "frustré"
            mode = "erreur"
            intensity = max(intensity, 0.8)

        # 2️⃣ FRUSTRATION
        elif frustr:
            emotion = "frustré"
            mode = "focus"
            intensity = min(1.0, intensity + 0.2)

        # 3️⃣ URGENCE
        elif urgent:
            emotion = "stressé"
            mode = "focus"
            intensity = min(1.0, intensity + 0.15)

        # 4️⃣ CONTENU TECHNIQUE DENSE
        elif tscore > 0.35:
            emotion = None
            mode = "focus"

        # 5️⃣ CONFUSION (plus faible priorité)
        elif confus:
            emotion = "fatigué"
            mode = "reflexion"

        # 6️⃣ MOTIVATION
        elif motiv:
            emotion = "motivé"
            mode = "focus"

        else:
            emotion = None
            mode = "calme"


        # Policy de réponse (valeurs par défaut)
        temperature = 0.45
        top_p = 0.8
        max_tokens = 420

        if emotion == "fatigué":
            temperature = 0.2
            top_p = 0.45
            max_tokens = 160

        elif emotion == "stressé":
            temperature = 0.28
            top_p = 0.55
            max_tokens = 240

        elif emotion == "frustré":
            temperature = 0.35
            top_p = 0.70
            max_tokens = 360

        elif emotion == "motivé":
            temperature = 0.60
            top_p = 0.90
            max_tokens = 700

        # Ajustement en fonction de l’intensité
        max_tokens = int(max_tokens * (0.65 + 0.7 * (intensity or 0.3)))
        max_tokens = max(120, min(1200, max_tokens))

        policy = {
            "temperature": float(temperature),
            "top_p": float(top_p),
            "max_tokens": int(max_tokens),
            "mode": mode,
        }

        return BehaviorResult(
            emotion=emotion,
            intensity=float(intensity),
            mode=mode,
            policy=policy
        )

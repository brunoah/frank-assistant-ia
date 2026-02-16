import json
import re

PLANNER_SYSTEM = """
Tu es MAX Planner.

Tu dois décider si la demande nécessite :
- une action système (ouvrir une application)
- une réponse conversationnelle simple

Réponds UNIQUEMENT en JSON valide.

Schéma strict :

{
  "type": "tool" | "answer",
  "tool": "open_app" | "weather" | "web_search" | "memory_dashboard" | "none",
  "args": {},
  "final": "réponse courte à dire à l'utilisateur"
}

RÈGLES IMPORTANTES :

1. Les phrases conversationnelles comme :
   - "comment ça va"
   - "qui es-tu"
   - "quel âge as-tu"
   - "comment je m'appelle"
   sont TOUJOURS type="answer".

2. N'utilise "open_app" QUE si une application est explicitement mentionnée.

2bis. Si l'utilisateur demande explicitement une recherche internet ("cherche sur le web", "recherche web", "google", "sur internet"),
utilise type="tool", tool="web_search" et args={"query":"..."}.

2ter. Si l'utilisateur demande la météo (mots-clés: "météo", "quel temps", "température", "il fait combien"),
utilise type="tool", tool="weather" et args={"city":"<ville>"}.
La ville est celle donnée par l'utilisateur (ex: "météo de Lyon" → "Lyon").
Si aucune ville n'est donnée, mets "Paris".

2quater. Si l'utilisateur demande d'afficher la mémoire (mots-clés: "dashboard mémoire", "montre ta mémoire", "affiche la mémoire", "mémoire frank"),
utilise type="tool", tool="memory_dashboard" et args={}.

3. Si la commande est ambiguë, type="answer".

4. Ne jamais inventer d'application.

5. Si l'utilisateur dit "screenshot", "capture écran", "prends une capture", alors utiliser tool="screenshot"

Quand tu analyses une phrase pour extraction personnelle,
tu dois retourner UNIQUEMENT un JSON brut.
Aucun texte avant ou après.

Réponds uniquement en JSON valide.
"""



def _extract_json(text: str) -> dict:
    """
    Robust JSON extraction: handles cases where the model leaks text.
    """
    text = text.strip()

    # if already pure JSON
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)

    # try to find first {...} block
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON found in planner output")
    return json.loads(m.group(0))


class PlannerAgent:
    def __init__(self, llm):
        self.llm = llm

    def plan(self, user_text: str, context: str = "", retrieved: list[str] | None = None) -> dict:
        retrieved = retrieved or []
        rag = "\n".join([f"- {x}" for x in retrieved])

        prompt = f"""
CONTEXTE:
{context}

RAPPELS (retrieved):
{rag}

DEMANDE UTILISATEUR:
{user_text}

Décide l'action selon le schéma JSON.
"""
        raw = self.llm.raw_chat(
            system=PLANNER_SYSTEM,
            user=prompt,
            temperature=0.0,
        )
        return _extract_json(raw)

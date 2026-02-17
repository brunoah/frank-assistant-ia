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
  "tool": "open_app" | "weather" | "web_search" | "memory_dashboard" | "image_generate" | "none" | "camera_snapshot" | "camera_open_stream",
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

IMPORTANT :
Toujours utiliser :
args={"app_name":"nom_exact"}

Ne jamais utiliser "app".

2bis. Si l'utilisateur demande explicitement une recherche internet ("cherche sur le web", "recherche web", "google", "sur internet"),
utilise type="tool", tool="web_search" et args={"query":"..."}.

2ter. Si l'utilisateur demande la météo (mots-clés: "météo", "quel temps", "température", "il fait combien"),
utilise type="tool", tool="weather" et args={"city":"<ville>"}.
La ville est celle donnée par l'utilisateur (ex: "météo de Lyon" → "Lyon").
Si aucune ville n'est donnée, mets "Paris".

2quater. Si l'utilisateur demande d'afficher la mémoire (mots-clés: "dashboard mémoire", "montre ta mémoire", "affiche la mémoire", "mémoire frank"),
utilise type="tool", tool="memory_dashboard" et args={}.

2quinquies. Si l'utilisateur parle de rendez-vous, planning, agenda, réunion, événement :

2sexies. Si l'utilisateur demande la caméra (mots-clés: "caméra", "camera", "tapo", "flux", "stream", "montre la caméra"),
utilise type="tool", tool="camera_open_stream" et args={"camera":"tapo"}.

2septies. Si l'utilisateur demande une photo/snapshot (mots-clés: "snapshot", "photo", "capture caméra", "image de la caméra"),
utilise type="tool", tool="camera_snapshot" et args={"camera":"tapo"}.

2octies. Si l'utilisateur demande de générer/créer une image
(mots-clés: "génère une image", "crée une image", "fais une image", "dessine", "image de", "illustration"),
utilise type="tool", tool="image_generate" et args={"prompt":"<description complète>"}.

Utilise tool="agenda".

Pour ajouter :
args={
    "action": "add",
    "title": "<titre court>",
    "date": "<expression naturelle EXACTE extraite>",
    "time": "<heure EXACTE extraite>"
}

IMPORTANT :
- Ne calcule jamais la date.
- Ne convertis jamais en format YYYY-MM-DD.
- Garde les mots exacts comme "demain", "vendredi", "dans 2 jours".
- Si aucune heure n’est donnée, ne mets rien.
- Ne jamais inventer une date.

3. Si la commande est ambiguë, type="answer".

4. Ne jamais inventer d'application.

5. Si l'utilisateur dit "screenshot", "capture écran", "prends une capture", alors utiliser tool="screenshot"

Quand tu analyses une phrase pour extraction personnelle,
tu dois retourner UNIQUEMENT un JSON brut.
Aucun texte avant ou après.

Réponds uniquement en JSON valide.

Si l'utilisateur dit "surveillance extérieure",
retourne :
{
  "type": "tool",
  "tool": "camera_open_stream",
  "args": {"camera": "exterieure"}
}

Si l'utilisateur dit "surveillance intérieure",
retourne :
{
  "type": "tool",
  "tool": "camera_open_stream",
  "args": {"camera": "interieure"}
}
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

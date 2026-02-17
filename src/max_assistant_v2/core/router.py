import json
import re

from max_assistant_v2.agents.planner_agent import PlannerAgent
from max_assistant_v2.tools.tool_registry import ToolRegistry
from max_assistant_v2.tools.system_tools import SystemTools
from max_assistant_v2.tools.web_tools import WebTools
from max_assistant_v2.utils.logger import get_logger
from max_assistant_v2.memory.profile import ProfileMemory
from max_assistant_v2.core.project_manager import ProjectManager
from max_assistant_v2.tools.memory_dashboard_tool import open_memory_dashboard
from max_assistant_v2.core.behavior_analyzer import BehaviorAnalyzer

log = get_logger(__name__)


class Router:
    def __init__(self, llm):
        self.llm = llm
        self.planner = PlannerAgent(llm)
        self.profile = ProfileMemory()
        self.behavior = BehaviorAnalyzer(self.profile)
        self.profile.cleanup()
        self.tool_registry = ToolRegistry()
        self.sys = SystemTools(self.tool_registry)
        self.web = WebTools()

        # Enregistrement des tools dans le registry
        self.tool_registry.register("web_search", self.web.web_search)
        self.tool_registry.register("screenshot", self.sys.screenshot)
        self.tool_registry.register("weather", self.web.weather)
        self.tool_registry.register("memory_dashboard", open_memory_dashboard)
        
        self.projects = ProjectManager("data/projects.json")

    def detect_implicit_emotion(self, text: str):
        text = (text or "").lower()

        emotion_keywords = {
            "stressé": ["pression", "overload", "trop de travail", "j'en peux plus", "burnout"],
            "fatigué": ["épuisé", "crevé", "vidé", "hs"],
            "frustré": ["ça m'énerve", "injuste", "ras le bol"],
            "motivé": ["à fond", "déterminé", "let's go", "objectif"],
            "heureux": ["génial", "super", "trop content", "incroyable"],
        }

        intensifiers = {
            "très": 0.2,
            "vraiment": 0.2,
            "extrêmement": 0.3,
            "un peu": -0.2,
        }

        detected_emotion = None
        base_intensity = 0.6

        for emotion, words in emotion_keywords.items():
            for w in words:
                if w in text:
                    detected_emotion = emotion
                    break
            if detected_emotion:
                break

        if not detected_emotion:
            return None, 0.0

        # ajustement intensité
        for word, delta in intensifiers.items():
            if word in text:
                base_intensity += delta

        base_intensity = max(0.2, min(1.0, base_intensity))

        return detected_emotion, base_intensity

    def extract_personal_info(self, user_text: str):
        prompt = f"""
Tu es un module d'extraction de mémoire personnelle.

Analyse la phrase suivante.

Si elle contient une information personnelle durable concernant l'utilisateur,
retourne STRICTEMENT un JSON valide avec ce format EXACT :

{{
  "type": "name | location | relation | project | preference | none",
  "key": "string",
  "value": "string"
}}

Si aucune information personnelle durable n'est détectée,
retourne EXACTEMENT :

{{
  "type": "none",
  "key": "",
  "value": ""
}}

Si la phrase contient une émotion exprimée par l'utilisateur
(ex: je suis stressé, fatigué, motivé, frustré, heureux, etc.)
retourne :
{{
  "type": "emotion",
  "key": "",
  "value": "emotion_detected"
}}


Phrase :
\"\"\"{user_text}\"\"\"
"""

        result = self.llm.chat(prompt)

        # parsing robuste (le modèle peut ajouter du texte)
        try:
            m = re.search(r"\{.*\}", result, re.DOTALL)
            if m:
                return json.loads(m.group(0))
        except Exception:
            log.warning(f"Extraction JSON failed. RAW={result!r}")

        return {"type": "none", "key": "", "value": ""}

    def handle(self, user_text: str, context: str, retrieved: list[str], state_cb=None) -> str:
        txt = (user_text or "").strip()

        low = txt.lower()

        # =========================
        # 0) Analyse comportementale (déterministe)
        # =========================
        beh = self.behavior.analyze(txt, last_error=None)
      
        # 🔥 METTRE ICI
        if beh.emotion == "frustré":
            self.profile.bump_metric("frustration_hits", 1)

        if beh.emotion == "stressé":
            self.profile.bump_metric("urgent_hits", 1)

        if state_cb:
            state_cb(beh.mode, 0.7)

        # On pousse dans la mémoire émotionnelle existante
        if beh.emotion:
            self.profile.set_emotion(beh.emotion, beh.intensity)
            self.profile.update_emotion_pattern(txt, beh.emotion)

        # =========================
        # Metrics comportementales durables
        # =========================
        if beh.mode:
            self.profile.set_last_mode(beh.mode)  

        
                
        ut = low

        if re.search(r"\b(crée|creer|créer|créer un|creer un|crée un)\b.*\bprojet\b", user_text.lower()):

            text = user_text.lower()

            # Supprime la commande principale
            title_part = user_text.split("projet", 1)[1].strip()

            title = title_part
            theme = ""
            description = ""

            # Extraction thème : "sur ..."
            if " sur " in title_part.lower():
                parts = title_part.split(" sur ", 1)
                title = parts[0].strip()
                rest = parts[1]

                # Si "qui" dans la suite → thème + description
                if " qui " in rest:
                    theme, description = rest.split(" qui ", 1)
                    theme = theme.strip()
                    description = description.strip()
                else:
                    theme = rest.strip()

            # Extraction description si "qui est" direct
            elif " qui " in title_part.lower():
                title, description = title_part.split(" qui ", 1)
                title = title.strip()
                description = description.strip()

            try:
                p = self.projects.add_project(
                    title=title,
                    description=description,
                    theme=theme
                )
                return f"Projet ajouté : {p['title']}"
            except Exception as e:
                return f"Erreur : {e}"

        # ACTIVER PROJET
        if re.search(r"\b(active|travaille)\b.*\bprojet\b", ut):

            parts = re.split(r"\bprojet\b", user_text, flags=re.IGNORECASE)
            if len(parts) < 2:
                return "Quel projet dois-je activer ?"

            title = parts[1].strip()

            p = self.projects.find_by_title(title)

            if not p:
                return "Projet introuvable."

            self.projects.set_current_project(p["id"])
            return f"Projet actif : {p['title']}"

        if "projet courant" in ut or "projet actif" in ut:
            p = self.projects.get_current_project()
            if not p:
                return "Aucun projet actif."
            return f"Projet actuel : {p['title']} (thème : {p.get('theme') or '—'})"
        
        # =========================
        # MODIFICATION DESCRIPTION
        # =========================
        if re.search(r"\b(description|décris|ajoute une description)\b", ut):

            for p in self.projects.list_projects():
                if p["title"].lower() in ut:

                    # On prend tout après le titre
                    desc = user_text.split(p["title"], 1)[1].strip()

                    self.projects.update_project(p["id"], "description", desc)
                    return f"Description mise à jour pour {p['title']}"

            return "Projet introuvable pour modification."

        # =========================
        # MODIFICATION THEME
        # =========================
        if "change le thème" in ut or "modifie le thème" in ut:

            for p in self.projects.list_projects():
                if p["title"].lower() in ut:

                    parts = re.split(r"\ben\b", user_text, maxsplit=1, flags=re.IGNORECASE)

                    if len(parts) < 2:
                        return "Quel est le nouveau thème ?"

                    new_theme = parts[1].strip()

                    self.projects.update_project(p["id"], "theme", new_theme)
                    return f"Thème mis à jour pour {p['title']}"

            return "Projet introuvable."

        # 🔥 Détection émotion implicite
        emotion_detected, intensity = self.detect_implicit_emotion(txt)

        if emotion_detected:
            self.profile.set_emotion(emotion_detected, intensity)
            self.profile.update_emotion_pattern(txt, emotion_detected)


        # -------------------------
        # 1) Réponses directes profil (prioritaires)
        # -------------------------
        clean = low.replace("m'appelle", "mappelle")

        if "comment je mappelle" in clean or "comment je m'appelle" in low:
            name = self.profile.get_name()
            return f"Tu t'appelles {name}." if name else "Je ne connais pas encore ton nom."

        # Déclaration simple (ultra fiable) sans LLM
        if "je mappelle" in clean and "comment" not in clean:
            name = clean.split("mappelle")[-1].strip()
            name = name.replace("?", "").replace(".", "").strip()
            if len(name) >= 2:
                self.profile.set_name(name)
                return f"D'accord {name.capitalize()}, je m'en souviendrai."

        # -------------------------
        # 2) Extraction mémoire via LLM (auto)
        # -------------------------
        personal = self.extract_personal_info(txt)
        t = (personal.get("type") or "none").lower()
        key = (personal.get("key") or "").strip()
        value = (personal.get("value") or "").strip()

        if t != "none" and value:
            if t == "name":
                self.profile.set_name(value)
                return f"D'accord {value.capitalize()}, je m'en souviendrai."

            if t == "location":
                self.profile.set_location(value)
                return f"Très bien, tu habites à {value.capitalize()}."

            if t == "relation":
                # key attendu: "femme", "mari", "enfant", etc.
                rel = key.lower() if key else "proche"
                self.profile.set_relation(rel, value)
                return f"Je retiens que ton/ta {rel} s'appelle {value.capitalize()}."

            if t == "preference":

                val_low = value.lower()
                key_low = key.lower()

                # 🔥 NORMALISATION INTELLIGENTE
                if "court" in val_low:
                    self.profile.set_preference("style", "court", importance=0.9)

                elif "long" in val_low or "detail" in val_low:
                    self.profile.set_preference("style", "detaille", importance=0.9)

                elif key_low in ["réponse", "réponses", "style", "format"]:
                    self.profile.set_preference("style", val_low, importance=0.8)

                else:
                    self.profile.set_preference(key_low or "general", value, importance=0.7)

                return "Préférence enregistrée."


            if t == "emotion":
                self.profile.set_emotion(value)

                # 🔥 AJOUT ICI
                self.profile.update_emotion_pattern(txt, value)

                return "Je comprends comment tu te sens."



        # -------------------------
        # 3) Injection intelligente contexte (utilise importance + timestamp)
        # -------------------------
        profile_context = self.profile.build_context(hint_text=txt)
        if profile_context:
            context = profile_context + "\n\n" + (context or "")


        ut = (user_text or "").strip()

        # LISTE
        if re.match(r"^(liste|liste-moi|affiche).*(projets?)", ut.lower()):
            projs = self.projects.list_projects()
            if not projs:
                return "Aucun projet enregistré."
            lines = [f"- {p['title']} (id: {p['id']}) — thème: {p.get('theme') or '—'}" for p in projs]
            return "Projets :\n" + "\n".join(lines)

        # RECHERCHE
        m = re.match(r"^recherche\s+(.*)", ut.lower())
        if m:
            q = ut.split(" ", 1)[1].strip()
            results = self.projects.search(q)
            if not results:
                return f"Aucun résultat pour : {q}"
            lines = [f"- {p['title']} (id: {p['id']}) — thème: {p.get('theme') or '—'}" for p in results]
            return "Résultats :\n" + "\n".join(lines)

        # =========================
        # SUPPRESSION PROJET
        # =========================
        if re.search(r"\b(sup+?r?i?m?e?)\b.*\bprojet\b", ut):

            # Cas spécial : projet actif
            if "actif" in ut:
                current = self.projects.get_current_project()
                if not current:
                    return "Aucun projet actif à supprimer."

                self.projects.delete_project(current["id"])
                self.projects.set_current_project(None)
                return f"Projet supprimé : {current['title']}"

            # Sinon suppression par titre
            parts = re.split(r"\bprojet\b", user_text, flags=re.IGNORECASE)
            if len(parts) < 2:
                return "Quel projet dois-je supprimer ?"

            target = parts[1].strip()

            # Suppression par ID si ça ressemble à un uuid
            if re.match(r"^[0-9a-fA-F-]{20,}$", target):
                deleted = self.projects.delete_project(target)
                return "Projet supprimé." if deleted else "Projet introuvable."

            # Suppression par titre
            p = self.projects.find_by_title(target)
            if not p:
                return "Projet introuvable."

            self.projects.delete_project(p["id"])

            # Si c'était le projet actif → on le reset
            current = self.projects.get_current_project()
            if current and current["id"] == p["id"]:
                self.projects.set_current_project(None)

            return f"Projet supprimé : {p['title']}"


        # -------------------------
        # 4) Planner / Tools / Answer
        # -------------------------
        try:
            plan = self.planner.plan(user_text=txt, context=context, retrieved=retrieved)
            print("🧠 PLAN:", plan)
        except Exception as e:
            
            log.error(f"Planner JSON error: {e}")
            return self.llm.chat(user_text=txt, context=context, retrieved=retrieved)

        ptype = (plan.get("type") or "answer").lower()
        tool = (plan.get("tool") or "none").lower()
        args = plan.get("args") or {}
        final = (plan.get("final") or "").strip()

        # Tools
        if ptype == "tool":

            

            result = self.tool_registry.execute(
                tool,
                **args
            )

            # 🔹 Screenshot → réponse directe (pas de LLM)
            if tool == "screenshot":
                return result

            # 🔹 Web search → synthèse
            if tool == "web_search":
                return self.llm.chat(
                    f"""
        Tu es FRANK, assistant technique.

        Voici des informations récupérées via une recherche web :

        {result}

        Ta tâche :
        - Synthétise ces informations
        - Supprime les doublons
        - Structure clairement la réponse
        - Donne une réponse claire et exploitable
        """,
                    context="",
                    retrieved=[],
                    temperature=0.4,
                    max_tokens=600,
                    top_p=0.8
                )

            # 🔹 Par défaut → retourne résultat brut
            return result

        # Answer

        temperature = 0.5
        top_p = 0.8
        max_tokens = 400

        emotion_value, intensity = self.profile.get_emotion()

        # =========================
        # Override soft via BehaviorAnalyzer
        # (si son intensité est forte, on priorise)
        # =========================
        if beh and (beh.intensity >= 0.65):
            temperature = beh.policy.get("temperature", temperature)
            top_p = beh.policy.get("top_p", top_p)
            max_tokens = beh.policy.get("max_tokens", max_tokens)


        # Normalisation robuste
        if emotion_value:
            emotion_value = emotion_value.lower().strip()

            if emotion_value.startswith("stress"):
                emotion_value = "stressé"
            elif emotion_value.startswith("fatigu"):
                emotion_value = "fatigué"
            elif emotion_value.startswith("frustr"):
                emotion_value = "frustré"
            elif emotion_value.startswith("motiv"):
                emotion_value = "motivé"

            self.profile.update_emotion_pattern(txt, emotion_value)

        if emotion_value == "fatigué":
            temperature = 0.2
            top_p = 0.4
            max_tokens = 120

        elif emotion_value == "stressé":
            temperature = 0.3
            top_p = 0.5
            max_tokens = 200

        elif emotion_value == "frustré":
            temperature = 0.4
            top_p = 0.7
            max_tokens = 350

        elif emotion_value == "motivé":
            temperature = 0.6 + (0.3 * (intensity or 0.5))
            top_p = 0.9
            max_tokens = 700

        max_tokens = int(max_tokens * (0.6 + intensity))    

        # -------------------------
        # B) Ajustement selon préférence utilisateur
        # -------------------------

        pref_style = (self.profile.get_preference("style") or
                      self.profile.get_preference("response_style") or "").lower()

        if pref_style == "court":
            max_tokens = int(max_tokens * 0.6)
            temperature = min(temperature, 0.45)

        elif pref_style in ["détaillé", "detaille", "long"]:
            max_tokens = int(max_tokens * 1.4)
            temperature = max(temperature, 0.5)

   
        if state_cb:
            state_cb("calme", 0.3)
        
        if ptype == "answer":
            if final:
                return final
            return self.llm.chat(
                user_text=txt,
                context=context,
                retrieved=retrieved,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )
            

        return self.llm.chat(
            user_text=txt,
            context=context,
            retrieved=retrieved,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )


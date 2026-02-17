# src/max_assistant_v2/core/orchestrator.py
from max_assistant_v2.config.settings import settings
from max_assistant_v2.stt.whisper_engine import WhisperSTT
from max_assistant_v2.tts.piper_engine import PiperTTS
from max_assistant_v2.llm.lmstudio_client import LMStudioClient
from max_assistant_v2.core.router import Router
from max_assistant_v2.memory.short_term import ShortTermMemory
from max_assistant_v2.memory.long_term import LongTermMemory
from max_assistant_v2.memory.vector_store import VectorStore
from max_assistant_v2.memory.embeddings import Embeddings
from max_assistant_v2.utils.logger import get_logger
from max_assistant_v2.ui.hud import SpeakingHUD
from datetime import datetime, timezone
from max_assistant_v2.memory.memory_writer import MemoryWriter
from max_assistant_v2.tools.tool_registry import ToolRegistry
from max_assistant_v2.tools.system_tools import SystemTools
from max_assistant_v2.ui.console_hud import ConsoleStateHUD
from max_assistant_v2.memory.profile import ProfileMemory

log = get_logger(__name__)

class Orchestrator:
    def __init__(self, hud: SpeakingHUD | None = None):
        self.stt = WhisperSTT()
        self.tts = PiperTTS(piper_exe=settings.PIPER_EXE, piper_model=settings.PIPER_MODEL)
        self.llm = LMStudioClient(base_url=settings.LM_BASE_URL, model_id=settings.MODEL_ID)

        self.memory_writer = MemoryWriter(self.llm)

        self.short_mem = ShortTermMemory(max_turns=12)
        self.long_mem = LongTermMemory(path=settings.LONG_TERM_PATH)
        self.profile = ProfileMemory()

        self.embed = Embeddings()
        self.vstore = VectorStore(dir_path=settings.VECTOR_DIR, embeddings=self.embed)

        self.tool_registry = ToolRegistry()
        self.system_tools = SystemTools(self.tool_registry)
        self.console_hud = ConsoleStateHUD()

        self.router = Router(llm=self.llm)

        self.hud = hud 

    def record_user_emotion(self):

        emotion, intensity = self.router.profile.get_emotion()

        if not emotion:
            return

        if "emotion_history" not in self.profile.data:
            self.profile.data["emotion_history"] = []

        self.profile.data["emotion_history"].append({
            "emotion": emotion.upper(),
            "intensity": float(intensity),
            "timestamp": datetime.now().timestamp()
        })

        # limite historique
        self.profile.data["emotion_history"] = self.profile.data["emotion_history"][-200:]

        if hasattr(self.profile, "save"):
            self.profile.save()
    

    def render_emotion(self):
        emotion, intensity = self.router.profile.get_emotion()

        if not emotion:
            return

        bar_length = 12
        filled = int(bar_length * intensity)
        bar = "█" * filled + "·" * (bar_length - filled)

        print(f"\n🗣️ User État détecté : {emotion.upper()}")
        print(f"   Intensité : {bar} {intensity:.2f}\n")
    
    def run_forever(self):
        while True:

            self.console_hud.set_state("ecoute", 0.4)
            
            text = self.stt.listen_one_utterance(
                wake_word=settings.WAKE_WORD
            )
            if not text:
                continue

            # Stop phrase simple (tu pourras enrichir)
            if text.strip().lower() in {"quit frank", "stop frank", "au revoir frank", "frank quitte"}:
                self.tts.say("🔴 D'accord. Je m'arrête.")
                break

            print(f"🗣️ User: {text}")

            # -------------------------
            # FRANK entre en réflexion
            # -------------------------
            self.console_hud.set_state("reflexion", 0.6)
          
        
            # RAG (mémoire perso) : pas utile sur des messages trop courts
            low = text.strip().lower()
            if len(low) < 6 or low in {"ok", "oui", "non", "merci", "d'accord", "ça marche"}:
                retrieved_items = []
            else:
                retrieved_items = self.vstore.search(
                    text,
                    k=settings.RAG_TOP_K,
                    min_score=settings.RAG_MIN_SCORE
                )

            def fmt_mem(it: dict) -> str:
                md = it.get("metadata", {}) or {}
                role = md.get("role", md.get("type", "mem"))
                ts = md.get("ts", "")
                score = it.get("score", 0.0)
                txt = it.get("text", "")
                return f"[{role} | {ts} | score={score:.2f}] {txt}".strip()

            # dédoublonnage simple
            seen = set()
            retrieved = []
            for it in retrieved_items:
                s = fmt_mem(it)
                if s not in seen:
                    seen.add(s)
                    retrieved.append(s)


            context = self.short_mem.render() + self.long_mem.render_last(n=12)

            response = self.router.handle(
                user_text=text,
                context=context,
                retrieved=retrieved
            )

            # Enregistrer émotion USER détectée
            self.record_user_emotion()

            # -------------------------
            # Réponse prête → FRANK calme
            # -------------------------
            self.console_hud.set_state("calme", 0.3)

            self.short_mem.add(user=text, assistant=response)
            self.long_mem.append(user=text, assistant=response)

            # ====================================
            # MEMORY WRITER (LLM GATING PROPRE)
            # ====================================

            ts = datetime.now(timezone.utc).isoformat()

            decision = self.memory_writer.decide(
                user_text=text,
                assistant_text=response,
                user_profile=None  # tu peux brancher ton profile plus tard
            )

            if decision.should_write:
                self.vstore.add(
                    decision.memory_text,
                    metadata={
                        "role": "memory",
                        "ts": ts,
                        "confidence": decision.confidence,
                        "tags": decision.tags,
                        "kind": "fact"
                    }
                )

            # ====================================
            # FIN MEMORY WRITER
            # ====================================

            

            if self.hud:
                self.hud.show()

            # --- Etat utilisateur stocké ---
            user_emotion, user_intensity = self.router.profile.get_emotion()

            print("🗣️ USER EMOTION:", user_emotion, user_intensity)
            
            self.tts.say(
                response,
                hud=self.hud,
                user_emotion=user_emotion,
                user_intensity=user_intensity
            )


            if self.hud:
                self.hud.hide()



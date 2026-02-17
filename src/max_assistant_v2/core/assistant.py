from max_assistant_v2.core.orchestrator import Orchestrator
from max_assistant_v2.utils.logger import get_logger
from max_assistant_v2.core.agenda_reminder import AgendaReminderService
from max_assistant_v2.tts.piper_engine import PiperTTS

log = get_logger(__name__)


class Assistant:
    def __init__(self, hud=None):
        self.hud = hud
        self.orchestrator = Orchestrator(hud=hud)

        self.piper = self.orchestrator.tts

        # 🔔 Reminder branché sur Piper
        self.reminder_service = AgendaReminderService(
            agenda_manager=self.orchestrator.tool_registry.agenda,
            speak_callback=self._reminder_speak
        )

        self.reminder_service.start()

    def _reminder_speak(self, text):
        print(f"🔔 RAPPEL: {text}")
        self.piper.say(text, hud=self.hud)

    def run(self):
        print("🤖 FRANK Assistant v2 prêt.")
        self.orchestrator.run_forever()

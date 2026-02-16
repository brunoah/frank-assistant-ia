# src/max_assistant_v2/core/assistant.py
from max_assistant_v2.core.orchestrator import Orchestrator
from max_assistant_v2.utils.logger import get_logger

log = get_logger(__name__)

class Assistant:
    def __init__(self, hud=None):
        self.orchestrator = Orchestrator(hud=hud)
        
    def run(self):
        print("🤖 FRANK Assistant v2 prêt.")
        self.orchestrator.run_forever()

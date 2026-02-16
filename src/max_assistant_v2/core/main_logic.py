# src/max_assistant_v2/core/main_logic.py

from max_assistant_v2.core.assistant import Assistant

def run_app(hud=None):
    assistant = Assistant(hud=hud)
    assistant.run()
# src/max_assistant_v2/memory/long_term.py
import json
import os
from datetime import datetime

class LongTermMemory:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            open(path, "a", encoding="utf-8").close()

    def append(self, user: str, assistant: str):
        item = {
            "ts": datetime.utcnow().isoformat(),
            "user": user,
            "assistant": assistant,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def render_last(self, n: int = 10) -> str:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-n:]
            if not lines:
                return ""
            out = ["--- Mémoire long terme récente ---"]
            for line in lines:
                j = json.loads(line)
                out.append(f"User: {j.get('user','')}")
                out.append(f"Assistant: {j.get('assistant','')}")
            out.append("--- Fin ---")
            return "\n".join(out) + "\n"
        except Exception:
            return ""

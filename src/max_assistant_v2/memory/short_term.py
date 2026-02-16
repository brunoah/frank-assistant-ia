# src/max_assistant_v2/memory/short_term.py
from collections import deque

class ShortTermMemory:
    def __init__(self, max_turns: int = 10):
        self.buffer = deque(maxlen=max_turns)

    def add(self, user: str, assistant: str):
        self.buffer.append((user, assistant))

    def render(self) -> str:
        if not self.buffer:
            return ""
        lines = ["--- Conversation récente ---"]
        for u, a in self.buffer:
            lines.append(f"User: {u}")
            lines.append(f"Assistant: {a}")
        lines.append("--- Fin ---")
        return "\n".join(lines) + "\n"

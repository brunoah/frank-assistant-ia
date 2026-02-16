# src/max_assistant_v2/ui/console_hud.py

import sys
import threading
import time
from random import randint


class ConsoleStateHUD:
    """
    HUD immersif console :
    FRANK
    STATE: FOCUS
    ██████░░░░
    """

    COLORS = {
        "calme": "\033[92m",        # vert doux
        "focus": "\033[94m",        # bleu
        "reflexion": "\033[93m",    # jaune
        "erreur": "\033[91m",       # rouge
        "reset": "\033[0m",
        "bold": "\033[1m"
    }

    def __init__(self):
        self.state = "calme"
        self.level = 0.3
        self.running = True
        self.lock = threading.Lock()


    def set_state(self, state: str, level: float = 0.3):
        self.state = state.lower()
        self.level = max(0.0, min(1.0, level))
        self._render()

    def stop(self):
        self.running = False

    # -------------------------

    def _build_bar(self):
        blocks = 10
        filled = int(self.level * blocks)
        empty = blocks - filled
        return "█" * filled + "░" * empty

    def _render(self):
        color = self.COLORS.get(self.state, self.COLORS["calme"])
        reset = self.COLORS["reset"]
        bold = self.COLORS["bold"]

        blocks = 10
        filled = int(self.level * blocks)
        bar = "█" * filled + "░" * (blocks - filled)

        output = (
            f"\n🤖 FRANK État détecté "
            f"{color}{self.state.upper()}{reset}\n"
            f"{color}{bar}{reset}\n"
        )

        print(output)


    def _loop(self):
        # imprime structure vide au démarrage
        print("\n\n")

        phase = 0

        while self.running:
            with self.lock:

                # animation légère selon état
                if self.state == "calme":
                    self.level = 0.3 + (0.05 if phase % 2 == 0 else -0.05)

                elif self.state == "reflexion":
                    self.level = abs((phase % 20) - 10) / 10

                elif self.state == "focus":
                    self.level = 0.6 if phase % 4 < 2 else 0.4

                elif self.state == "erreur":
                    self.level = 1.0
                    if phase % 4 == 0:
                        # petit effet glitch texte
                        self.state = "erreur" if randint(0, 1) else "err"

                self.level = max(0.0, min(1.0, self.level))

                self._render()

            phase += 1
            time.sleep(0.25)

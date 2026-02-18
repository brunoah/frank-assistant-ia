import os
import logging
import threading
from max_assistant_v2.web.server import app, attach_assistant
import uvicorn

from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / "data" / ".env"

load_dotenv(dotenv_path=env_path)
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

from max_assistant_v2.core.main_logic import run_app
from max_assistant_v2.ui.hud import SpeakingHUD


def main():

    hud = SpeakingHUD(gif_rel_path="assets/speaking.gif")

    # 1️⃣ Création Assistant via run_app
    from max_assistant_v2.core.assistant import Assistant

    assistant = Assistant(hud=hud)

    # 2️⃣ Attacher assistant au serveur web
    attach_assistant(assistant)

    # 3️⃣ Lancer serveur HTTPS en thread
    def start_web():
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            ssl_keyfile="src/max_assistant_v2/web/192.168.1.15-key.pem",
            ssl_certfile="src/max_assistant_v2/web/192.168.1.15.pem",
            log_level="info"
        )

    web_thread = threading.Thread(target=start_web, daemon=True)
    web_thread.start()

    # 4️⃣ Lancer FRANK desktop
    t = threading.Thread(target=assistant.run, daemon=True)
    t.start()

    hud.root.mainloop()



if __name__ == "__main__":
    main()

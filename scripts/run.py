import os
import logging
import threading

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

    t = threading.Thread(target=run_app, kwargs={"hud": hud}, daemon=True)
    t.start()

    hud.root.mainloop()


if __name__ == "__main__":
    main()

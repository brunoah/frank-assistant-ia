from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    # LM Studio
    LM_BASE_URL: str = "http://localhost:1234/v1"
    MODEL_ID: str = "typhoon2-qwen2.5-7b-instruct"

    # Audio
    SAMPLE_RATE: int = 16000
    WAKE_WORD: str = "FRANK"
    SILENCE_MS: int = 900
    FRAME_MS: int = 30

    # TTS Piper
    PIPER_EXE: str = r"D:\AI\PIPER\PIPER.EXE"
    PIPER_MODEL: str = r"D:\AI\PIPER\model\fr_FR-tom-medium.onnx"

    # Mémoire
    DATA_DIR: str = r"D:\AI\max_assistant_v2\data"
    LONG_TERM_PATH: str = r"D:\AI\max_assistant_v2\data\long_term.jsonl"
    VECTOR_DIR: str = r"D:\AI\max_assistant_v2\data\vector_store"

    # RAG - mémoire personnelle
    RAG_TOP_K: int = 6
    RAG_MIN_SCORE: float = 0.25  # à ajuster selon ton modèle d'embeddings


settings = Settings()

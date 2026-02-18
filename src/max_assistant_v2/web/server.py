from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from max_assistant_v2.core.assistant import Assistant
import uvicorn
import os
import tempfile
import soundfile as sf
import numpy as np
from scipy.signal import resample_poly
from fastapi import UploadFile, File, Form
import subprocess


API_TOKEN = os.getenv("FRANK_WEB_TOKEN", "frank-local-token")

app = FastAPI()
assistant = None

def attach_assistant(a):
    global assistant
    assistant = a

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    text: str
    token: str

@app.post("/ask")
def ask_frank(message: Message):

    if message.token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token invalide")

    result = assistant.process_text(message.text)
    return result

@app.post("/voice")
async def voice_input(
    file: UploadFile = File(...),
    token: str = Form(...)
):

    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Token invalide")

    # Sauvegarde brute (webm)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        content = await file.read()
        tmp.write(content)
        input_path = tmp.name

    # Convertir en wav 16k mono
    output_path = input_path.replace(".webm", ".wav")

    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        output_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Lire wav converti
    audio, rate = sf.read(output_path)

    audio = audio.astype(np.float32)

    text = assistant.orchestrator.stt.transcribe(audio)

    print("🧠 TRANSCRIPTION:", text)

    if not text:
        return {"status": "empty"}

    result = assistant.process_text(text)

    return result

@app.get("/health")
def health():
    return {"status": "FRANK ONLINE"}


def start():
    BASE_PATH = Path(__file__).resolve().parent

    cert_file = BASE_PATH / "192.168.1.15.pem"
    key_file = BASE_PATH / "192.168.1.15-key.pem"

    uvicorn.run(
        "max_assistant_v2.web.server:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile=str(key_file),
        ssl_certfile=str(cert_file),
        reload=False
    )


if __name__ == "__main__":
    start()

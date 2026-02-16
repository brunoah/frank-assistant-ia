# src/max_assistant_v2/tts/piper_engine.py
import subprocess
import tempfile
import os
import sounddevice as sd
import numpy as np
import wave

class PiperTTS:
    def __init__(self, piper_exe: str, piper_model: str):
        self.piper_exe = piper_exe
        self.piper_model = piper_model

    def say(self, text: str, hud=None):

        print(f"\n🟢 FRANK: {text}\n")

        if not text.strip():
            return

        with tempfile.TemporaryDirectory() as td:
            out_wav = os.path.join(td, "out.wav")
            cmd = [self.piper_exe, "-m", self.piper_model, "-f", out_wav]

            subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            with wave.open(out_wav, "rb") as wf:
                sr = wf.getframerate()
                total_frames = wf.getnframes()

                chunk = 1024

                stream = sd.OutputStream(
                    samplerate=sr,
                    channels=1,
                    dtype="int16"
                )

                stream.start()

                while True:
                    data = wf.readframes(chunk)
                    if not data:
                        break

                    audio_chunk = np.frombuffer(data, dtype=np.int16)

                    # 🔥 RMS pour pulse
                    if hud:
                        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2)) / 32768.0
                        hud.set_volume(rms)

                    stream.write(audio_chunk)

                stream.stop()
                stream.close()

            if hud:
                hud.set_volume(0.0)


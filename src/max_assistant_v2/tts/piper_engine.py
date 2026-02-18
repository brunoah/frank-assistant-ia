# src/max_assistant_v2/tts/piper_engine.py
import subprocess
import tempfile
import os
import sounddevice as sd
import numpy as np
import wave
import random

class PiperTTS:
    def __init__(self, piper_exe: str, piper_model: str):
        self.piper_exe = piper_exe
        self.piper_model = piper_model

    def _voice_from_user_state(self, emotion: str | None, intensity: float = 0.0):

        if not emotion:
            return 1.0, 1.0

        emotion = emotion.lower()

        # vitesse, volume
        profiles = {
            "fatigué": (0.97, 0.90),
            "stressé": (0.98, 0.95),
            "frustré": (0.99, 0.97),
            "motivé": (1.02, 1.0),
            "heureux": (1.03, 1.0),
            "neutre": (1.0, 1.0),
        }

        speed, gain = profiles.get(emotion, (1.0, 1.0))

        # modulation douce par intensité
        speed = speed + (0.05 * intensity if speed > 1 else -0.05 * intensity)

        return speed, gain

    def _apply_micro_variation(self, speed: float, gain: float):
        """
        Applique de très légères variations naturelles
        pour éviter une voix trop mécanique.
        """

        # variation vitesse ±1.5%
        speed_variation = random.uniform(-0.015, 0.015)

        # variation volume ±3%
        gain_variation = random.uniform(-0.03, 0.03)

        speed = speed + speed_variation
        gain = gain + gain_variation

        # limites de sécurité
        speed = max(0.96, min(1.04, speed))
        gain = max(0.85, min(1.10, gain))

        return speed, gain

    def _naturalize_text(self, text: str, user_emotion=None):
        """
        Ajoute de micro-pauses naturelles selon l'état.
        """

        if not text:
            return text

        # Pause légère après virgules
        text = text.replace(",", ", ")

        # Fatigué → phrases plus respirées
        if user_emotion == "fatigué":
            text = text.replace(".", "... ")

        # Stressé → micro pause avant infos importantes
        if user_emotion == "stressé":
            text = text.replace(":", " : ")

        return text


    def say(self, text: str, hud=None, user_emotion=None, user_intensity=0.0):

        # --- Micro naturalisation texte ---
        text = self._naturalize_text(text, user_emotion)

        print(f"\n🟢 {text}\n")

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
                speed_factor, gain = self._voice_from_user_state(user_emotion, user_intensity)
                # --- Micro variations naturelles ---
                speed_factor, gain = self._apply_micro_variation(speed_factor, gain)
                out_sr = int(sr * speed_factor)
                total_frames = wf.getnframes()

                chunk = 1024

                stream = sd.OutputStream(
                    samplerate=out_sr,
                    channels=1,
                    dtype="int16"
                )

                stream.start()

                while True:
                    data = wf.readframes(chunk)
                    if not data:
                        break

                    audio_chunk = np.frombuffer(data, dtype=np.int16)

                    if gain != 1.0:
                        x = audio_chunk.astype(np.float32) * gain
                        x = np.clip(x, -32768, 32767)
                        audio_chunk = x.astype(np.int16)


                    # 🔥 RMS pour pulse
                    if hud:
                        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2)) / 32768.0
                        hud.set_volume(rms)

                    stream.write(audio_chunk)

                stream.stop()
                stream.close()

            if hud:
                hud.set_volume(0.0)


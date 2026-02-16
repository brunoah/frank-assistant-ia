import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
from scipy.signal import resample_poly
import time


class WhisperSTT:
    def __init__(self):
        self.model = WhisperModel(
            "small",
            device="cuda",
            compute_type="int8"
        )

        self.input_rate = 48000
        self.target_rate = 16000

        # Auto-détection micro TONOR
        self.device_index = None
        for i, dev in enumerate(sd.query_devices()):
            if "TONOR" in dev["name"] and dev["max_input_channels"] > 0:
                self.device_index = i
                print(f"🎤 Micro détecté: {dev['name']} (index {i})")
                break

        if self.device_index is None:
            self.device_index = sd.default.device[0]
            print("⚠️ TONOR non trouvé, micro par défaut utilisé.")

    def transcribe(self, audio):
        segments, _ = self.model.transcribe(
            audio,
            language="fr",
            beam_size=5,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=False,
        )
        return " ".join([s.text.strip() for s in segments]).strip()

    def listen_one_utterance(self, wake_word="max"):

        wake_word = wake_word.lower()
        print("👂 En écoute...")

        state = "IDLE"

        wake_buffer = []
        command_buffer = []

        silence_start = None
        last_wake_test = 0

        # Réglages stables
        block_duration = 0.04          # 40ms
        wake_window_sec = 1.5          # 1.5s contexte wake
        silence_threshold_sec = 0.9    # 0.9s silence commande

        wake_chunks_needed = int(wake_window_sec / block_duration)

        def callback(indata, frames, time_info, status):
            nonlocal state, wake_buffer, command_buffer, silence_start

            audio = indata.flatten().astype(np.float32) / 32768.0
            rms = np.sqrt(np.mean(audio ** 2))

            if state == "IDLE":
                wake_buffer.append(audio.copy())

                if len(wake_buffer) > wake_chunks_needed:
                    wake_buffer = wake_buffer[-wake_chunks_needed:]

            elif state == "LISTENING":
                command_buffer.append(audio.copy())

                if rms > 0.025:
                    silence_start = None
                else:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > silence_threshold_sec:
                        raise sd.CallbackStop()

        with sd.InputStream(
            device=self.device_index,
            samplerate=self.input_rate,
            channels=1,
            dtype="int16",
            callback=callback,
            blocksize=int(self.input_rate * block_duration),
        ):

            while True:

                sd.sleep(100)

                # -------- WAKE DETECTION (hors callback) --------
                if state == "IDLE" and len(wake_buffer) >= wake_chunks_needed:

                    # Cooldown pour éviter spam Whisper
                    if time.time() - last_wake_test < 0.6:
                        continue

                    last_wake_test = time.time()

                    short_audio = np.concatenate(wake_buffer)
                    short_resampled = resample_poly(
                        short_audio,
                        self.target_rate,
                        self.input_rate
                    )

                    rms = np.sqrt(np.mean(short_resampled ** 2))

                    # Ignore quasi-silence
                    if rms < 0.03:
                        continue


                    text = self.transcribe(short_resampled)

                    if len(text.split()) > 5:
                        continue

                    wake_variants = ["frank", "franck", "franc", "fran", "franq"]

                    transcript = text.lower()

                    if any(w in transcript for w in wake_variants):
                        print("🟢 Wake détecté")
                        state = "LISTENING"
                        wake_buffer = []
                        command_buffer = []
                        silence_start = None

                # -------- STOP COMMANDE --------
                if state == "LISTENING" and silence_start is not None:
                    if time.time() - silence_start > silence_threshold_sec:
                        break

        if not command_buffer:
            return None

        full_audio = np.concatenate(command_buffer)
        audio_resampled = resample_poly(
            full_audio,
            self.target_rate,
            self.input_rate
        )

        # Normalisation
        rms = np.sqrt(np.mean(audio_resampled ** 2))
        if rms > 0:
            audio_resampled = audio_resampled / rms * 0.1

        command = self.transcribe(audio_resampled)

        print("🧠 COMMANDE:", command)

        return command

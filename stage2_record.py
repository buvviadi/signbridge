import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

sd.default.device = 1   # your Realtek mic; try 7 if 1 doesn't work

SR = 16000          # Whisper expects 16 kHz audio
SECONDS = 5

print("Loading model (English-only 'base.en')...")
model = WhisperModel("base.en", device="cpu", compute_type="int8")

input("Press Enter, then speak for 5 seconds...")
print("Recording...")
audio = sd.rec(int(SECONDS * SR), samplerate=SR, channels=1, dtype="float32")
sd.wait()
audio = audio[:, 0]   # flatten to 1-D

print(f"Loudest level: {np.abs(audio).max():.3f}  (should be well above 0.01)")

print("Transcribing...")
segments, info = model.transcribe(audio, language="en", beam_size=1)
text = " ".join(s.text.strip() for s in segments)
print("You said:", text)
import sounddevice as sd
from faster_whisper import WhisperModel

print("Audio input devices:")
for i, d in enumerate(sd.query_devices()):
    if d["max_input_channels"] > 0:
        print(f"  [{i}] {d['name']}")

print("\nLoading Whisper 'base' model (first run downloads ~150 MB)...")
model = WhisperModel("base", device="cpu", compute_type="int8")
print("Model loaded OK")
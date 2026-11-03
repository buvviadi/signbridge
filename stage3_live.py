import queue
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

sd.default.device = 1        # same mic that worked in Stage 2

SR = 16000
BLOCK_SEC = 0.03
BLOCK = int(BLOCK_SEC * SR)  # 30 ms per block
SILENCE_END = 0.7            # seconds of quiet that ends a sentence
MAX_UTTERANCE = 10.0         # force a cut after this many seconds
MIN_UTTERANCE = 0.4          # ignore clicks/bumps shorter than this

print("Loading model (base.en)...")
model = WhisperModel("base.en", device="cpu", compute_type="int8")

audio_q = queue.Queue()

def callback(indata, frames, time, status):
    audio_q.put(indata[:, 0].copy())

def rms(x):
    return float(np.sqrt(np.mean(x ** 2)))

def transcribe(audio):
    segments, _ = model.transcribe(
        audio, language="en", beam_size=1, vad_filter=True
    )
    return " ".join(s.text.strip() for s in segments).strip()

def main():
    with sd.InputStream(samplerate=SR, channels=1, blocksize=BLOCK,
                        dtype="float32", callback=callback):
        # 1) Calibrate: stay quiet for 1 second
        print("Calibrating room noise, stay quiet for 1 second...")
        noise = [rms(audio_q.get()) for _ in range(int(1.0 / BLOCK_SEC))]
        threshold = max(0.01, float(np.mean(noise)) * 3)
        print(f"Noise floor: {np.mean(noise):.4f} -> speech threshold: {threshold:.4f}")

        # 2) Listen loop
        print("\nListening... speak a sentence, then pause. (Ctrl+C to stop)\n")
        buf, silent_blocks, speaking = [], 0, False
        silence_limit = int(SILENCE_END / BLOCK_SEC)

        while True:
            block = audio_q.get()
            loud = rms(block) > threshold

            if loud:
                speaking, silent_blocks = True, 0
            elif speaking:
                silent_blocks += 1

            if speaking:
                buf.append(block)

            duration = len(buf) * BLOCK_SEC
            if speaking and (silent_blocks > silence_limit or duration > MAX_UTTERANCE):
                if duration >= MIN_UTTERANCE:
                    text = transcribe(np.concatenate(buf))
                    if text:
                        print("You said:", text)
                buf, silent_blocks, speaking = [], 0, False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
import csv
import os
import queue
import time
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from gloss import gloss_string

sd.default.device = 1        # same mic as before

SR = 16000
BLOCK_SEC = 0.03
BLOCK = int(BLOCK_SEC * SR)
SILENCE_END = 0.7
MAX_UTTERANCE = 10.0
MIN_UTTERANCE = 0.4
LOG_FILE = "results.csv"

print("Loading model (base.en)...")
model = WhisperModel("base.en", device="cpu", compute_type="int8")

audio_q = queue.Queue()

def callback(indata, frames, time_info, status):
    audio_q.put(indata[:, 0].copy())

def rms(x):
    return float(np.sqrt(np.mean(x ** 2)))

def transcribe(audio):
    segments, _ = model.transcribe(
        audio, language="en", beam_size=1, vad_filter=True
    )
    return " ".join(s.text.strip() for s in segments).strip()

def log_row(text, gloss, asr_ms, gloss_ms):
    new_file = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["transcript", "gloss", "asr_ms", "gloss_ms"])
        w.writerow([text, gloss, f"{asr_ms:.0f}", f"{gloss_ms:.2f}"])

def main():
    with sd.InputStream(samplerate=SR, channels=1, blocksize=BLOCK,
                        dtype="float32", callback=callback):
        print("Calibrating room noise, stay quiet for 1 second...")
        noise = [rms(audio_q.get()) for _ in range(int(1.0 / BLOCK_SEC))]
        threshold = max(0.01, float(np.mean(noise)) * 3)
        print(f"Noise floor: {np.mean(noise):.4f} -> threshold: {threshold:.4f}")
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
                    t0 = time.perf_counter()
                    text = transcribe(np.concatenate(buf))
                    t1 = time.perf_counter()
                    if text:
                        gloss = gloss_string(text)
                        t2 = time.perf_counter()
                        print(f"Heard : {text}")
                        print(f"Gloss : {gloss}")
                        print(f"        (ASR {1000*(t1-t0):.0f} ms, gloss {1000*(t2-t1):.2f} ms)\n")
                        log_row(text, gloss, 1000 * (t1 - t0), 1000 * (t2 - t1))
                buf, silent_blocks, speaking = [], 0, False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped. Results saved in results.csv")
import asyncio
import json
import queue
import threading
import time
from contextlib import asynccontextmanager

import numpy as np
import sounddevice as sd
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from faster_whisper import WhisperModel

from gloss import text_to_gloss

sd.default.device = 1        # same mic as before

SR = 16000
BLOCK_SEC = 0.03
BLOCK = int(BLOCK_SEC * SR)
SILENCE_END = 0.7
MAX_UTTERANCE = 10.0
MIN_UTTERANCE = 0.4

clients = set()
loop = None
mic_status = "Starting microphone and speech model..."

async def broadcast(msg):
    for ws in list(clients):
        try:
            await ws.send_text(json.dumps(msg))
        except Exception:
            clients.discard(ws)

def send(msg):
    if loop is not None:
        asyncio.run_coroutine_threadsafe(broadcast(msg), loop)

def update_mic_status(text):
    global mic_status
    mic_status = text
    send({"type": "status", "text": text})

def rms(x):
    return float(np.sqrt(np.mean(x ** 2)))

def _run_microphone():
    print("Loading Whisper model (base.en)...")
    update_mic_status("Loading Whisper model...")
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    audio_q = queue.Queue()

    def callback(indata, frames, time_info, status):
        audio_q.put(indata[:, 0].copy())

    with sd.InputStream(samplerate=SR, channels=1, blocksize=BLOCK,
                        dtype="float32", callback=callback):
        print("Calibrating room noise, stay quiet for 1 second...")
        noise = [rms(audio_q.get()) for _ in range(int(1.0 / BLOCK_SEC))]
        threshold = max(0.01, float(np.mean(noise)) * 3)
        print(f"Threshold {threshold:.4f}. READY - open http://127.0.0.1:8000")
        update_mic_status("Listening...")

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
                    segments, _ = model.transcribe(
                        np.concatenate(buf), language="en",
                        beam_size=1, vad_filter=True)
                    text = " ".join(s.text.strip() for s in segments).strip()
                    asr_ms = 1000 * (time.perf_counter() - t0)
                    if text:
                        tokens = text_to_gloss(text)
                        print(f"Heard: {text}  ({asr_ms:.0f} ms)")
                        send({"type": "utterance", "text": text,
                              "tokens": tokens, "asr_ms": round(asr_ms)})
                buf, silent_blocks, speaking = [], 0, False

def mic_loop():
    try:
        _run_microphone()
    except Exception as exc:
        message = f"Microphone unavailable: {exc}. Typed input remains available."
        print(message)
        update_mic_status(message)

@asynccontextmanager
async def lifespan(app):
    global loop
    loop = asyncio.get_running_loop()
    threading.Thread(target=mic_loop, daemon=True).start()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def page():
    return FileResponse("index.html")

@app.get("/landmarks_data.js")
def data():
    return FileResponse("landmarks_data.js")

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        await ws.send_text(json.dumps({"type": "status", "text": mic_status}))
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            if msg.get("type") == "text" and msg.get("text", "").strip():
                text = msg["text"].strip()
                await broadcast({"type": "utterance", "text": text,
                                 "tokens": text_to_gloss(text), "asr_ms": 0})
    except WebSocketDisconnect:
        clients.discard(ws)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
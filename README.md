# SignBridge: speech to sign avatar

A college major project. It listens to English speech (or typed text), converts it to sign-language gloss, and plays the matching signs on an animated avatar in the browser.

This is a student prototype with a limited vocabulary. It is not a full ASL translator.

## How it works

1. **Microphone**: the server listens and ends a sentence after a short pause.
2. **Speech to text**: faster-whisper (`base.en`) runs on the CPU.
3. **Gloss**: `gloss.py` drops filler words, reduces words to base forms, and moves question words to the end. Words with no sign are shown as text letters.
4. **Sign data**: each sign comes from a WLASL video, converted to hand and body landmarks with MediaPipe Holistic.
5. **Avatar**: the landmarks are smoothed, centered and drawn on a canvas in the browser.

The current bundle (`landmarks_data.js`) contains **219 signs**. Clip quality varies from word to word.

## Run it

Requires Windows or Linux, Python 3.11, and a microphone.

```powershell
python -m venv venv
venv\Scripts\activate
pip install faster-whisper sounddevice numpy fastapi "uvicorn[standard]"
python server.py
```

Wait for the line `READY`, then open http://127.0.0.1:8000.

The microphone is set in `server.py` with `sd.default.device = 1`. Change `1` to your own microphone's index. To list your devices:

```powershell
python -c "import sounddevice as sd; print(sd.query_devices())"
```

You can also type a sentence on the page instead of speaking. `viewer.html` is a simple standalone viewer that needs no server.

## Rebuilding the sign data (optional)

The landmark files are already included. To rebuild them you need the WLASL videos, which are not in this repo:

1. Download the dataset from Kaggle (`risangbaskoro/wlasl-processed`) and extract it into a `videos/` folder.
2. `pip install mediapipe==0.10.14 opencv-python` (this version is pinned on purpose, because the code uses the older `mp.solutions` API).
3. Run `pick_videos.py`, `extract_landmarks.py`, `improve_landmarks.py`, then `build_data.py`.

## Limitations

- Gloss playback only. This is not full ASL grammar.
- No facial expressions or other non-manual signals.
- Words outside the vocabulary are shown as letters on screen, not as ASL fingerspelling.
- English speech input only.
- Each sign comes from a single signer, so speed and framing differ between words.
- Not suitable for medical, legal or other high-stakes communication.

## Data and credits

Sign videos come from the [WLASL dataset](https://dxli94.github.io/WLASL/) (Li et al.), which is licensed for academic and computational use only, with no commercial use. The landmark files in this repo are derived from that data. This project is non-commercial and for academic purposes. Please read the dataset's license before reusing the data.

Built with faster-whisper, FastAPI, MediaPipe and the Canvas 2D API.
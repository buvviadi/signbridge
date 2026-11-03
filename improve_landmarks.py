import os
os.environ["GLOG_minloglevel"] = "2"   # hides the noisy warnings

import json
import cv2
import mediapipe as mp

THRESHOLD = 70          # retry words below this hand-detection %
ALIASES = {"thanks": "thank you"}

def pts(lm):
    if lm is None:
        return None
    return [[round(p.x, 4), round(p.y, 4)] for p in lm.landmark]

def extract(path):
    holistic = mp.solutions.holistic.Holistic(model_complexity=1)
    cap = cv2.VideoCapture(path)
    frames, hands = [], 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        r = holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        lh, rh = pts(r.left_hand_landmarks), pts(r.right_hand_landmarks)
        if lh or rh:
            hands += 1
        frames.append({"pose": pts(r.pose_landmarks), "left": lh, "right": rh})
    cap.release()
    holistic.close()
    return frames, 100 * hands / max(len(frames), 1)

def pct_of(frames):
    return 100 * sum(1 for f in frames if f["left"] or f["right"]) / max(len(frames), 1)

on_disk = {}
for root, _, files in os.walk("videos"):
    for f in files:
        if f.lower().endswith(".mp4"):
            on_disk[os.path.splitext(f)[0]] = os.path.join(root, f)

with open("WLASL_v0.3.json", encoding="utf-8") as f:
    by_gloss = {e["gloss"].lower(): e["instances"] for e in json.load(f)}
with open("selected_videos.json", encoding="utf-8") as f:
    selected = json.load(f)

for word in list(selected):
    with open(f"landmarks/{word}.json") as f:
        current = pct_of(json.load(f))
    if current >= THRESHOLD:
        continue

    paths = [on_disk[i["video_id"]] for i in by_gloss[ALIASES.get(word, word)]
             if i["video_id"] in on_disk]
    best_pct, best_frames, best_path = current, None, selected[word]
    for p in paths:
        frames, pct = extract(p)
        if pct > best_pct:
            best_pct, best_frames, best_path = pct, frames, p

    if best_frames is not None:
        with open(f"landmarks/{word}.json", "w") as f:
            json.dump(best_frames, f)
        selected[word] = best_path
    print(f"{word:12} {current:3.0f}% -> {best_pct:3.0f}%  (tried {len(paths)} videos)")

with open("selected_videos.json", "w", encoding="utf-8") as f:
    json.dump(selected, f, indent=2)
print("\nDone.")
import json
import os
import cv2
import mediapipe as mp

with open("selected_videos.json", encoding="utf-8") as f:
    selected = json.load(f)

os.makedirs("landmarks", exist_ok=True)

def pts(landmarks):
    """21 or 33 points -> [[x, y], ...] or None if not detected."""
    if landmarks is None:
        return None
    return [[round(p.x, 4), round(p.y, 4)] for p in landmarks.landmark]

print(f"{'word':12} {'frames':>6} {'hands found':>12}")
for word, path in selected.items():
    holistic = mp.solutions.holistic.Holistic(model_complexity=1) # type: ignore
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

    with open(f"landmarks/{word}.json", "w") as f:
        json.dump(frames, f)
    pct = 100 * hands / max(len(frames), 1)
    print(f"{word:12} {len(frames):>6} {pct:>11.0f}%")

print("\nDone. Files are in the landmarks folder.")
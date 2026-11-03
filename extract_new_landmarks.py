import json
import os
import tempfile
from pathlib import Path

os.environ["GLOG_minloglevel"] = "2"

import cv2
import mediapipe as mp

DATA_DIR = Path("videos")
LANDMARK_DIR = Path("landmarks")
WLASL_PATH = Path("WLASL_v0.3.json")
SELECTED_PATH = Path("selected_videos.json")
MAX_CLIPS_PER_WORD = 6
EARLY_STOP_HAND_PERCENT = 90

APPROVED_WORDS = """
name know see sit stand college sister money day live open close love more
sign nice call cold nurse from coffee student boy girl child baby car bus
tired hurt cough blood head eye ear nose emergency police safe danger bathroom
train travel buy pay store problem question answer appointment
""".split()


def points(landmarks):
    if landmarks is None:
        return None
    return [[round(point.x, 4), round(point.y, 4)] for point in landmarks.landmark]


def extract(path):
    holistic = mp.solutions.holistic.Holistic(model_complexity=1)
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        holistic.close()
        raise RuntimeError(f"Could not open video: {path}")

    frames = []
    hands_found = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            result = holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            left = points(result.left_hand_landmarks)
            right = points(result.right_hand_landmarks)
            if left or right:
                hands_found += 1
            frames.append({
                "pose": points(result.pose_landmarks),
                "left": left,
                "right": right,
            })
    finally:
        capture.release()
        holistic.close()

    if not frames:
        raise RuntimeError(f"No frames decoded from video: {path}")
    return frames, 100 * hands_found / len(frames)


def write_json_atomically(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(data, temp_file, ensure_ascii=False)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def main():
    with WLASL_PATH.open(encoding="utf-8") as file:
        dataset = json.load(file)
    by_gloss = {
        entry["gloss"].strip().lower(): entry["instances"]
        for entry in dataset
    }
    with SELECTED_PATH.open(encoding="utf-8") as file:
        selected = json.load(file)

    on_disk = {}
    for path in DATA_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() == ".mp4":
            on_disk[path.stem] = path

    LANDMARK_DIR.mkdir(parents=True, exist_ok=True)
    print(f"{'word':16} {'frames':>7} {'hands':>8} {'tried':>7}  selected clip")
    for word in APPROVED_WORDS:
        landmark_path = LANDMARK_DIR / f"{word}.json"
        if landmark_path.exists():
            print(f"{word:16} {'SKIPPED':>7} {'existing landmarks file'}")
            continue
        if word not in selected:
            raise KeyError(f"{word!r} is missing from {SELECTED_PATH}")
        if word not in by_gloss:
            raise KeyError(f"{word!r} is missing from {WLASL_PATH}")

        instances = by_gloss[word]
        available_ids = []
        for instance in instances:
            video_id = str(instance["video_id"])
            if video_id in on_disk and video_id not in available_ids:
                available_ids.append(video_id)
        if len(available_ids) < 3:
            raise RuntimeError(
                f"{word}: expected at least 3 clips on disk, found {len(available_ids)}"
            )

        current_path = Path(selected[word])
        current_id = current_path.stem
        if current_id not in available_ids:
            raise RuntimeError(
                f"{word}: current selection {selected[word]!r} does not match "
                "a WLASL instance available on disk"
            )
        ordered_ids = [current_id] + [
            video_id for video_id in available_ids if video_id != current_id
        ]

        best_frames = None
        best_percent = -1
        best_path = None
        tried = 0
        for video_id in ordered_ids[:MAX_CLIPS_PER_WORD]:
            path = on_disk[video_id]
            tried += 1
            try:
                frames, percent = extract(path)
            except (OSError, RuntimeError, cv2.error) as error:
                print(f"ERROR {word}: {path}: {error}")
                continue

            if percent > best_percent:
                best_frames = frames
                best_percent = percent
                best_path = path
            if percent >= EARLY_STOP_HAND_PERCENT:
                break

        if best_frames is None or best_path is None:
            raise RuntimeError(f"{word}: no usable clips among {tried} attempts")
        if landmark_path.exists():
            print(f"{word}: landmarks appeared during extraction; skipping save")
            continue

        write_json_atomically(landmark_path, best_frames)
        selected[word] = str(best_path)
        write_json_atomically(SELECTED_PATH, selected)
        print(
            f"{word:16} {len(best_frames):7} {best_percent:7.1f}% "
            f"{tried:7}  {best_path}"
        )


if __name__ == "__main__":
    main()

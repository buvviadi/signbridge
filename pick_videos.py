import json
import os

WLASL_JSON = "WLASL_v0.3.json"
DATA_DIR = "videos"

MY_WORDS = """
hello thanks please sorry yes no good morning night
i you doctor mother father friend teacher
go come want need help eat drink sleep understand wait stop
hospital home school water food medicine toilet phone
sick pain hungry happy sad fine
what where when who why how
today tomorrow yesterday now
""".split()
ALIASES = {"thanks": "thank you"}

# 1) index every mp4 on disk by its video id
on_disk = {}
for root, _, files in os.walk(DATA_DIR):
    for f in files:
        if f.lower().endswith(".mp4"):
            on_disk[os.path.splitext(f)[0]] = os.path.join(root, f)
print(f"Found {len(on_disk)} mp4 files under {DATA_DIR}\n")

# 2) for each word, pick the first instance whose video exists
with open(WLASL_JSON, encoding="utf-8") as f:
    data = json.load(f)
by_gloss = {e["gloss"].lower(): e["instances"] for e in data}

selected, missing = {}, []
for w in MY_WORDS:
    instances = by_gloss[ALIASES.get(w, w)]
    paths = [on_disk[i["video_id"]] for i in instances if i["video_id"] in on_disk]
    if paths:
        selected[w] = paths[0]
        print(f"  {w:12} {len(paths)}/{len(instances)} videos on disk")
    else:
        missing.append(w)

with open("selected_videos.json", "w", encoding="utf-8") as f:
    json.dump(selected, f, indent=2)

print(f"\nSELECTED {len(selected)}/{len(MY_WORDS)} words -> selected_videos.json")
print("NO VIDEO:", missing)
import json
import os
import urllib.request

URL = "https://raw.githubusercontent.com/dxli94/WLASL/master/start_kit/WLASL_v0.3.json"
FILE = "WLASL_v0.3.json"

if not os.path.exists(FILE):
    print("Downloading WLASL index...")
    urllib.request.urlretrieve(URL, FILE)

with open(FILE, encoding="utf-8") as f:
    data = json.load(f)

index = {entry["gloss"].lower(): len(entry["instances"]) for entry in data}
print(f"WLASL has {len(index)} words\n")

MY_WORDS = """
hello thanks please sorry yes no good morning night
i you doctor mother father friend teacher
go come want need help eat drink sleep understand wait stop
hospital home school water food medicine toilet phone
sick pain hungry happy sad fine
what where when who why how
today tomorrow yesterday now
""".split()

# Words where WLASL may use a different label
ALIASES = {"thanks": "thank you", "toilet": "bathroom", "i": "me",
           "night": "night", "medicine": "medicine"}

found, missing = [], []
for w in MY_WORDS:
    key = w if w in index else ALIASES.get(w)
    if key and key in index:
        found.append((w, key, index[key]))
    else:
        missing.append(w)

print(f"FOUND {len(found)}/{len(MY_WORDS)}:")
for w, key, n in found:
    print(f"  {w:12} -> '{key}' ({n} videos)")
print(f"\nMISSING {len(missing)}: {missing}")
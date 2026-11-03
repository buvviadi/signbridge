import glob, json, os

data = {}
for path in glob.glob("landmarks/*.json"):
    with open(path) as f:
        data[os.path.basename(path)[:-5]] = json.load(f)

with open("landmarks_data.js", "w") as f:
    f.write("const SIGNS = " + json.dumps(data) + ";")
print(f"Bundled {len(data)} words -> landmarks_data.js")
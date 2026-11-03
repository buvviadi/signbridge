import json, glob, os

rows = []
for path in glob.glob("landmarks/*.json"):
    with open(path) as f:
        frames = json.load(f)
    hands = sum(1 for fr in frames if fr["left"] or fr["right"])
    rows.append((os.path.basename(path)[:-5], 100 * hands / max(len(frames), 1), len(frames)))

rows.sort(key=lambda r: r[1])
print(f"{'word':12} {'hands %':>8} {'frames':>7}")
for w, p, n in rows:
    print(f"{w:12} {p:>7.0f}% {n:>7}")
print(f"\nAverage: {sum(r[1] for r in rows) / len(rows):.0f}%   Words below 70%: {sum(1 for r in rows if r[1] < 70)}")
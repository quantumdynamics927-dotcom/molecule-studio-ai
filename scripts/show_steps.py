import json, sys, os

os.chdir("D:/Molecule-App")

# Read the JSONL file
with open("aspirin_steps.jsonl") as f:
    raw = f.read()

# Split on lines that look like JSON objects
lines = []
for line in raw.splitlines():
    stripped = line.strip()
    if stripped.startswith('{"'):
        lines.append(stripped)

print(f"{len(lines)} steps captured\n")
print(f"{'step':>4}  {'#1':>6} {'p1':>8}  {'#2':>6} {'p2':>8}  {'H':>8}")
print("-" * 55)
for line in lines:
    try:
        j = json.loads(line)
        t = j["localization"][0]
        t2 = j["localization"][1]
        print(f"{j['walk_steps']:>4}  {t['element']}{t['atom_index']:>3} {t['visit_probability']:>8.4f}  {t2['element']}{t2['atom_index']:>3} {t2['visit_probability']:>8.4f}  {j['position_entropy']:>8.3f}")
    except Exception as e:
        print(f"Error parsing: {e}")

# Aspirin atom assignments
print("\n\n--- Aspirin atom indices ---")
with open("aspirin.json") as f:
    mol = json.load(f)
for i, atom in enumerate(mol["atoms"]):
    print(f"  {i:>2}: {atom['element']:>2}  x={atom['x']:>8.4f}  y={atom['y']:>8.4f}  z={atom['z']:>8.4f}")

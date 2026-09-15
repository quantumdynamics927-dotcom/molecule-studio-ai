import json, os
os.chdir("D:/Molecule-App")

for mol, jsonl in [("aspirin", "aspirin_steps.jsonl"), ("adrenaline", "adrenaline_steps.jsonl")]:
    with open(jsonl) as f:
        raw = f.read()
    lines = [l.strip() for l in raw.splitlines() if l.strip().startswith('{')]
    print(f"\n{'='*60}")
    print(f"{mol.upper()} — top site evolution (starting node 0)")
    print(f"{'='*60}")
    print(f"{'step':>4}  {'#1':>8} {'p1':>8}  {'#2':>8} {'p2':>8}  {'H':>8}")
    print("-" * 60)
    for line in lines:
        try:
            j = json.loads(line)
            t = j["localization"][0]
            t2 = j["localization"][1]
            print(f"{j['walk_steps']:>4}  {t['element']}{t['atom_index']:>3} {t['visit_probability']:>8.4f}  {t2['element']}{t2['atom_index']:>3} {t2['visit_probability']:>8.4f}  {j['position_entropy']:>8.3f}")
        except Exception as e:
            pass

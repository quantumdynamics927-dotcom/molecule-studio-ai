import json, subprocess, sys

result = subprocess.run(
    ["python", "scripts/molecular_fractal_bridge.py", "-n", "0", "-s", "10", "--steps-series"],
    capture_output=True, text=True, cwd="D:/Molecule-App",
    env={**__import__("os").environ, "PATH": __import__("os").environ.get("PATH", "")}
)

print("STDOUT:", result.stdout[:500] if result.stdout else "(empty)")
print("STDERR:", result.stderr[:500] if result.stderr else "(empty)")

if result.returncode != 0:
    print("FAILED")
    sys.exit(1)

lines = [l for l in result.stdout.splitlines() if l.strip()]
print(f"\n{len(lines)} results:\n")
print(f"{'steps':>5}  {'#1':>6} {'p1':>8}  {'#2':>6} {'p2':>8}  {'H':>8}")
print("-" * 55)
for line in lines:
    j = json.loads(line)
    t = j["localization"][0]
    t2 = j["localization"][1]
    print(f"{j['walk_steps']:>5}  {t['element']}{t['atom_index']:>3} {t['visit_probability']:>8.4f}  {t2['element']}{t2['atom_index']:>3} {t2['visit_probability']:>8.4f}  {j['position_entropy']:>8.3f}")

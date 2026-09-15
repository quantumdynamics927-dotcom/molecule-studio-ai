from fetch_molecule import fetch_molecule

# PAH series
PAHS = ['benzene', 'naphthalene', 'anthracene', 'tetracene', 'pentacene']
print("PAH Series:")
for name in PAHS:
    r = fetch_molecule(name)
    if r:
        print(f"  {name}: {len(r['atoms'])} atoms OK")
    else:
        print(f"  {name}: FAILED")

# Alkane series
ALKANES = ['methane', 'ethane', 'propane', 'butane', 'pentane', 'hexane']
print("\nAlkane Series:")
for name in ALKANES:
    r = fetch_molecule(name)
    if r:
        print(f"  {name}: {len(r['atoms'])} atoms OK")
    else:
        print(f"  {name}: FAILED")

# Additional heterocycles
HETEROS = ['pyridine', 'pyrrole', 'furan', 'thiophene', 'quinoline', 'isoquinoline']
print("\nHeterocycles:")
for name in HETEROS:
    r = fetch_molecule(name)
    if r:
        print(f"  {name}: {len(r['atoms'])} atoms OK")
    else:
        print(f"  {name}: FAILED")

# Small heteroatom-dominants
SMALL = ['water', 'hydrogen sulfide', 'ammonia', 'methanol', 'methanethiol']
print("\nSmall heteroatom-dominant:")
for name in SMALL:
    r = fetch_molecule(name)
    if r:
        print(f"  {name}: {len(r['atoms'])} atoms OK")
    else:
        print(f"  {name}: FAILED")

# Additional aromatics
AROMATICS = ['toluene', 'phenol', 'aniline', 'styrene', 'biphenyl']
print("\nAdditional aromatics:")
for name in AROMATICS:
    r = fetch_molecule(name)
    if r:
        print(f"  {name}: {len(r['atoms'])} atoms OK")
    else:
        print(f"  {name}: FAILED")

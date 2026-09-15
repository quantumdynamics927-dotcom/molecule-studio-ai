import json, requests

r = requests.get('https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/record/JSON?heading=3D+Conformer', timeout=30)
data = r.json()
compound = data['PC_Compounds'][0]
conformers = compound['coords'][0]['conformers']
print(f'Num conformers: {len(conformers)}')
for i, c in enumerate(conformers):
    print(f'Conf {i} keys: {list(c.keys())}')
    print(f'Conf {i} x count: {len(c.get("x", []))}')

atoms = compound['atoms']
print(f'\natoms keys: {list(atoms.keys())}')
print(f'element codes: {atoms["element"][:15]}')

# z from conformer style
print(f'\nconf[0] style keys: {list(conformers[0].get("style", {}).keys()) if "style" in conformers[0] else "no style"}')

# Check if aid is per-conformer
print(f'\nFirst conformer aid: {conformers[0].get("aid", "MISSING")[:10]}')

# Check bonds
bonds = compound['bonds']
print(f'\nbonds keys: {list(bonds.keys())}')
print(f'aid1: {bonds["aid1"][:10]}')
print(f'aid2: {bonds["aid2"][:10]}')
print(f'Order: {bonds.get("order", "NO ORDER FIELD")[:10]}')

# Check the count section
count = compound.get('count', {})
print(f'\ncount keys: {list(count.keys())}')

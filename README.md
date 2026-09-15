# Molecule Studio

Interactive 3D molecular structure lab. Look up compounds from PubChem, inspect bonds and geometry, keep notebooks, and export structures.

## Features

- **3D viewer** — ball-and-stick and space-fill rendering with orbit controls
- **PubChem search** — load molecules by name, formula, CID, or SMILES
- **Analysis** — bond lengths, angles, composition, and estimated properties
- **Library** — built-in presets plus saved structures
- **Notes** — per-molecule lab notebook
- **Export** — PDB, XYZ, MOL, and JSON
- **AI tools** — generate, explain, and simulate reactions (uses the app owner’s xAI quota when configured)

## Run locally

**Prerequisites:** Node.js 22+

```bash
npm install
npm run dev
```

The app listens on `http://localhost:8080`.

```bash
npm run build      # production build
npm run typecheck
npm test
```

## Research notes

This repository also contains quantum / fractal analysis experiments and protocols:

- [SPEC.md](SPEC.md)
- [PROTOCOL.md](PROTOCOL.md)
- [ANALYSIS.md](ANALYSIS.md)
- [ENAQT_ANALYSIS.md](ENAQT_ANALYSIS.md)
- [FINAL_RESEARCH_SUMMARY.md](FINAL_RESEARCH_SUMMARY.md)

Python helpers live under [`scripts/`](scripts/).

## Stack

React 19, TanStack Start, Three.js / React Three Fiber, Tailwind CSS v4, Zustand.

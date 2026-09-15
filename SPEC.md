# Molecule Studio Scientific Platform - SPEC.md

## 1. Project Overview
- **Name**: Molecule Studio Scientific Platform
- **Type**: Interactive molecular visualization and analysis web app
- **Core Function**: AI-powered 3D molecular structure generation + scientific analysis tools
- **Target Users**: Chemistry researchers, students, drug discovery teams

## 2. Technology Stack
| Layer | Technology |
|-------|------------|
| UI Framework | React 19 + TypeScript + Vite |
| 3D Rendering | Three.js + @react-three/fiber + @react-three/drei |
| AI Backend | Ollama Cloud API (minimax-m2.7:cloud) |
| Styling | Tailwind CSS (via CDN) + Lucide icons |
| Testing | Vitest + @testing-library/react |

## 3. Architecture

### Directory Structure
```
D:\Molecule-App\
├── App.tsx                      # Main app with tabbed interface
├── index.tsx                    # React entry point
├── index.html                   # HTML shell
├── types.ts                     # TypeScript interfaces
├── constants.ts                 # CPK colors, presets
├── SPEC.md                      # This file
├── CLAUDE.md                    # Claude Code instructions
├── services\
│   ├── ollamaService.ts         # Ollama Cloud API client
│   ├── molecularProperties.ts   # MW, formula calculations
│   ├── geometryUtils.ts         # Bond lengths, angles, RMSD
│   ├── exportService.ts         # PDB, XYZ, MOL, JSON export
│   └── pubchemService.ts        # PubChem PUG REST API
├── components\
│   ├── MoleculeCanvas.tsx       # 3D viewer (existing)
│   ├── AtomMesh.tsx             # Atom spheres (existing)
│   ├── BondMesh.tsx             # Bond cylinders (existing)
│   └── notebook\
│       ├── NotebookContainer.tsx
│       ├── CodeCell.tsx
│       ├── MarkdownCell.tsx
│       ├── ViewCell.tsx
│       └── PrebuiltNotebooks.ts
├── modules\
│   ├── GeometryOptimizer.tsx
│   ├── BondAnalyzer.tsx
│   ├── PropertyCalculator.tsx
│   ├── MoleculeComparator.tsx
│   ├── ReactionSimulator.tsx
│   └── PDBExplorer.tsx
└── tests\
    ├── setup.ts
    ├── services.test.ts
    └── geometryUtils.test.ts
```

## 4. Data Models

```typescript
interface Atom {
  element: string;
  x: number;
  y: number;
  z: number;
}

interface MoleculeData {
  name: string;
  formula: string;
  description: string;
  category: string;
  atoms: Atom[];
  bonds: number[][];
}

interface MolecularProperties {
  molecularWeight: number;
  formula: string;
  atomCount: Record<string, number>;
  bondCount: number;
  bondStats: { min: number; max: number; avg: number };
  centerOfMass: { x: number; y: number; z: number };
}
```

## 5. API Design

### Ollama Cloud Service
- **Endpoint**: `POST https://api.ollama.cloud/v1/chat/completions`
- **Model**: `minimax-m2.7:cloud`
- **Timeout**: 30s with retry logic

### PubChem Service
- **Endpoint**: `https://pubchem.ncbi.nlm.nih.gov/rest/pug`
- **Methods**: searchMolecule(), getMolecule2D(), getMoleculeProperties()

## 6. UI Specification

### Layout
- **Header**: Logo, tabs (Viewer/Analysis/Notebooks/DB), search, export dropdown, dark mode toggle, API status
- **Sidebar** (320px): Context-sensitive based on active tab
- **Main Canvas**: 3D viewer, notebook interface, or analysis panel
- **Notifications**: Toast system (bottom-right)

### Tabs
1. **3D Viewer** - Molecule visualization (default)
2. **Analysis** - Module selector grid
3. **Notebooks** - Jupyter-style notebook interface
4. **Molecule DB** - PubChem search

## 7. Analysis Modules

| Module | Purpose | Algorithm |
|--------|---------|-----------|
| GeometryOptimizer | Minimize bond length violations | Gradient descent |
| BondAnalyzer | Analyze all bond lengths/angles | Distance calculations |
| PropertyCalculator | MW, formula, atom counts | Summation |
| MoleculeComparator | Compare two molecules | RMSD calculation |
| ReactionSimulator | Predict reaction products | Ollama AI |
| PDBExplorer | Fetch RCSB protein structures | PDB REST API |

## 8. Export Formats
- **PDB**: Standard protein data bank format
- **XYZ**: Atom count + comment + coordinates
- **MOL**: MDL MOL file format
- **JSON**: Pretty-printed molecule data

## 9. Testing Strategy
- Unit tests for all geometry utility functions
- Component tests for analysis modules
- Integration tests for API calls (mocked)

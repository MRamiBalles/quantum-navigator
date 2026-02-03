# Quantum Navigator v2.0

**Technology-Agnostic Quantum Middleware for NISQ-era Optimization**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/react-18+-blue.svg)](https://reactjs.org/)

---

## Overview

Quantum Navigator is a **Quantum Middle Layer** that orchestrates heterogeneous quantum backends without reimplementing low-level compilation. Instead of competing with native SDKs (Qiskit, Pulser, Cirq), it *governs* them to extract maximum performance.

### Key Capabilities

| Module | Purpose | Backend |
|--------|---------|---------|
| **Parallel Routing Orchestration** | Launch 100+ SABRE instances with varied seeds/heuristics | Qiskit 1.2+ (Rust) |
| **Neutral Atom Driver** | FPQA geometry & analog pulse sequences | Pulser (Pasqal/QuEra) |
| **QEC Simulation** | Surface code error correction pipelines | Stim + PyMatching |
| **Adaptive Data Loading** | ATP with L-BFGS-B for QML circuits | NumPy/SciPy |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React/TypeScript)              │
│  ┌──────────────┐  ┌───────────────────┐  ┌──────────────┐  │
│  │ Dashboard UI │  │ Atom Register     │  │ Sequence     │  │
│  │              │  │ Editor            │  │ Timeline     │  │
│  └──────────────┘  └───────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Quantum Middle Layer v2.0                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Technology-Agnostic JSON IR                ││
│  │     (neutral_atom_job.schema.json / circuit_job.json)   ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                               │
│      ┌───────────────────────┼───────────────────────┐      │
│      ▼                       ▼                       ▼      │
│  ┌──────────┐          ┌──────────┐          ┌──────────┐   │
│  │ Qiskit   │          │ Pulser   │          │ Stim     │   │
│  │ Driver   │          │ Adapter  │          │ Engine   │   │
│  └──────────┘          └──────────┘          └──────────┘   │
└─────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│ IBM Quantum  │    │ Pasqal Fresnel   │    │ Classical    │
│ Backends     │    │ QuEra Aquila     │    │ Simulator    │
└──────────────┘    └──────────────────┘    └──────────────┘
```

---

## Neutral Atom Support

Quantum Navigator includes a complete driver for **neutral atom quantum processors** (Pasqal, QuEra) based on the Pulser library.

### Features

- **Interactive Register Editor**: Visual canvas for placing SLM (static) and AOD (mobile) atoms
- **Blockade Radius Visualization**: See which atoms can interact via Rydberg coupling
- **Physics Constraint Validation**: Pre-flight checks for collisions, velocity limits, and topological constraints
- **Analog Pulse Timeline**: Visualize Ω(t) and Δ(t) waveforms

### Supported Operations

| Operation | Description | Parameters |
|-----------|-------------|------------|
| `GlobalPulse` | Rydberg pulse on all atoms | Ω(t), Δ(t), φ |
| `LocalDetuning` | Address specific atoms | target_atoms, detuning |
| `ShuttleMove` | AOD atom transport | atom_ids, target_positions, trajectory |
| `RydbergGate` | Two-qubit CZ via blockade | control, target |
| `Measurement` | Fluorescence imaging | atom_ids, basis |

### Physical Constraints Enforced

| Constraint | Typical Value | Error Type |
|------------|---------------|------------|
| Minimum atom distance | ≥ 4 µm | `CollisionError` |
| Rydberg blockade radius | 6–10 µm | `BlockadeDistanceError` |
| AOD velocity limit | ≤ 0.55 µm/µs | `VelocityExceededError` |
| AOD row/column crossing | Prohibited | `TopologicalViolationError` |

---

## Quick Start

### Prerequisites

- Node.js 18+ (frontend)
- Python 3.10+ (backend)
- pnpm or npm

### Installation

```bash
# Clone repository
git clone https://github.com/MRamiBalles/quantum-navigator.git
cd quantum-navigator

# Frontend
npm install
npm run dev

# Backend (in separate terminal)
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
npm run test
```

---

## Project Structure

```
quantum-navigator/
├── src/                          # Frontend (React/TypeScript)
│   ├── components/
│   │   ├── dashboard/            # Main dashboard UI
│   │   ├── neutral-atom/         # Atom register editor
│   │   │   ├── AtomRegisterEditor.tsx
│   │   │   ├── AnalogSequenceTimeline.tsx
│   │   │   └── NeutralAtomStudio.tsx
│   │   └── ui/                   # Shared UI components
│   └── pages/
│
├── backend/                      # Python middleware
│   ├── drivers/
│   │   └── neutral_atom/         # Pulser-based driver
│   │       ├── schema.py         # Pydantic models
│   │       ├── validator.py      # Physics constraints
│   │       └── pulser_adapter.py # Pulser bridge
│   ├── schemas/
│   │   └── neutral_atom_job.schema.json
│   └── tests/
│
└── docs/                         # Documentation
    ├── ARCHITECTURE.md
    ├── API_REFERENCE.md
    └── PHYSICAL_CONSTRAINTS.md
```

---

## JSON Schema Example

```json
{
  "name": "MIS Demo",
  "device": { "backend_id": "pasqal_fresnel" },
  "register": {
    "min_atom_distance": 4.0,
    "blockade_radius": 8.0,
    "atoms": [
      { "id": 0, "x": 0.0, "y": 0.0, "role": "SLM" },
      { "id": 1, "x": 6.0, "y": 0.0, "role": "SLM" },
      { "id": 2, "x": 3.0, "y": 5.2, "role": "AOD", "aod_row": 0, "aod_col": 0 }
    ]
  },
  "operations": [
    {
      "op_type": "global_pulse",
      "start_time": 0,
      "omega": { "type": "blackman", "duration": 1000, "area": 3.14159 }
    },
    {
      "op_type": "measure",
      "start_time": 1100,
      "atom_ids": [0, 1, 2]
    }
  ]
}
```

---

## References

### Neutral Atom Computing

1. **Pulser Documentation** - [pulser.readthedocs.io](https://pulser.readthedocs.io/)
2. **QuEra Aquila** - [queracomputing.com](https://www.queracomputing.com/)
3. **Pasqal Hardware** - [pasqal.com](https://www.pasqal.com/)

### Key Papers

- *High-fidelity gates and mid-circuit erasure conversion in an atomic qubit* (Lukin et al., 2023)
- *FPQA-C: A Compilation Framework for Field Programmable Qubit Arrays* (arXiv:2311.15123)
- *Logical quantum processor based on reconfigurable atom arrays* (Nature, 2023)

### Related Projects

- [pasqal-io/Pulser](https://github.com/pasqal-io/Pulser) - Control library for neutral atom devices
- [quantumlib/Stim](https://github.com/quantumlib/Stim) - Fast stabilizer circuit simulator
- [Qiskit](https://github.com/Qiskit/qiskit) - IBM's quantum computing SDK

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) before submitting pull requests.

---

*Quantum Navigator v2.0 - Built for the NISQ era and beyond.*

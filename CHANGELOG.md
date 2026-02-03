# Changelog

All notable changes to Quantum Navigator are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [2.0.0] - 2026-02-03

### Added

**Neutral Atom Driver**
- Complete driver for Pasqal and QuEra neutral atom processors
- Pydantic schema for technology-agnostic job specification (`schema.py`)
- Physics constraint validator with collision, velocity, and topology checks (`validator.py`)
- Pulser adapter for compilation and simulation (`pulser_adapter.py`)
- JSON Schema for frontend validation (`neutral_atom_job.schema.json`)

**Frontend Components**
- `AtomRegisterEditor`: Interactive SVG canvas for atom placement
- `AnalogSequenceTimeline`: Ω(t) and Δ(t) waveform visualization
- `NeutralAtomStudio`: Full-page editor with JSON export

**Documentation**
- `README.md`: Complete project overview
- `docs/ARCHITECTURE.md`: System layer diagram
- `docs/PHYSICAL_CONSTRAINTS.md`: Physics guide
- `docs/API_REFERENCE.md`: REST API documentation
- `docs/CONTRIBUTING.md`: Contribution guidelines

### Changed
- Architecture pivot from circuit reimplementation to middleware orchestration
- Backend structure reorganized into `drivers/` and `schemas/`

### Technical Details
- Pulser integration via `pasqal-io/Pulser` library
- Supports `DigitalAnalogDevice` (Fresnel) and `AnalogDevice` (Aquila)
- Validation enforces: min distance 4µm, blockade radius configurable, AOD velocity limit 0.55 µm/µs

---

## [1.0.0] - 2026-01-15

### Added
- Initial React dashboard with shadcn/ui
- Backend status display for IBM Quantum, QuEra, Pasqal
- Module cards for routing, QML, QEC, PQC
- Circuit uploader component
- Metrics visualization with Recharts

---

## [0.1.0] - 2025-12-01

### Added
- Project scaffolding with Vite + React + TypeScript
- TailwindCSS configuration
- Basic layout components

# Quantum Navigator v2.0 - Technical Architecture

## Design Philosophy

Quantum Navigator adopts a **middleware orchestration** approach rather than reimplementing low-level quantum compilation. This design follows the HPC-inspired blueprint for technology-agnostic quantum computing.

### Core Principles

1. **Backend Agnosticism**: Define quantum intent in JSON, translate to native SDK calls
2. **Validation First**: Reject physically impossible configurations before compilation
3. **Parallel Exploration**: Exploit SDK speed to sample solution spaces

---

## System Layers

### Layer 1: Frontend (React/TypeScript)

```
src/
├── components/
│   ├── dashboard/           # Main control panel
│   │   ├── Dashboard.tsx    # Module cards, stats
│   │   ├── BackendStatus.tsx # Backend health/queue
│   │   └── CircuitUploader.tsx
│   │
│   └── neutral-atom/        # Atom register tools
│       ├── AtomRegisterEditor.tsx   # Interactive canvas
│       ├── AnalogSequenceTimeline.tsx
│       └── NeutralAtomStudio.tsx    # Full-page editor
```

**Technology Stack:**
- React 18 with TypeScript
- Vite for bundling
- TailwindCSS + shadcn/ui
- SVG for interactive graphics

### Layer 2: JSON Intermediate Representation

The middleware accepts technology-agnostic job specifications:

```
backend/schemas/
└── neutral_atom_job.schema.json
```

**Key Types:**
- `NeutralAtomJob` - Top-level job container
- `NeutralAtomRegister` - Geometry specification
- `GlobalPulse`, `ShuttleMove`, `RydbergGate` - Operations
- `WaveformSpec` - Analog pulse shapes

### Layer 3: Driver Layer (Python)

```
backend/drivers/
└── neutral_atom/
    ├── schema.py          # Pydantic models
    ├── validator.py       # Physics constraints
    └── pulser_adapter.py  # Pulser bridge
```

**Responsibilities:**
1. Parse and validate JSON IR
2. Check physical constraints
3. Translate to native SDK objects
4. Execute on simulator or hardware

### Layer 4: Hardware Backends

| Backend | SDK | Connection |
|---------|-----|------------|
| IBM Quantum | Qiskit | IBM Cloud |
| Pasqal Fresnel | Pulser | Pasqal Cloud |
| QuEra Aquila | Pulser/Braket | AWS Braket |
| Local Simulator | QutipEmulator | Local |

---

## Neutral Atom Driver Architecture

### Data Flow

```
┌─────────────────┐
│  Frontend JSON  │
│    Editor       │
└────────┬────────┘
         │ POST /api/jobs
         ▼
┌─────────────────┐
│   schema.py     │  Pydantic validation
│ NeutralAtomJob  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  validator.py   │  Physics checks
│ PulserValidator │
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│ pulser_adapter.py│  SDK translation
│  PulserAdapter   │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│  pulser.Sequence │
│  QutipEmulator   │
└─────────────────┘
```

### Validator Checks

| Check | Method | Exception |
|-------|--------|-----------|
| Atom collision | Pairwise distance | `CollisionError` |
| Blockade reach | Gate distance check | `BlockadeDistanceError` |
| AOD velocity | distance/time | `VelocityExceededError` |
| AOD topology | Row/col order | `TopologicalViolationError` |

### Device Registry

The adapter maintains device profiles:

```python
DEVICE_REGISTRY = {
    "pasqal_fresnel": DeviceProfile(
        pulser_device=DigitalAnalogDevice,
        max_omega=25,  # rad/µs
        supports_local_addressing=True,
        supports_aod_movement=True,
    ),
    "quera_aquila": DeviceProfile(
        pulser_device=AnalogDevice,
        supports_local_addressing=False,
        supports_aod_movement=False,
    ),
}
```

---

## Frontend State Management

### AtomRegisterEditor State

```typescript
interface RegisterConfig {
  layoutType: "arbitrary" | "triangular" | "rectangular";
  minAtomDistance: number;
  blockadeRadius: number;
  atoms: AtomPosition[];
}
```

### Validation Flow

1. User places atom via canvas click
2. Position snapped to grid
3. `validateRegister()` runs on every change
4. Errors displayed inline
5. Export disabled if errors exist

---

## Simulation Strategy

| System Size | Backend | Notes |
|-------------|---------|-------|
| ≤ 15 atoms | QutipEmulator | Exact, full Hilbert space |
| 16-30 atoms | Tensor Network | Approximate, low entanglement |
| > 30 atoms | Hardware/Braket | Cloud execution |

---

## Security Considerations

- **Input Validation**: All JSON validated via Pydantic before processing
- **Rate Limiting**: API endpoints implement request throttling
- **Credential Isolation**: Backend tokens never exposed to frontend
- **Sandboxed Execution**: Simulation runs in isolated process

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Register validation | < 10ms | ✓ |
| Pulser compilation | < 100ms | ✓ |
| 10-atom simulation | < 5s | ✓ |
| Frontend FPS | 60 | ✓ |

---

## Future Extensions

1. **Tensor Network Backend**: Integration with quimb for large systems
2. **QAOA Templates**: Pre-built optimization circuits
3. **Multi-zone Support**: Storage/entanglement/readout zones
4. **Real-time Hardware Monitoring**: Queue status, calibration data

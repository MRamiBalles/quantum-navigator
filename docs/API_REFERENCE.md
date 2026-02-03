# API Reference

## Overview

Quantum Navigator exposes a REST API for job submission and management. The backend is built with FastAPI.

---

## Jobs Endpoint

### Submit Job

```http
POST /api/v2/jobs
Content-Type: application/json
```

**Request Body:** See [neutral_atom_job.schema.json](../backend/schemas/neutral_atom_job.schema.json)

**Example:**
```json
{
  "name": "MIS Demo",
  "device": { "backend_id": "simulator" },
  "register": {
    "min_atom_distance": 4.0,
    "blockade_radius": 8.0,
    "atoms": [
      { "id": 0, "x": 0, "y": 0, "role": "SLM" },
      { "id": 1, "x": 6, "y": 0, "role": "SLM" }
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
      "atom_ids": [0, 1]
    }
  ],
  "simulation": {
    "backend": "qutip",
    "shots": 1000
  }
}
```

**Response:**
```json
{
  "job_id": "j-abc123",
  "status": "queued",
  "submitted_at": "2026-02-03T03:00:00Z"
}
```

---

### Get Job Status

```http
GET /api/v2/jobs/{job_id}
```

**Response:**
```json
{
  "job_id": "j-abc123",
  "status": "completed",
  "result": {
    "counts": { "00": 512, "11": 488 },
    "shots_executed": 1000,
    "execution_time_ms": 1234.5
  }
}
```

---

### Validate Job (Dry Run)

```http
POST /api/v2/jobs/validate
Content-Type: application/json
```

Returns validation results without executing:

```json
{
  "is_valid": false,
  "errors": [
    {
      "type": "CollisionError",
      "message": "Atoms 0 and 1 are 3.5 µm apart (min: 4.0 µm)"
    }
  ],
  "warnings": []
}
```

---

## Backends Endpoint

### List Available Backends

```http
GET /api/v2/backends
```

**Response:**
```json
{
  "backends": [
    {
      "id": "pasqal_fresnel",
      "name": "Pasqal Fresnel",
      "type": "neutral-atom",
      "status": "online",
      "max_qubits": 100,
      "supports_aod": true
    },
    {
      "id": "quera_aquila",
      "name": "QuEra Aquila",
      "type": "neutral-atom",
      "status": "online",
      "max_qubits": 256,
      "supports_aod": false
    },
    {
      "id": "simulator",
      "name": "Local QutipEmulator",
      "type": "simulator",
      "status": "online",
      "max_qubits": 15
    }
  ]
}
```

---

## Schema Types

### AtomPosition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | ✓ | Unique atom identifier |
| `x` | float | ✓ | X coordinate (µm) |
| `y` | float | ✓ | Y coordinate (µm) |
| `role` | string | | `"SLM"`, `"AOD"`, or `"STORAGE"` |
| `aod_row` | integer | | AOD grid row (for topological validation) |
| `aod_col` | integer | | AOD grid column |

### WaveformSpec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ✓ | `"constant"`, `"blackman"`, `"gaussian"`, `"interpolated"` |
| `duration` | float | ✓ | Duration in nanoseconds |
| `amplitude` | float | * | For constant waveforms (rad/µs) |
| `area` | float | * | For blackman/gaussian (rad) |
| `times` | float[] | * | For interpolated |
| `values` | float[] | * | For interpolated |

### GlobalPulse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `op_type` | string | ✓ | Must be `"global_pulse"` |
| `start_time` | float | ✓ | Start time (ns) |
| `omega` | WaveformSpec | ✓ | Rabi frequency waveform |
| `detuning` | WaveformSpec | | Detuning waveform |
| `phase` | float | | Phase in radians (0-2π) |

### ShuttleMove

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `op_type` | string | ✓ | Must be `"shuttle"` |
| `atom_ids` | integer[] | ✓ | AOD atoms to move |
| `start_time` | float | ✓ | Start time (ns) |
| `duration` | float | ✓ | Movement duration (ns) |
| `target_positions` | [float, float][] | ✓ | Target (x, y) per atom |
| `trajectory` | string | | `"linear"`, `"minimum_jerk"`, `"sine"` |

### RydbergGate

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `op_type` | string | ✓ | Must be `"rydberg_gate"` |
| `control_atom` | integer | ✓ | Control atom ID |
| `target_atom` | integer | ✓ | Target atom ID |
| `start_time` | float | ✓ | Start time (ns) |
| `gate_type` | string | | `"CZ"` or `"CPHASE"` |

### Measurement

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `op_type` | string | ✓ | Must be `"measure"` |
| `atom_ids` | integer[] | ✓ | Atoms to measure |
| `start_time` | float | ✓ | Measurement time (ns) |
| `basis` | string | | `"computational"`, `"x"`, `"y"` |

---

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 400 | `VALIDATION_ERROR` | Job failed physics validation |
| 404 | `JOB_NOT_FOUND` | Unknown job ID |
| 422 | `SCHEMA_ERROR` | Malformed JSON |
| 503 | `BACKEND_UNAVAILABLE` | Hardware offline |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/api/v2/jobs` (POST) | 10/min |
| `/api/v2/jobs/validate` | 60/min |
| `/api/v2/jobs/{id}` (GET) | 120/min |

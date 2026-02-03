# Physical Constraints Guide

## Overview

Neutral atom quantum processors operate under strict physical constraints that differ fundamentally from superconducting or trapped-ion systems. This guide documents the constraints enforced by Quantum Navigator's validation layer.

---

## Geometric Constraints

### Minimum Atom Distance

**Constraint:** Adjacent atoms must maintain a minimum separation to avoid destructive light-assisted collisions during trap loading and to ensure optical resolution.

| Parameter | Typical Value | Hard Limit |
|-----------|---------------|------------|
| Minimum distance | 4.0 µm | ~3.5 µm |

**Why it matters:** At shorter distances, the optical tweezers cannot reliably resolve individual atoms, and light-assisted collisions during the loading phase can eject atoms from the trap.

**Validation Code:**
```python
if distance(atom_i, atom_j) < config.min_atom_distance:
    raise CollisionError(...)
```

---

### Rydberg Blockade Radius

**Constraint:** Two-qubit gates based on Rydberg blockade require atoms to be within the blockade radius R_b.

| Parameter | Typical Value | Range |
|-----------|---------------|-------|
| Blockade radius | 8.0 µm | 5-12 µm |

The blockade radius depends on the Rydberg state (principal quantum number n) and the interaction coefficient C_6:

```
R_b = (C_6 / Ω)^(1/6)
```

**Why it matters:** If atoms are too far apart, the Rydberg-Rydberg interaction is too weak to create entanglement. The gate will fail silently, producing separable states instead of entangled states.

**Validation Code:**
```python
if distance(control, target) > config.blockade_radius:
    raise BlockadeDistanceError(...)
```

---

## AOD Movement Constraints

### Velocity Limit

**Constraint:** Atoms transported by acousto-optic deflectors (AODs) must move slowly enough to avoid heating.

| Parameter | Typical Value | Hard Limit |
|-----------|---------------|------------|
| Max velocity | 0.55 µm/µs | ~0.8 µm/µs |

**Why it matters:** Rapid movement causes parametric heating of the atomic motion in the trap. The atom's vibrational quantum number increases, leading to:
- Reduced gate fidelity
- Position uncertainty
- Potential atom loss

**Heating Model:**
```python
decoherence_cost = distance * (velocity / max_velocity) * HEATING_COEFFICIENT
```

---

### Topological Constraints (Row/Column Ordering)

**Constraint:** In a 2D AOD array, atoms cannot cross rows or columns during movement.

**Why this exists:** AOD arrays work by deflecting a single laser beam with acoustic waves. The deflection angles determine trap positions. In a 2D array:
- Rows are controlled by one AOD (e.g., X-deflector)
- Columns are controlled by another AOD (Y-deflector)

Since each deflector creates a 1D sorted array of traps, atoms cannot "pass through" each other:

```
Initial:    A(row 0) --- B(row 1)
Invalid:    B(row 0) --- A(row 1)   # Would require crossing
Valid:      A(row 0, col 1) --- B(row 1, col 0)  # Allowed
```

**Validation Code:**
```python
if relative_row_order_changes or relative_col_order_changes:
    raise TopologicalViolationError(...)
```

---

## Pulse Constraints

### Slew Rate

**Constraint:** Pulse amplitude and detuning changes are limited by the AWG (arbitrary waveform generator) bandwidth.

| Parameter | Typical Value |
|-----------|---------------|
| AWG bandwidth | 100 MHz |
| Min pulse duration | 16 ns |

**Why it matters:** Attempting to change Ω or Δ faster than the hardware bandwidth results in:
- Spectral leakage
- Incomplete pulses
- Off-resonant excitation

---

### Maximum Amplitude

**Constraint:** Rabi frequency is limited by available laser power.

| Device | Max Ω |
|--------|-------|
| Pasqal Fresnel | ~25 rad/µs |
| QuEra Aquila | ~15 rad/µs |

---

## Timing Constraints

### Sequence Duration

| Parameter | Typical Limit |
|-----------|---------------|
| Max sequence | 6000 ns (Aquila) |
| Clock period | 4 ns |

All pulse timings must be multiples of the clock period.

---

## Zone Architecture (Advanced)

Modern FPQA designs divide the register into functional zones:

### Storage Zone
- Low decoherence
- No active gates
- Atoms parked between operations

### Entanglement Zone
- High-fidelity gate region
- Optimized laser alignment
- Atoms shuttled here for CZ gates

### Readout Zone
- Fluorescence imaging
- Atoms moved here for measurement
- Non-destructive measurement possible

**Constraint:** Atoms must be shuttled between zones for different operations. The validator ensures shuttle paths do not violate topological constraints.

---

## Error Summary

| Error Type | Cause | Fix |
|------------|-------|-----|
| `CollisionError` | Atoms too close | Increase spacing |
| `BlockadeDistanceError` | Gate atoms too far | Move atoms closer first |
| `VelocityExceededError` | Shuttle too fast | Increase duration |
| `TopologicalViolationError` | Invalid AOD crossing | Redesign movement path |
| `SlewRateError` | Pulse too sharp | Use smoother waveform |

---

## References

1. Evered et al., "High-fidelity gates in a neutral-atom quantum computer" (Nature 2023)
2. Bluvstein et al., "Logical quantum processor with reconfigurable atom arrays" (Nature 2024)
3. Pulser Documentation - Hardware Specifications
4. FPQA-C Compiler Paper (arXiv:2311.15123)

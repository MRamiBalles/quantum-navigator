# Physics Validator Engine

## Technical Report - v2.1

**Autor**: Equipo de Física Cuántica Aplicada  
**Fecha**: 3 de Febrero de 2026  
**Versión**: 2.1 (Zone-Aware Validation)

---

## 1. Resumen Ejecutivo

El `PulserValidator` es el motor de validación física del Quantum Navigator. Su función es garantizar que cualquier secuencia de operaciones cuánticas respete las restricciones físicas reales de un procesador de átomos neutros antes de enviarla al hardware o simulador.

### Misión Crítica

> Un job que pasa la validación debe ser físicamente ejecutable en hardware QuEra/Pasqal sin fallos catastróficos.

---

## 2. Arquitectura del Validador

```
PulserValidator
├── validate(job) → ValidationResult
│   ├── _validate_register_geometry()
│   ├── _validate_operation() × N
│   │   ├── _validate_shuttle()
│   │   ├── _validate_rydberg_gate()
│   │   ├── _validate_global_pulse_zones()
│   │   └── _validate_measurement_zones()
│   └── _check_temporal_overlaps()
└── ValidationResult
    ├── is_valid: bool
    ├── errors: list[PhysicsConstraintError]
    ├── warnings: list[ValidationWarning]
    ├── total_movement_distance: float
    └── estimated_decoherence_cost: float
```

---

## 3. Tipos de Error

### 3.1 Errores Fatales (PhysicsConstraintError)

| Error | Causa | Consecuencia Física |
|-------|-------|---------------------|
| `CollisionError` | Átomos < 4 µm | Pérdida de átomos por colisión |
| `TopologicalViolationError` | Cruce de filas/columnas AOD | Imposible físicamente |
| `VelocityExceededError` | Shuttle > 0.55 µm/µs | Calentamiento, pérdida de trampa |
| `BlockadeDistanceError` | CZ con átomos > 10 µm | No hay interacción Rydberg |
| `ZoneViolationError` | Puerta en zona incorrecta | Fallo de coherencia |

### 3.2 Advertencias (ValidationWarning)

| Código | Severidad | Significado |
|--------|-----------|-------------|
| `NEAR_COLLISION` | medium | Átomos cerca del límite (4-5 µm) |
| `MARGINAL_BLOCKADE` | medium | Átomos en borde del radio de bloqueo |
| `PULSE_IN_STORAGE_ZONE` | medium | Pulso afecta átomos en Storage |
| `PULSE_IN_SHIELDED_ZONE` | high | Pulso en zona blindada (fallará) |
| `MEASUREMENT_OUTSIDE_READOUT` | medium | Medición fuera de zona dedicada |
| `CONCURRENT_SHUTTLES` | high | Shuttles superpuestos temporalmente |

---

## 4. Detalle de Validaciones

### 4.1 Detección de Colisiones

**Algoritmo**: O(n²) pairwise distance check

```python
def _check_collisions(current_positions, min_distance):
    for i, j in combinations(atoms, 2):
        if distance(i, j) < min_distance:
            raise CollisionError(...)
```

**Parámetros Físicos**:
- `min_atom_distance`: 4.0 µm (default)
- Margen de seguridad recomendado: +1 µm

### 4.2 Validación de Shuttle AOD

**Restricciones Validadas**:

1. **Velocidad Máxima**:
   ```
   v = distance / duration
   if v > MAX_VELOCITY (0.55 µm/µs):
       raise VelocityExceededError
   ```

2. **Restricción Topológica**:
   - Los AODs están organizados en una grilla de trampas
   - Las filas y columnas NO pueden cruzarse físicamente
   - Validación: ordenamiento por Y (filas) y X (columnas) debe preservarse

3. **Colisiones Durante Movimiento**:
   - Verificación en puntos intermedios del trajectory
   - Interpolación lineal para `linear`, spline para `minimum_jerk`

### 4.3 Validación de Rydberg Gate

**Requisito Físico**: Los átomos deben estar dentro del radio de bloqueo Rydberg.

```python
def _validate_rydberg_gate(op, register, current_positions):
    d = distance(control, target)
    
    if d > register.blockade_radius:
        raise BlockadeDistanceError(
            f"Atoms too far for blockade: {d:.2f} µm > {register.blockade_radius} µm"
        )
    
    if d < register.min_atom_distance:
        raise CollisionError("Atoms too close")
```

**Física del Bloqueo Rydberg**:
- Interacción van der Waals: C₆/r⁶
- Radio típico: 6-10 µm para Rb-87
- Fidelidad de puerta > 99% requiere r < 0.8 × Rb

### 4.4 Validación de Zonas (v2.1)

**GlobalPulse**:
```python
if atom in STORAGE zone with shielding_light:
    warning("PULSE_IN_SHIELDED_ZONE", severity="high")
elif atom in STORAGE zone:
    warning("PULSE_IN_STORAGE_ZONE", severity="medium")
```

**Measurement**:
```python
if atom not in READOUT zone and READOUT zones exist:
    warning("MEASUREMENT_OUTSIDE_READOUT")
```

**Justificación Física**:
- El apantallamiento espectral desplaza los niveles Rydberg
- La luz de fluorescencia dispersa puede despolarizar átomos cercanos

---

## 5. Cálculo de Decoherencia

El validador estima el costo de decoherencia total de la secuencia:

```python
decoherence_cost = Σ (movement_time × DECOHERENCE_RATE)
                 + Σ (idle_time × IDLE_DECOHERENCE_RATE)
```

**Constantes Típicas**:
- `DECOHERENCE_RATE_PER_UM`: 0.001 (1% por µm de movimiento)
- `T2_TIME`: ~1000 µs para Rb-87 en MOT

---

## 6. Integración con Pipeline

```
Job Definition → Schema Validation → Physics Validation → Pulser Compilation
                      ↓                     ↓
                 Pydantic Errors      ValidationResult
                                           ↓
                                    [errors=0?] → Proceed
                                    [errors>0?] → Reject with details
```

---

## 7. Ejemplo de Uso

```python
from drivers.neutral_atom.validator import PulserValidator, validate_job

# Método 1: Función directa
result = validate_job(job)

if not result.is_valid:
    for error in result.errors:
        print(f"ERROR: {error}")

# Método 2: Instancia del validador
validator = PulserValidator()
result = validator.validate(job)

print(f"Decoherence estimate: {result.estimated_decoherence_cost:.3f}")
print(f"Total movement: {result.total_movement_distance:.2f} µm")
```

---

## 8. Extensibilidad

Para añadir nuevas validaciones:

1. Definir nuevo `PhysicsConstraintError` si es fatal
2. Añadir método `_validate_<operation_type>()` al validador
3. Actualizar `_validate_operation()` dispatch
4. Añadir tests correspondientes

---

## 9. References

1. Levine, H. et al. "High-Fidelity Control and Entanglement of Rydberg-Atom Qubits" PRL 2018
2. Evered, S. et al. "High-fidelity parallel entangling gates on a neutral-atom quantum computer" Nature 2023
3. Graham, T. et al. "Mid-circuit measurements on a neutral atom quantum computer" arXiv 2023

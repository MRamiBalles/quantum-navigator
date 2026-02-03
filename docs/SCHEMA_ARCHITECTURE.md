# Neutral Atom Schema Architecture

## Technical Report - v2.1

**Autor**: Equipo de Ingeniería Cuántica  
**Fecha**: 3 de Febrero de 2026  
**Versión**: 2.1 (Zoned Architecture)

---

## 1. Resumen Ejecutivo

Este documento describe la arquitectura del esquema de datos para el driver de átomos neutros del Quantum Navigator. El esquema está diseñado para capturar con precisión las restricciones físicas de los procesadores cuánticos basados en átomos neutros, particularmente los sistemas de tipo FPQA (Field-Programmable Qubit Arrays) desarrollados por Harvard/MIT/QuEra.

### Objetivos del Diseño

1. **Fidelidad Física**: Cada estructura de datos modela una realidad física (posiciones atómicas, pulsos, zonas funcionales)
2. **Validación Temprana**: Pydantic detecta errores de configuración antes de la compilación
3. **Compatibilidad Pulser**: Estructuras directamente traducibles al framework Pulser
4. **Extensibilidad**: Nuevos tipos de operación pueden añadirse sin modificar el núcleo

---

## 2. Jerarquía de Modelos

```
NeutralAtomJob
├── DeviceConfig (backend_id, shots)
├── NeutralAtomRegister
│   ├── AtomPosition[] (id, x, y, role)
│   └── ZoneDefinition[] (zone_id, zone_type, bounds)
├── NeutralAtomOperation[] (Union de 6 tipos)
│   ├── GlobalPulse
│   ├── LocalDetuning
│   ├── ShuttleMove
│   ├── RydbergGate
│   ├── Measurement
│   └── ShieldingEvent
└── SimulationConfig
```

---

## 3. Modelos Fundamentales

### 3.1 AtomPosition

| Campo | Tipo | Unidad | Restricción |
|-------|------|--------|-------------|
| `id` | int | - | ≥ 0, único |
| `x` | float | µm | -50 a 50 |
| `y` | float | µm | -50 a 50 |
| `role` | TrapRole | - | SLM, AOD, STORAGE |
| `aod_row` | Optional[int] | - | Para validación topológica |
| `aod_col` | Optional[int] | - | Para validación topológica |

**Justificación Física**:
- **SLM (Spatial Light Modulator)**: Trampas estáticas, posición fija durante toda la ejecución
- **AOD (Acousto-Optic Deflector)**: Trampas móviles, pueden transportar átomos entre zonas
- **STORAGE**: Rol específico para átomos en reserva (v2.1)

### 3.2 ZoneDefinition (v2.1)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `zone_id` | str | Identificador único |
| `zone_type` | ZoneType | STORAGE, ENTANGLEMENT, READOUT, PREPARATION, RESERVOIR, BUFFER |
| `x_min`, `x_max` | float | Límites horizontales en µm |
| `y_min`, `y_max` | float | Límites verticales en µm |
| `shielding_light` | bool | Si aplica apantallamiento espectral |

**Justificación Física (Harvard/MIT 2025)**:
- La separación espacial de zonas permite operación continua
- El shielding utiliza el efecto Autler-Townes (5P₃/₂ → 4D₅/₂)
- El reservorio proporciona recarga a ~300,000 átomos/segundo

---

## 4. Tipo de Operaciones

### 4.1 GlobalPulse

Pulso Rydberg global que afecta a todos los átomos en la zona de entrelazamiento.

```python
GlobalPulse(
    start_time=0,
    omega=WaveformSpec(type="blackman", duration=1000, area=3.14159),
    detuning=WaveformSpec(type="constant", duration=1000, value=0)
)
```

**Parámetros Críticos**:
- `duration`: 100ns - 10µs típico para puertas π
- `area`: Integral del pulso (π para NOT, π/2 para Hadamard)

### 4.2 ShuttleMove

Movimiento de átomos AOD para reconfiguración de geometría.

```python
ShuttleMove(
    atom_ids=[0, 1],
    start_time=1000,
    duration=2000,
    target_positions=[(10.0, 0.0), (15.0, 0.0)],
    trajectory="minimum_jerk"
)
```

**Restricciones Físicas**:
- Velocidad máxima: 0.55 µm/µs (para evitar calentamiento)
- Sin cruce de filas/columnas AOD (restricción topológica)
- Distancia mínima durante movimiento: 4 µm

### 4.3 RydbergGate

Puerta de dos qubits nativa basada en bloqueo Rydberg.

```python
RydbergGate(
    control_atom=0,
    target_atom=1,
    gate_type="CZ",
    start_time=3000
)
```

**Requisito**: Distancia entre átomos ≤ blockade_radius (típico 8 µm)

### 4.4 ShieldingEvent (v2.1)

Control dinámico del apantallamiento espectral.

```python
ShieldingEvent(
    start_time=0,
    duration=5000,
    zone_ids=["storage1"],
    mode="activate"
)
```

---

## 5. Validación de Esquema

### 5.1 Validación Automática (Pydantic)

- IDs de átomos únicos
- Posiciones target coinciden con atom_ids en ShuttleMove
- WaveformSpec tiene parámetros válidos según tipo
- Límites de zona (x_min < x_max, y_min < y_max)

### 5.2 Validación Física (PulserValidator)

- Detección de colisiones
- Velocidad de shuttle < límite
- Átomos de RydbergGate dentro del radio de bloqueo
- Operaciones en zonas correctas

---

## 6. Compatibilidad con Pulser

El esquema está diseñado para traducción directa a objetos Pulser:

| NeutralAtomJob | Pulser |
|----------------|--------|
| NeutralAtomRegister | Register |
| GlobalPulse | Sequence.add_pulse() |
| LocalDetuning | Sequence.target_local() |
| Measurement | Implicit (final state) |

---

## 7. Ejemplo Completo

```python
from drivers.neutral_atom.schema import *

job = NeutralAtomJob(
    device=DeviceConfig(backend_id="quera_simulator", shots=1000),
    register=NeutralAtomRegister(
        atoms=[
            AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.AOD),
            AtomPosition(id=1, x=6.0, y=0.0, role=TrapRole.SLM),
        ],
        zones=[
            ZoneDefinition(
                zone_id="entangle",
                zone_type=ZoneType.ENTANGLEMENT,
                x_min=-10, x_max=20, y_min=-10, y_max=10
            )
        ]
    ),
    operations=[
        GlobalPulse(
            start_time=0,
            omega=WaveformSpec(type=WaveformType.BLACKMAN, duration=1000, area=3.14159)
        ),
        RydbergGate(control_atom=0, target_atom=1, gate_type="CZ", start_time=1100),
        Measurement(start_time=2200, atom_ids=[0, 1])
    ]
)
```

---

## 8. Referencias

1. Bluvstein, D. et al. "A quantum processor based on coherent transport of entangled atom arrays" Nature, 2024
2. Harvard/MIT/QuEra. "Continuous-operation quantum computer demonstration" Nature, Oct 2025
3. Silverio, H. et al. "Pulser: An open-source package for programming neutral-atom devices"

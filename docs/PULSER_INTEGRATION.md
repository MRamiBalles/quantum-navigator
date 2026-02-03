# Pulser Integration Bridge

## Technical Report - v2.0

**Autor**: Equipo de Integración Cuántica  
**Fecha**: 3 de Febrero de 2026  
**Framework**: Pulser-Core by Pasqal

---

## 1. Resumen Ejecutivo

El `PulserAdapter` es el puente de traducción entre el esquema de datos de Quantum Navigator y el framework Pulser, la librería de referencia para programar dispositivos de átomos neutros. Esta integración permite a nuestros usuarios diseñar visualmente algoritmos cuánticos y ejecutarlos en simuladores o hardware real.

---

## 2. Arquitectura de Integración

```
Quantum Navigator                    Pulser Framework
─────────────────                    ────────────────
NeutralAtomJob      ─────────────▶   pulser.Sequence
├── Register        ─────────────▶   pulser.Register
├── Operations      ─────────────▶   Sequence.add_pulse()
│   ├── GlobalPulse ─────────────▶   .add("global", pulse, "ch")
│   ├── Shuttle     ─────────────▶   (Position update)
│   └── Measurement ─────────────▶   (Implicit)
└── Device          ─────────────▶   pulser.Device
```

---

## 3. Proceso de Compilación

### 3.1 Pipeline Completo

```
1. Schema Validation (Pydantic)
          ↓
2. Physics Validation (PulserValidator)
          ↓
3. Pulser Compilation (PulserAdapter)
          ↓
4. Execution (Simulator/Hardware)
          ↓
5. Result Processing
```

### 3.2 API del Adapter

```python
from drivers.neutral_atom.pulser_adapter import PulserAdapter, compile_and_run

# Compilación
adapter = PulserAdapter()
result = adapter.compile(job)

if result.success:
    sequence = result.sequence
    print(f"Compiled {len(job.operations)} operations")
else:
    print(f"Compilation failed: {result.errors}")

# Ejecución directa
run_result = compile_and_run(job, shots=1000)
print(f"Counts: {run_result.counts}")
```

---

## 4. Mapeo de Estructuras

### 4.1 Register → pulser.Register

```python
def _build_register(self, reg: NeutralAtomRegister) -> pulser.Register:
    qubits = {}
    for atom in reg.atoms:
        qubits[f"q{atom.id}"] = (atom.x, atom.y)
    return pulser.Register(qubits)
```

**Notas**:
- Coordenadas en µm (unidades Pulser)
- IDs se convierten a nombres tipo "q0", "q1"
- Roles (SLM/AOD) implícitos en el registro

### 4.2 GlobalPulse → Sequence Pulse

```python
def _add_global_pulse(self, seq, pulse: GlobalPulse):
    omega_wf = self._build_waveform(pulse.omega)
    delta_wf = self._build_waveform(pulse.detuning) if pulse.detuning else None
    
    combined_pulse = pulser.Pulse(
        amplitude=omega_wf,
        detuning=delta_wf or pulser.ConstantWaveform(0),
        phase=0
    )
    seq.add(combined_pulse, "rydberg_global")
```

### 4.3 WaveformSpec → pulser.Waveform

| Tipo QN | Pulser Waveform |
|---------|-----------------|
| CONSTANT | ConstantWaveform |
| BLACKMAN | BlackmanWaveform |
| GAUSSIAN | GaussianWaveform |
| INTERPOLATED | InterpolatedWaveform |

```python
def _build_waveform(self, spec: WaveformSpec) -> pulser.Waveform:
    if spec.type == WaveformType.BLACKMAN:
        return pulser.BlackmanWaveform(
            duration=spec.duration,
            area=spec.area
        )
    elif spec.type == WaveformType.CONSTANT:
        return pulser.ConstantWaveform(
            duration=spec.duration,
            value=spec.value
        )
    # ...
```

---

## 5. Manejo de Shuttle

El movimiento de átomos AOD requiere un tratamiento especial ya que Pulser no tiene un "shuttle" nativo. Implementamos esto como actualización del registro:

```python
def _apply_shuttle(self, current_register, move: ShuttleMove):
    new_positions = dict(current_register.qubits)
    
    for atom_id, (x, y) in zip(move.atom_ids, move.target_positions):
        new_positions[f"q{atom_id}"] = (x, y)
    
    return pulser.Register(new_positions)
```

**Limitación Conocida**: Pulser no simula la dinámica del transporte, solo la geometría final.

---

## 6. Configuración de Dispositivo

### 6.1 Dispositivos Soportados

| Backend ID | Pulser Device |
|------------|---------------|
| simulator | AnalogDevice |
| quera_aquila | Chadoq2 (proxy) |
| pasqal_orion | (Custom) |

```python
def _get_device(self, device_config: DeviceConfig) -> pulser.Device:
    if device_config.backend_id == "simulator":
        return pulser.devices.AnalogDevice
    elif device_config.backend_id == "quera_aquila":
        return pulser.devices.Chadoq2
    # ...
```

### 6.2 Parámetros del Dispositivo

```python
device = pulser.devices.AnalogDevice

# Límites típicos:
device.max_atom_num  # 256
device.min_atom_distance  # 4 µm
device.max_sequence_duration  # 4000 µs
device.rydberg_blockade_radius(...)  # Calculado
```

---

## 7. Simulación

### 7.1 Simulador QutipEmulator

```python
from drivers.neutral_atom.pulser_adapter import compile_and_run

result = compile_and_run(job, shots=1000)

# Acceder a resultados
print(result.counts)  # {'00': 523, '01': 12, '10': 8, '11': 457}
print(result.shots_executed)
```

### 7.2 Estado Cuántico Final

```python
# Para análisis detallado
simul = pulser.simulation.QutipEmulator.from_sequence(sequence)
state = simul.simulate().get_final_state()

# Componentes del estado
import qutip
state.shape  # (4,) para 2 qubits
```

---

## 8. Manejo de Errores

### 8.1 CompilationResult

```python
@dataclass
class CompilationResult:
    success: bool
    sequence: Optional[pulser.Sequence]
    errors: list[str]
    warnings: list[str]
    compilation_time_ms: float
```

### 8.2 Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `DeviceNotFoundError` | Backend desconocido | Verificar `backend_id` |
| `RegisterTooLargeError` | > 256 átomos | Dividir circuito |
| `SequenceTooLongError` | > 4ms total | Optimizar timing |
| `WaveformError` | Parámetros inválidos | Revisar WaveformSpec |

---

## 9. Extensiones Futuras

### 9.1 Soporte para DMM (Local Control)

```python
# Próxima versión
seq.config_detuning_map(local_weights)
seq.add_dmm_detuning(local_waveform, "local_ch")
```

### 9.2 Mediciones Mid-Circuit

Pulser v1.x no soporta mid-circuit measurement. Nuestro workaround:
1. Dividir secuencia en segmentos
2. Simular segmento 1
3. Medir y colapsar
4. Reiniciar con nuevo estado
5. Continuar segmento 2

---

## 10. Benchmarks

| Operación | Tiempo Compilación | Tiempo Simulación (10 qubits, 1000 shots) |
|-----------|-------------------|------------------------------------------|
| GlobalPulse simple | ~5 ms | ~200 ms |
| 5 operaciones | ~15 ms | ~500 ms |
| 10 + Shuttle | ~30 ms | ~800 ms |

---

## 11. Referencias

1. Silverio, H. et al. "Pulser: An open-source package for programming neutral-atom quantum devices" Quantum 2022
2. Pulser Documentation: https://pulser.readthedocs.io/
3. QuTiP: Quantum Toolbox in Python

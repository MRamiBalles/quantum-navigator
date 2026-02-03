"""
Quantum Navigator v2.0 - Neutral Atom JSON Schema
==================================================

Pydantic models for the technology-agnostic JSON IR (Intermediate Representation)
supporting analog/digital hybrid operations on neutral atom quantum processors.

Supported Hardware:
- Pasqal Fresnel/Orion (via Pulser)
- QuEra Aquila (via AWS Braket abstraction)

References:
- HPC-Inspired Blueprint for Technology-Agnostic Quantum Middle Layer (2025)
- FPQA-C Compiler Architecture
- Pulser Documentation (pasqal-io/Pulser)
"""

from __future__ import annotations
from typing import Literal, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
import math


# =============================================================================
# ENUMS
# =============================================================================

class TrapRole(str, Enum):
    """Role of atom trap in FPQA architecture."""
    SLM = "SLM"       # Static Light Modulator - fixed data qubits
    AOD = "AOD"       # Acousto-Optic Deflector - mobile shuttle qubits
    STORAGE = "STORAGE"  # Storage zone atoms


class LayoutType(str, Enum):
    """Predefined layout patterns for atom registers."""
    TRIANGULAR = "triangular"
    RECTANGULAR = "rectangular"
    HONEYCOMB = "honeycomb"
    ARBITRARY = "arbitrary"  # Custom XY coordinates


class ChannelType(str, Enum):
    """Pulser channel types for addressing atoms."""
    RYDBERG_GLOBAL = "rydberg_global"
    RYDBERG_LOCAL = "rydberg_local"
    RAMAN_LOCAL = "raman_local"
    DIGITAL = "digital"


class WaveformType(str, Enum):
    """Supported waveform shapes for analog pulses."""
    CONSTANT = "constant"
    BLACKMAN = "blackman"
    GAUSSIAN = "gaussian"
    INTERPOLATED = "interpolated"
    COMPOSITE = "composite"


class ZoneType(str, Enum):
    """
    Functional zones in zoned architecture (Harvard/MIT/QuEra 2025).
    
    Modern neutral atom processors divide the register into functional zones:
    - STORAGE: Atoms parked between operations, shielded from laser light
    - ENTANGLEMENT: Active gate zone where Rydberg pulses are applied
    - READOUT: Fluorescence imaging zone for measurements
    - BUFFER: Transition zone between others (optional)
    """
    STORAGE = "STORAGE"
    ENTANGLEMENT = "ENTANGLEMENT"
    READOUT = "READOUT"
    BUFFER = "BUFFER"


# =============================================================================
# GEOMETRY: Atom Register Definition
# =============================================================================

class AtomPosition(BaseModel):
    """Single atom position in the register."""
    id: int = Field(..., ge=0, description="Unique atom identifier")
    x: float = Field(..., description="X coordinate in micrometers")
    y: float = Field(..., description="Y coordinate in micrometers")
    role: TrapRole = Field(default=TrapRole.SLM, description="Trap type: SLM (static) or AOD (mobile)")
    
    # Optional: For AOD atoms, track their row/column in the AOD grid
    aod_row: Optional[int] = Field(default=None, description="AOD grid row (for topological validation)")
    aod_col: Optional[int] = Field(default=None, description="AOD grid column (for topological validation)")


class ZoneDefinition(BaseModel):
    """
    Defines a functional zone in the zoned architecture.
    
    Based on Harvard/MIT/QuEra 2025 continuous-operation processor design:
    - Atoms are shuttled between zones for different operations
    - Storage zone has shielding light to protect coherence
    - Entanglement zone is where Rydberg pulses are applied
    - Readout zone is where fluorescence measurement occurs
    """
    zone_id: str = Field(..., description="Unique zone identifier")
    zone_type: ZoneType = Field(..., description="Functional type of zone")
    
    # Bounding box in micrometers
    x_min: float = Field(..., description="Left boundary in µm")
    x_max: float = Field(..., description="Right boundary in µm")
    y_min: float = Field(..., description="Bottom boundary in µm")
    y_max: float = Field(..., description="Top boundary in µm")
    
    # Zone-specific properties
    shielding_light: bool = Field(
        default=False, 
        description="If True, zone has shielding light (reduces gate fidelity but protects storage)"
    )
    
    @model_validator(mode='after')
    def validate_bounds(self) -> 'ZoneDefinition':
        """Ensure bounds are valid."""
        if self.x_min >= self.x_max:
            raise ValueError(f"Zone {self.zone_id}: x_min must be < x_max")
        if self.y_min >= self.y_max:
            raise ValueError(f"Zone {self.zone_id}: y_min must be < y_max")
        return self
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside this zone."""
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max
    
    def contains_atom(self, atom: 'AtomPosition') -> bool:
        """Check if an atom is inside this zone."""
        return self.contains_point(atom.x, atom.y)


class NeutralAtomRegister(BaseModel):
    """
    Defines the spatial arrangement of atoms in the quantum register.
    
    Key constraints enforced:
    - min_atom_distance: Minimum separation to avoid collisions (~4 µm)
    - blockade_radius: Rydberg blockade radius for entanglement (~6-10 µm)
    
    Zoned Architecture (v2.1):
    - Optional zones define functional regions (Storage, Entanglement, Readout)
    - Operations are validated against zone types
    """
    layout_type: LayoutType = Field(default=LayoutType.ARBITRARY)
    min_atom_distance: float = Field(default=4.0, ge=1.0, le=20.0, 
                                      description="Minimum inter-atom distance in µm")
    blockade_radius: float = Field(default=8.0, ge=4.0, le=15.0,
                                    description="Rydberg blockade radius in µm")
    atoms: list[AtomPosition] = Field(..., min_length=1, max_length=256,
                                       description="List of atom positions")
    
    # Zoned architecture (optional for backward compatibility)
    zones: Optional[list[ZoneDefinition]] = Field(
        default=None,
        description="Functional zones (Storage, Entanglement, Readout). If None, entire canvas is Entanglement zone."
    )
    
    @field_validator('atoms')
    @classmethod
    def validate_unique_ids(cls, atoms: list[AtomPosition]) -> list[AtomPosition]:
        """Ensure all atom IDs are unique."""
        ids = [a.id for a in atoms]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate atom IDs detected in register")
        return atoms
    
    def get_atom_by_id(self, atom_id: int) -> Optional[AtomPosition]:
        """Retrieve atom by its ID."""
        for atom in self.atoms:
            if atom.id == atom_id:
                return atom
        return None
    
    def get_aod_atoms(self) -> list[AtomPosition]:
        """Get all mobile (AOD) atoms."""
        return [a for a in self.atoms if a.role == TrapRole.AOD]
    
    def get_slm_atoms(self) -> list[AtomPosition]:
        """Get all static (SLM) atoms."""
        return [a for a in self.atoms if a.role == TrapRole.SLM]
    
    def get_zone_at_position(self, x: float, y: float) -> Optional[ZoneDefinition]:
        """Get the zone containing a given position (first match)."""
        if self.zones is None:
            return None
        for zone in self.zones:
            if zone.contains_point(x, y):
                return zone
        return None
    
    def get_atom_zone(self, atom_id: int) -> Optional[ZoneDefinition]:
        """Get the zone containing a specific atom."""
        atom = self.get_atom_by_id(atom_id)
        if atom is None:
            return None
        return self.get_zone_at_position(atom.x, atom.y)
    
    def get_zones_by_type(self, zone_type: ZoneType) -> list[ZoneDefinition]:
        """Get all zones of a specific type."""
        if self.zones is None:
            return []
        return [z for z in self.zones if z.zone_type == zone_type]


# =============================================================================
# WAVEFORMS: Analog Pulse Shapes
# =============================================================================

class WaveformSpec(BaseModel):
    """Specification for pulse waveform shape."""
    type: WaveformType = Field(...)
    duration: float = Field(..., gt=0, description="Duration in nanoseconds")
    
    # Type-specific parameters
    amplitude: Optional[float] = Field(default=None, description="For constant waveforms (rad/µs)")
    area: Optional[float] = Field(default=None, description="For Blackman/Gaussian (rad)")
    
    # For interpolated waveforms
    times: Optional[list[float]] = Field(default=None, description="Time points in ns")
    values: Optional[list[float]] = Field(default=None, description="Amplitude values")
    
    @model_validator(mode='after')
    def validate_waveform_params(self) -> 'WaveformSpec':
        """Validate that required params are present for each waveform type."""
        if self.type == WaveformType.CONSTANT and self.amplitude is None:
            raise ValueError("Constant waveform requires 'amplitude'")
        if self.type in (WaveformType.BLACKMAN, WaveformType.GAUSSIAN) and self.area is None:
            raise ValueError(f"{self.type.value} waveform requires 'area'")
        if self.type == WaveformType.INTERPOLATED:
            if self.times is None or self.values is None:
                raise ValueError("Interpolated waveform requires 'times' and 'values'")
            if len(self.times) != len(self.values):
                raise ValueError("times and values must have same length")
        return self


# =============================================================================
# OPERATIONS: Native Neutral Atom Instructions
# =============================================================================

class GlobalPulse(BaseModel):
    """
    Global Rydberg pulse applied to ALL atoms simultaneously.
    
    Implements Hamiltonian: H = (Ω/2)Σ|g⟩⟨r| + h.c. - ΔΣn_r
    """
    op_type: Literal["global_pulse"] = "global_pulse"
    channel: ChannelType = Field(default=ChannelType.RYDBERG_GLOBAL)
    start_time: float = Field(..., ge=0, description="Start time in ns")
    
    # Rabi frequency Ω(t)
    omega: WaveformSpec = Field(..., description="Rabi frequency waveform")
    
    # Detuning Δ(t) - optional, defaults to 0
    detuning: Optional[WaveformSpec] = Field(default=None, description="Detuning waveform")
    
    # Phase φ - typically constant
    phase: float = Field(default=0.0, ge=0, lt=2*math.pi, description="Phase in radians")


class LocalDetuning(BaseModel):
    """
    Local detuning applied to specific atoms using DMD or local beams.
    Used for targeted addressing in digital-analog hybrid mode.
    """
    op_type: Literal["local_detuning"] = "local_detuning"
    channel: ChannelType = Field(default=ChannelType.RAMAN_LOCAL)
    target_atoms: list[int] = Field(..., min_length=1, description="Atom IDs to address")
    start_time: float = Field(..., ge=0, description="Start time in ns")
    
    detuning: WaveformSpec = Field(..., description="Local detuning waveform")
    
    # Weights for each targeted atom (optional, for DMD patterns)
    weights: Optional[list[float]] = Field(default=None, description="Relative weights per atom")
    
    @model_validator(mode='after')
    def validate_weights(self) -> 'LocalDetuning':
        """If weights provided, must match target_atoms length."""
        if self.weights is not None and len(self.weights) != len(self.target_atoms):
            raise ValueError("weights must have same length as target_atoms")
        return self


class ShuttleMove(BaseModel):
    """
    AOD atom movement operation for FPQA reconfiguration.
    
    Critical constraints (validated by PulserValidator):
    - Max velocity: ~0.55 µm/µs to avoid heating
    - No row/column crossing in AOD grid (topological constraint)
    - Atoms must not collide during movement
    """
    op_type: Literal["shuttle"] = "shuttle"
    atom_ids: list[int] = Field(..., min_length=1, description="AOD atom IDs to move")
    start_time: float = Field(..., ge=0, description="Start time in ns")
    duration: float = Field(..., gt=0, description="Movement duration in ns")
    
    # Target positions after movement
    target_positions: list[tuple[float, float]] = Field(..., 
        description="Target (x, y) coordinates in µm for each atom")
    
    # Movement profile (affects heating)
    trajectory: Literal["linear", "minimum_jerk", "sine"] = Field(
        default="minimum_jerk", 
        description="Motion profile - minimum_jerk reduces heating"
    )
    
    @model_validator(mode='after')
    def validate_positions_match(self) -> 'ShuttleMove':
        """Target positions must match number of atoms."""
        if len(self.target_positions) != len(self.atom_ids):
            raise ValueError("target_positions must match atom_ids length")
        return self


class RydbergGate(BaseModel):
    """
    Native two-qubit Rydberg gate (CZ-equivalent via blockade).
    
    Requires atoms to be within blockade_radius for entanglement.
    """
    op_type: Literal["rydberg_gate"] = "rydberg_gate"
    control_atom: int = Field(..., description="Control atom ID")
    target_atom: int = Field(..., description="Target atom ID")
    start_time: float = Field(..., ge=0, description="Start time in ns")
    
    # Gate parameters
    gate_type: Literal["CZ", "CPHASE"] = Field(default="CZ")
    phase: Optional[float] = Field(default=None, description="For CPHASE, the accumulated phase")
    
    # Pulse specification (optional - can use device defaults)
    pulse: Optional[WaveformSpec] = Field(default=None, description="Custom gate pulse")


class Measurement(BaseModel):
    """
    Projective measurement in computational basis.
    Neutral atoms: fluorescence imaging of ground vs Rydberg state.
    """
    op_type: Literal["measure"] = "measure"
    atom_ids: list[int] = Field(..., min_length=1, description="Atoms to measure")
    start_time: float = Field(..., ge=0, description="Measurement start time in ns")
    
    # Measurement configuration
    basis: Literal["computational", "x", "y"] = Field(default="computational")
    

# Union type for all operations
NeutralAtomOperation = Union[
    GlobalPulse,
    LocalDetuning, 
    ShuttleMove,
    RydbergGate,
    Measurement
]


# =============================================================================
# TOP-LEVEL JOB SCHEMA
# =============================================================================

class DeviceConfig(BaseModel):
    """Hardware device configuration."""
    backend_id: str = Field(..., description="Device identifier (e.g., 'pasqal_fresnel', 'quera_aquila')")
    
    # Optional overrides for device defaults
    max_omega: Optional[float] = Field(default=None, description="Max Rabi frequency (rad/µs)")
    max_detuning: Optional[float] = Field(default=None, description="Max detuning (rad/µs)")
    max_aod_velocity: Optional[float] = Field(default=0.55, description="Max AOD velocity (µm/µs)")


class SimulationConfig(BaseModel):
    """Configuration for simulation backend selection."""
    backend: Literal["qutip", "tensor_network", "braket", "hardware"] = Field(default="qutip")
    
    # Tensor network specific
    max_bond_dimension: Optional[int] = Field(default=128, description="For TN backends")
    
    # Number of shots for sampling
    shots: int = Field(default=1000, ge=1, le=100000)
    
    # Return observables beyond bitstrings
    compute_energy: bool = Field(default=False, description="Compute Hamiltonian expectation value")
    compute_correlations: bool = Field(default=False, description="Compute two-point correlators")


class NeutralAtomJob(BaseModel):
    """
    Complete job specification for neutral atom quantum processor.
    
    This is the top-level JSON IR that the Quantum Middle Layer accepts
    for neutral atom backends.
    """
    # Metadata
    job_id: Optional[str] = Field(default=None, description="Unique job identifier")
    name: Optional[str] = Field(default=None, description="Human-readable job name")
    version: str = Field(default="2.0", description="Schema version")
    
    # Hardware target
    device: DeviceConfig = Field(...)
    
    # Quantum register geometry
    register: NeutralAtomRegister = Field(...)
    
    # Sequence of operations (ordered by start_time)
    operations: list[NeutralAtomOperation] = Field(..., min_length=1)
    
    # Simulation/execution config
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    
    @model_validator(mode='after')
    def validate_operation_atoms_exist(self) -> 'NeutralAtomJob':
        """Ensure all referenced atom IDs exist in the register."""
        valid_ids = {a.id for a in self.register.atoms}
        
        for op in self.operations:
            referenced_ids = set()
            
            if hasattr(op, 'target_atoms'):
                referenced_ids.update(op.target_atoms)
            if hasattr(op, 'atom_ids'):
                referenced_ids.update(op.atom_ids)
            if hasattr(op, 'control_atom'):
                referenced_ids.add(op.control_atom)
            if hasattr(op, 'target_atom'):
                referenced_ids.add(op.target_atom)
                
            invalid = referenced_ids - valid_ids
            if invalid:
                raise ValueError(f"Operation references non-existent atom IDs: {invalid}")
        
        return self
    
    def get_total_duration(self) -> float:
        """Calculate total sequence duration in ns."""
        max_end = 0.0
        for op in self.operations:
            start = op.start_time
            duration = 0.0
            
            if hasattr(op, 'duration'):
                duration = op.duration
            elif hasattr(op, 'omega'):
                duration = op.omega.duration
            elif hasattr(op, 'detuning') and op.detuning:
                duration = op.detuning.duration
                
            max_end = max(max_end, start + duration)
        
        return max_end


# =============================================================================
# JSON EXPORT EXAMPLE
# =============================================================================

def create_example_job() -> NeutralAtomJob:
    """Create an example MIS (Maximum Independent Set) job for testing."""
    return NeutralAtomJob(
        name="MIS Demo - 4 atoms",
        device=DeviceConfig(backend_id="pasqal_fresnel"),
        register=NeutralAtomRegister(
            layout_type=LayoutType.ARBITRARY,
            min_atom_distance=4.0,
            blockade_radius=8.0,
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.SLM),
                AtomPosition(id=1, x=6.0, y=0.0, role=TrapRole.SLM),
                AtomPosition(id=2, x=3.0, y=5.2, role=TrapRole.SLM),
                AtomPosition(id=3, x=9.0, y=5.2, role=TrapRole.AOD, aod_row=0, aod_col=0),
            ]
        ),
        operations=[
            GlobalPulse(
                start_time=0,
                omega=WaveformSpec(type=WaveformType.BLACKMAN, duration=1000, area=3.14159),
                detuning=WaveformSpec(type=WaveformType.CONSTANT, duration=1000, amplitude=-5.0),
                phase=0.0
            ),
            Measurement(
                start_time=1100,
                atom_ids=[0, 1, 2, 3]
            )
        ],
        simulation=SimulationConfig(
            backend="qutip",
            shots=1000,
            compute_energy=True
        )
    )


if __name__ == "__main__":
    # Export example schema
    import json
    example = create_example_job()
    print(json.dumps(example.model_dump(), indent=2))

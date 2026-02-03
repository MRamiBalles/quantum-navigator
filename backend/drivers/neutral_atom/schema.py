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
    """
    Role of atom trap in FPQA architecture.
    
    v3.0 Roles:
    - SLM: Static data qubits (fixed position)
    - AOD: Mobile shuttle qubits (general)
    - BUS: Flying ancilla qubits - specialized AOD atoms that act as
           entanglement messengers between fixed data qubits
    - STORAGE: Atoms in storage zone (shielded)
    """
    SLM = "SLM"       # Static Light Modulator - fixed data qubits
    AOD = "AOD"       # Acousto-Optic Deflector - mobile qubits
    BUS = "BUS"       # Flying ancilla - entanglement messenger (v3.0)
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
    - PREPARATION: Initial loading from MOT, cooling, and rearrangement
    - RESERVOIR: Atom reservoir for continuous replenishment (~300k atoms/s)
    - BUFFER: Transition zone between others (optional)
    """
    STORAGE = "STORAGE"
    ENTANGLEMENT = "ENTANGLEMENT"
    READOUT = "READOUT"
    PREPARATION = "PREPARATION"
    RESERVOIR = "RESERVOIR"
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


class HeatingModel(BaseModel):
    """
    Vibrational heating model for AOD atom transport (v3.0).
    
    Based on Harvard/MIT 2025 continuous-operation research:
    - Movement causes vibrational excitation (n_vib increase)
    - Higher n_vib degrades two-qubit gate fidelity
    - Critical threshold: n_vib > 18 causes significant fidelity loss
    
    Physics:
        Δn_vib ∝ distance × velocity
        F_2Q ≈ 1 - α × n_vib  (simplified linear model)
    """
    
    # Heating coefficients (empirical from Harvard 2025)
    heating_coefficient: float = Field(
        default=0.01,
        description="n_vib increase per µm×(µm/µs) - empirical factor"
    )
    
    critical_nvib: float = Field(
        default=18.0,
        description="n_vib threshold above which fidelity loss is severe"
    )
    
    fidelity_degradation_rate: float = Field(
        default=0.008,
        description="Fidelity loss per unit n_vib (F = 1 - α×n_vib)"
    )
    
    @staticmethod
    def calculate_nvib_increase(
        distance_um: float,
        velocity_um_per_us: float,
        heating_coeff: float = 0.01
    ) -> float:
        """
        Calculate vibrational number increase from movement.
        
        Args:
            distance_um: Movement distance in micrometers
            velocity_um_per_us: Movement velocity in µm/µs
            heating_coeff: Empirical heating coefficient
        
        Returns:
            Δn_vib: Increase in vibrational quantum number
        """
        return heating_coeff * distance_um * velocity_um_per_us
    
    @staticmethod
    def estimate_fidelity_loss(
        delta_nvib: float,
        degradation_rate: float = 0.008
    ) -> float:
        """
        Estimate gate fidelity loss from vibrational heating.
        
        Returns:
            fidelity_loss: Fractional loss (0.0 to 1.0)
        """
        return min(1.0, degradation_rate * delta_nvib)


class AtomLossModel(BaseModel):
    """
    Probabilistic atom loss model (v3.0).
    
    Atoms can be lost due to:
    - Background gas collisions
    - Excessive heating during transport
    - Scattering from Rydberg light
    """
    
    # Loss probability per movement
    base_loss_rate: float = Field(
        default=0.001,
        description="Base probability of atom loss per shuttle operation"
    )
    
    heating_loss_factor: float = Field(
        default=0.005,
        description="Additional loss probability per unit n_vib above threshold"
    )
    
    @staticmethod
    def calculate_loss_probability(
        nvib: float,
        nvib_threshold: float = 18.0,
        base_rate: float = 0.001,
        heating_factor: float = 0.005
    ) -> float:
        """
        Calculate atom loss probability.
        
        Args:
            nvib: Current vibrational number
            nvib_threshold: n_vib above which heating contributes to loss
            base_rate: Base loss probability
            heating_factor: Additional loss per unit n_vib above threshold
        
        Returns:
            p_loss: Probability of atom loss (0.0 to 1.0)
        """
        excess_nvib = max(0, nvib - nvib_threshold)
        return min(1.0, base_rate + heating_factor * excess_nvib)


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


class ShieldingEvent(BaseModel):
    """
    Dynamic spectral shielding control (Harvard/MIT 2025).
    
    Activates/deactivates the auxiliary laser (5P₃/₂ → 4D₅/₂ transition)
    that shifts Rydberg levels via Autler-Townes effect, protecting
    atoms from scattered Rydberg light during loading/readout phases.
    """
    op_type: Literal["shielding"] = "shielding"
    start_time: float = Field(..., ge=0, description="Start time in ns")
    duration: float = Field(..., gt=0, description="Shielding duration in ns")
    
    # Target zones or atoms
    zone_ids: Optional[list[str]] = Field(default=None, description="Zones to shield")
    atom_ids: Optional[list[int]] = Field(default=None, description="Specific atoms to shield")
    
    # Shielding mode
    mode: Literal["activate", "deactivate"] = Field(default="activate")


class ReloadOperation(BaseModel):
    """
    Atom replenishment operation for continuous operation (v4.0).
    
    Based on Harvard/MIT/QuEra Nature 2025 continuous-operation processor:
    - Atoms are periodically loaded from reservoir to replace lost qubits
    - Replenishment rate: ~30,000 qubits/second
    - Fresh atoms are moved from Reservoir → Preparation → Storage zones
    
    This operation models the "replenishment cycle" that enables
    arbitrarily long quantum computations without qubit exhaustion.
    """
    op_type: Literal["reload"] = "reload"
    start_time: float = Field(..., ge=0, description="Start time in ns")
    
    # Target slots for replenishment
    target_slots: list[int] = Field(
        ..., 
        min_length=1,
        description="Atom slot IDs to replenish (must be empty or lost atoms)"
    )
    
    # Source zone (typically reservoir or preparation)
    source_zone: str = Field(
        default="reservoir",
        description="Zone from which fresh atoms are loaded"
    )
    
    # Timing parameters
    loading_duration_ns: float = Field(
        default=50_000.0,  # 50 µs typical loading time
        gt=0,
        description="Time to load and transport fresh atom"
    )
    
    # Cooling after reload
    post_cooling: bool = Field(
        default=True,
        description="Apply cooling before computation (resets n_vib)"
    )
    
    @property
    def replenishment_rate_per_second(self) -> float:
        """Calculate replenishment rate based on loading duration."""
        return 1e9 / self.loading_duration_ns  # atoms/second


class ContinuousOperationConfig(BaseModel):
    """
    Configuration for continuous operation mode (v4.0).
    
    Enables arbitrarily long computations by:
    - Tracking atom survival across operations
    - Scheduling automatic replenishment when atoms are lost
    - Managing reservoir depletion
    
    Reference: Nature 2025 - 3,000 qubit continuous operation
    """
    enabled: bool = Field(
        default=False,
        description="Enable continuous operation mode"
    )
    
    # Reservoir parameters
    reservoir_size: int = Field(
        default=300_000,
        ge=1000,
        description="Total atoms available in reservoir"
    )
    
    replenishment_rate: float = Field(
        default=30_000.0,
        gt=0,
        description="Atoms replenished per second"
    )
    
    # Automatic reload triggers
    auto_reload_threshold: float = Field(
        default=0.05,
        ge=0.01,
        le=0.5,
        description="Trigger reload when atom loss probability > threshold"
    )
    
    # Sustainable depth calculation
    target_fidelity: float = Field(
        default=0.90,
        ge=0.5,
        le=0.99,
        description="Target cumulative fidelity for sustainable operation"
    )


# Union type for all operations
NeutralAtomOperation = Union[
    GlobalPulse,
    LocalDetuning, 
    ShuttleMove,
    RydbergGate,
    Measurement,
    ShieldingEvent,
    ReloadOperation  # v4.0: Continuous operation
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


# =============================================================================
# SUSTAINABLE DEPTH ANALYSIS (v4.0)
# =============================================================================

class SustainableDepthAnalysis(BaseModel):
    """
    Predicts sustainable circuit depth before atom replenishment is required.
    
    Based on HeatingModel and AtomLossModel, calculates:
    - Maximum gates before cumulative fidelity drops below threshold
    - Time until atom loss probability exceeds safety limit
    - Required replenishment rate for target depth
    
    This metric is critical for designing long-running algorithms
    like quantum error correction and variational optimization.
    """
    
    # Input parameters
    avg_transport_distance_um: float = Field(
        default=15.0,
        gt=0,
        description="Average atom transport distance per gate layer"
    )
    
    transport_velocity_um_per_us: float = Field(
        default=0.40,
        gt=0,
        le=0.55,
        description="Transport velocity (should be below thermal limit)"
    )
    
    gate_time_ns: float = Field(
        default=1000.0,
        gt=0,
        description="Average two-qubit gate duration"
    )
    
    num_data_qubits: int = Field(
        default=100,
        ge=1,
        description="Number of data qubits in computation"
    )
    
    # Thresholds
    fidelity_threshold: float = Field(
        default=0.90,
        ge=0.5,
        le=0.99,
        description="Minimum acceptable cumulative fidelity"
    )
    
    loss_threshold: float = Field(
        default=0.10,
        ge=0.01,
        le=0.5,
        description="Maximum acceptable atom loss probability"
    )
    
    def calculate_sustainable_depth(self) -> dict:
        """
        Calculate sustainable circuit depth metrics.
        
        Returns:
            dict with:
                - max_layers_fidelity: Layers before fidelity drops below threshold
                - max_layers_loss: Layers before loss probability exceeds threshold
                - sustainable_depth: min(max_layers_fidelity, max_layers_loss)
                - time_to_replacement_ms: Time before replenishment needed
                - required_replenishment_rate: Atoms/second needed for indefinite operation
        """
        from .schema import HeatingModel, AtomLossModel
        
        # Calculate heating per layer
        delta_nvib_per_layer = HeatingModel.calculate_nvib_increase(
            self.avg_transport_distance_um,
            self.transport_velocity_um_per_us
        )
        
        # Calculate layers until fidelity threshold
        # F_cumulative = (1 - alpha * delta_nvib)^n_layers
        # Solve for n when F_cumulative = fidelity_threshold
        alpha = 0.008  # Fidelity degradation rate
        fidelity_loss_per_layer = alpha * delta_nvib_per_layer
        
        if fidelity_loss_per_layer > 0:
            import math
            max_layers_fidelity = int(
                math.log(self.fidelity_threshold) / 
                math.log(1 - fidelity_loss_per_layer)
            )
        else:
            max_layers_fidelity = float('inf')
        
        # Calculate layers until loss threshold
        # P_loss_cumulative increases with n_vib
        # Simplified: find layer where P_loss > loss_threshold
        nvib_for_loss = 18.0 + (self.loss_threshold - 0.001) / 0.005
        max_layers_loss = int(nvib_for_loss / delta_nvib_per_layer) if delta_nvib_per_layer > 0 else float('inf')
        
        # Sustainable depth is the minimum
        sustainable_depth = min(max_layers_fidelity, max_layers_loss)
        
        # Time calculation
        layer_time_ns = (
            self.avg_transport_distance_um / self.transport_velocity_um_per_us * 1000 +
            self.gate_time_ns
        )
        time_to_replacement_ms = (sustainable_depth * layer_time_ns) / 1_000_000
        
        # Required replenishment rate for indefinite operation
        p_loss_at_depth = AtomLossModel.calculate_loss_probability(
            sustainable_depth * delta_nvib_per_layer
        )
        atoms_lost_per_cycle = self.num_data_qubits * p_loss_at_depth
        cycle_time_s = time_to_replacement_ms / 1000
        required_rate = atoms_lost_per_cycle / cycle_time_s if cycle_time_s > 0 else 0
        
        return {
            'max_layers_fidelity': max_layers_fidelity,
            'max_layers_loss': max_layers_loss,
            'sustainable_depth': sustainable_depth,
            'time_to_replacement_ms': time_to_replacement_ms,
            'required_replenishment_rate': required_rate,
            'delta_nvib_per_layer': delta_nvib_per_layer,
            'layer_time_ns': layer_time_ns
        }


if __name__ == "__main__":
    # Export example schema
    import json
    example = create_example_job()
    print(json.dumps(example.model_dump(), indent=2))

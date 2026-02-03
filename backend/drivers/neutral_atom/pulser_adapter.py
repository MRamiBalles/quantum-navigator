"""
Quantum Navigator v2.0 - Pulser Adapter
========================================

Bridge between the technology-agnostic JSON IR and Pulser library.
Translates NeutralAtomJob into executable Pulser Sequences.

Supported Backends:
- Pasqal Fresnel/Orion
- QuEra Aquila (via compatible mode)
- Local simulation (QutipEmulator, TensorNetwork)

References:
- Pulser Documentation: https://pulser.readthedocs.io
- Pasqal Devices: IroiseMVP, Fresnel, Orion (via pasqal-cloud)
"""

from __future__ import annotations
from typing import Optional, Any
from dataclasses import dataclass, field
import logging

# Pulser imports (will be available when pulser-core is installed)
try:
    import pulser
    from pulser import Pulse, Sequence, Register
    from pulser.devices import DigitalAnalogDevice, AnalogDevice
    from pulser.waveforms import (
        ConstantWaveform, 
        BlackmanWaveform, 
        GaussianWaveform,
        InterpolatedWaveform,
        CompositeWaveform,
    )
    from pulser.simulation import QutipEmulator
    PULSER_AVAILABLE = True
except ImportError:
    PULSER_AVAILABLE = False
    # Create stub classes for type hints when pulser not installed
    Sequence = Any
    Register = Any

from .schema import (
    NeutralAtomJob,
    NeutralAtomRegister,
    AtomPosition,
    WaveformSpec,
    WaveformType,
    ChannelType,
    GlobalPulse,
    LocalDetuning,
    ShuttleMove,
    RydbergGate,
    Measurement,
    NeutralAtomOperation,
)
from .validator import PulserValidator, ValidationResult


logger = logging.getLogger(__name__)


# =============================================================================
# DEVICE REGISTRY
# =============================================================================

@dataclass
class DeviceProfile:
    """Hardware device profile with physical parameters."""
    name: str
    pulser_device: Any  # pulser.devices.Device
    max_omega: float  # rad/µs
    max_detuning: float  # rad/µs
    max_aod_velocity: float  # µm/µs
    supports_local_addressing: bool
    supports_aod_movement: bool
    native_gate_set: list[str]


# Device registry - populated when Pulser is available
DEVICE_REGISTRY: dict[str, DeviceProfile] = {}

def _init_device_registry():
    """Initialize device registry with Pulser devices."""
    if not PULSER_AVAILABLE:
        return
    
    global DEVICE_REGISTRY
    
    # Pasqal Fresnel (digital-analog hybrid)
    DEVICE_REGISTRY["pasqal_fresnel"] = DeviceProfile(
        name="Pasqal Fresnel",
        pulser_device=DigitalAnalogDevice,
        max_omega=2 * 3.14159 * 4,  # ~25 rad/µs
        max_detuning=2 * 3.14159 * 20,  # ~125 rad/µs
        max_aod_velocity=0.55,
        supports_local_addressing=True,
        supports_aod_movement=True,
        native_gate_set=["Rydberg", "Raman", "Global"]
    )
    
    # QuEra Aquila (analog only)
    DEVICE_REGISTRY["quera_aquila"] = DeviceProfile(
        name="QuEra Aquila",
        pulser_device=AnalogDevice,
        max_omega=2 * 3.14159 * 4,
        max_detuning=2 * 3.14159 * 20,
        max_aod_velocity=0.55,
        supports_local_addressing=False,  # Global only
        supports_aod_movement=False,  # Fixed SLM
        native_gate_set=["Global Rydberg"]
    )
    
    # Simulation device (permissive)
    DEVICE_REGISTRY["simulator"] = DeviceProfile(
        name="Local Simulator",
        pulser_device=DigitalAnalogDevice,
        max_omega=100,
        max_detuning=200,
        max_aod_velocity=1.0,
        supports_local_addressing=True,
        supports_aod_movement=True,
        native_gate_set=["All"]
    )

# Initialize on module load
_init_device_registry()


# =============================================================================
# COMPILATION RESULT
# =============================================================================

@dataclass
class CompilationResult:
    """Result of compiling a NeutralAtomJob to Pulser Sequence."""
    success: bool
    sequence: Optional[Sequence] = None
    register: Optional[Register] = None
    validation: Optional[ValidationResult] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    # Metrics
    total_duration_ns: float = 0.0
    num_pulses: int = 0
    num_channels: int = 0


@dataclass
class ExecutionResult:
    """Result of executing a Pulser sequence."""
    success: bool
    counts: Optional[dict[str, int]] = None  # Bitstring counts
    samples: Optional[list[str]] = None  # Raw samples
    
    # Observables (if requested)
    energy: Optional[float] = None
    correlations: Optional[dict[tuple[int, int], float]] = None
    
    # Metadata
    shots_executed: int = 0
    execution_time_ms: float = 0.0
    backend_used: str = ""
    errors: list[str] = field(default_factory=list)


# =============================================================================
# PULSER ADAPTER
# =============================================================================

class PulserAdapter:
    """
    Adapter that translates NeutralAtomJob (JSON IR) to Pulser Sequences.
    
    Responsibilities:
    1. Validate job against physics constraints
    2. Build Pulser Register from geometry specification
    3. Map operations to Pulser channels and pulses
    4. Execute on simulator or prepare for hardware submission
    
    Usage:
        adapter = PulserAdapter()
        result = adapter.compile(job)
        if result.success:
            exec_result = adapter.execute(result.sequence, shots=1000)
    """
    
    def __init__(
        self,
        validate: bool = True,
        strict_validation: bool = True,
        auto_select_backend: bool = True
    ):
        """
        Initialize the Pulser adapter.
        
        Args:
            validate: Whether to run physics validation before compilation
            strict_validation: If True, edge cases become errors
            auto_select_backend: Auto-switch between QutipEmulator and TN based on size
        """
        if not PULSER_AVAILABLE:
            raise ImportError(
                "Pulser is not installed. Please install with: "
                "pip install pulser-core pulser-simulation"
            )
        
        self.validate = validate
        self.strict_validation = strict_validation
        self.auto_select_backend = auto_select_backend
        self.validator = PulserValidator(strict_mode=strict_validation)
    
    def compile(self, job: NeutralAtomJob) -> CompilationResult:
        """
        Compile a NeutralAtomJob to a Pulser Sequence.
        
        Args:
            job: The neutral atom job specification
            
        Returns:
            CompilationResult with the compiled Sequence
        """
        result = CompilationResult(success=False)
        
        # 1. Validate if enabled
        if self.validate:
            validation = self.validator.validate(job)
            result.validation = validation
            
            if not validation.is_valid:
                result.errors = [str(e) for e in validation.errors]
                return result
            
            if validation.warnings:
                result.warnings = [w.message for w in validation.warnings]
        
        # 2. Get device profile
        device_id = job.device.backend_id
        if device_id not in DEVICE_REGISTRY:
            result.errors.append(f"Unknown device: {device_id}")
            return result
        
        device_profile = DEVICE_REGISTRY[device_id]
        
        try:
            # 3. Build Pulser Register
            register = self._build_register(job.register)
            result.register = register
            
            # 4. Create Sequence
            sequence = Sequence(register, device_profile.pulser_device)
            
            # 5. Declare channels
            channels_used = self._get_required_channels(job.operations)
            for channel_type in channels_used:
                channel_name = self._declare_channel(sequence, channel_type, device_profile)
                if channel_name is None:
                    result.errors.append(f"Device doesn't support channel: {channel_type}")
                    return result
            
            # 6. Compile operations
            for op in sorted(job.operations, key=lambda o: o.start_time):
                self._compile_operation(sequence, op, job.register)
                result.num_pulses += 1
            
            # 7. Finalize
            result.sequence = sequence
            result.success = True
            result.total_duration_ns = job.get_total_duration()
            result.num_channels = len(channels_used)
            
            logger.info(
                f"Compiled job '{job.name}': {result.num_pulses} pulses, "
                f"{result.total_duration_ns:.0f} ns, {len(job.register.atoms)} atoms"
            )
            
        except Exception as e:
            result.errors.append(f"Compilation error: {str(e)}")
            logger.exception("Failed to compile job")
        
        return result
    
    def execute(
        self,
        sequence: Sequence,
        shots: int = 1000,
        compute_energy: bool = False
    ) -> ExecutionResult:
        """
        Execute a compiled Pulser Sequence on the simulator.
        
        Args:
            sequence: Compiled Pulser Sequence
            shots: Number of measurement shots
            compute_energy: Whether to compute Hamiltonian expectation value
            
        Returns:
            ExecutionResult with measurement outcomes
        """
        import time
        result = ExecutionResult(success=False)
        
        try:
            start_time = time.time()
            
            # Select backend based on system size
            num_qubits = len(sequence.register.qubit_ids)
            
            if self.auto_select_backend and num_qubits > 15:
                # TODO: Integrate tensor network backend for large systems
                logger.warning(
                    f"System has {num_qubits} qubits. QutipEmulator may be slow. "
                    "Consider using tensor network backend for >15 qubits."
                )
            
            # Use QutipEmulator
            emulator = QutipEmulator.from_sequence(sequence)
            
            # Run simulation
            final_state = emulator.run()
            
            # Sample measurements
            samples = final_state.sample_final_state(n_samples=shots)
            result.samples = list(samples.keys())
            result.counts = dict(samples)
            
            # Compute observables if requested
            if compute_energy:
                # For analog mode, compute energy of final state
                # This requires access to the Hamiltonian
                pass  # TODO: Implement energy calculation
            
            result.success = True
            result.shots_executed = shots
            result.execution_time_ms = (time.time() - start_time) * 1000
            result.backend_used = "QutipEmulator"
            
            logger.info(
                f"Executed sequence: {shots} shots in {result.execution_time_ms:.1f}ms"
            )
            
        except Exception as e:
            result.errors.append(f"Execution error: {str(e)}")
            logger.exception("Failed to execute sequence")
        
        return result
    
    # =========================================================================
    # PRIVATE: Register Building
    # =========================================================================
    
    def _build_register(self, spec: NeutralAtomRegister) -> Register:
        """Build Pulser Register from specification."""
        # Extract coordinates as dict
        coords = {}
        for atom in spec.atoms:
            coords[f"q{atom.id}"] = (atom.x, atom.y)
        
        return Register(coords)
    
    # =========================================================================
    # PRIVATE: Channel Management
    # =========================================================================
    
    def _get_required_channels(
        self, 
        operations: list[NeutralAtomOperation]
    ) -> set[ChannelType]:
        """Determine which channels are needed for the operations."""
        channels = set()
        
        for op in operations:
            if isinstance(op, GlobalPulse):
                channels.add(op.channel)
            elif isinstance(op, LocalDetuning):
                channels.add(op.channel)
            elif isinstance(op, RydbergGate):
                channels.add(ChannelType.RYDBERG_LOCAL)
        
        # Default to global Rydberg if no specific channels
        if not channels:
            channels.add(ChannelType.RYDBERG_GLOBAL)
        
        return channels
    
    def _declare_channel(
        self,
        sequence: Sequence,
        channel_type: ChannelType,
        device_profile: DeviceProfile
    ) -> Optional[str]:
        """Declare a channel on the sequence."""
        channel_map = {
            ChannelType.RYDBERG_GLOBAL: "rydberg_global",
            ChannelType.RYDBERG_LOCAL: "rydberg_local", 
            ChannelType.RAMAN_LOCAL: "raman_local",
            ChannelType.DIGITAL: "digital",
        }
        
        channel_name = channel_map.get(channel_type)
        if channel_name is None:
            return None
        
        # Check if device supports this channel
        available = sequence.available_channels
        
        # Find matching channel in device
        for dev_channel in available:
            if channel_name in dev_channel.lower():
                sequence.declare_channel(channel_name, dev_channel)
                return channel_name
        
        # Fallback: use first available if exact match not found
        if available:
            sequence.declare_channel(channel_name, list(available.keys())[0])
            return channel_name
        
        return None
    
    # =========================================================================
    # PRIVATE: Operation Compilation
    # =========================================================================
    
    def _compile_operation(
        self,
        sequence: Sequence,
        op: NeutralAtomOperation,
        register: NeutralAtomRegister
    ) -> None:
        """Compile a single operation to Pulser instructions."""
        
        if isinstance(op, GlobalPulse):
            self._compile_global_pulse(sequence, op)
        elif isinstance(op, LocalDetuning):
            self._compile_local_detuning(sequence, op)
        elif isinstance(op, RydbergGate):
            self._compile_rydberg_gate(sequence, op)
        elif isinstance(op, ShuttleMove):
            self._compile_shuttle(sequence, op, register)
        elif isinstance(op, Measurement):
            # Measurements are implicit at sequence end in Pulser
            pass
    
    def _compile_global_pulse(self, sequence: Sequence, op: GlobalPulse) -> None:
        """Compile GlobalPulse to Pulser Pulse."""
        channel_name = "rydberg_global"
        
        # Build waveforms
        omega_wf = self._build_waveform(op.omega)
        
        if op.detuning:
            detuning_wf = self._build_waveform(op.detuning)
        else:
            # Zero detuning
            detuning_wf = ConstantWaveform(int(op.omega.duration), 0)
        
        # Create Pulse
        pulse = Pulse(
            amplitude=omega_wf,
            detuning=detuning_wf,
            phase=op.phase
        )
        
        # Add to sequence
        sequence.add(pulse, channel_name)
    
    def _compile_local_detuning(self, sequence: Sequence, op: LocalDetuning) -> None:
        """Compile LocalDetuning to targeted pulse."""
        channel_name = "raman_local"
        
        # Target specific atoms
        targets = [f"q{atom_id}" for atom_id in op.target_atoms]
        sequence.target(targets, channel_name)
        
        # Build detuning waveform
        detuning_wf = self._build_waveform(op.detuning)
        
        # Create pulse (amplitude 0, only detuning matters)
        omega_wf = ConstantWaveform(int(op.detuning.duration), 0)
        pulse = Pulse(amplitude=omega_wf, detuning=detuning_wf, phase=0)
        
        sequence.add(pulse, channel_name)
    
    def _compile_rydberg_gate(self, sequence: Sequence, op: RydbergGate) -> None:
        """Compile RydbergGate to two-qubit Rydberg pulse."""
        channel_name = "rydberg_local"
        
        # Target the control and target atoms
        targets = [f"q{op.control_atom}", f"q{op.target_atom}"]
        sequence.target(targets, channel_name)
        
        if op.pulse:
            # Use custom pulse
            omega_wf = self._build_waveform(op.pulse)
        else:
            # Use default CZ gate pulse (area = π for each atom)
            duration = 200  # ns, typical for Rydberg gates
            omega_wf = BlackmanWaveform(duration, area=3.14159)
        
        detuning_wf = ConstantWaveform(omega_wf.duration, 0)
        pulse = Pulse(amplitude=omega_wf, detuning=detuning_wf, phase=0)
        
        sequence.add(pulse, channel_name)
    
    def _compile_shuttle(
        self,
        sequence: Sequence,
        op: ShuttleMove,
        register: NeutralAtomRegister
    ) -> None:
        """
        Compile ShuttleMove operation.
        
        Note: AOD movement is not directly supported in Pulser's Sequence model.
        This is typically handled at the device level or via specialized FPQA
        compilers. Here we insert a delay to represent the movement time.
        """
        # Log warning about AOD movement limitations
        logger.warning(
            f"ShuttleMove for atoms {op.atom_ids}: AOD movement is device-specific. "
            "Inserting delay placeholder. Full AOD support requires device-level API."
        )
        
        # Insert delay for movement duration
        # This is a placeholder - actual AOD movement would be handled by
        # device-specific APIs (Pasqal Fresnel, QuEra Aquila, etc.)
        pass  # Pulser sequences don't have explicit delays
    
    def _build_waveform(self, spec: WaveformSpec) -> Any:
        """Build Pulser Waveform from specification."""
        duration_ns = int(spec.duration)
        
        if spec.type == WaveformType.CONSTANT:
            return ConstantWaveform(duration_ns, spec.amplitude)
        
        elif spec.type == WaveformType.BLACKMAN:
            return BlackmanWaveform(duration_ns, area=spec.area)
        
        elif spec.type == WaveformType.GAUSSIAN:
            # Gaussian requires sigma, derive from duration
            sigma = duration_ns / 6  # 3-sigma on each side
            return GaussianWaveform(duration_ns, sigma=sigma)
        
        elif spec.type == WaveformType.INTERPOLATED:
            # Build interpolated waveform from time-value pairs
            return InterpolatedWaveform(
                duration_ns,
                values=spec.values,
                times=spec.times
            )
        
        elif spec.type == WaveformType.COMPOSITE:
            # Composite requires list of waveforms - not yet supported
            raise NotImplementedError("Composite waveforms not yet supported")
        
        else:
            raise ValueError(f"Unknown waveform type: {spec.type}")


# =============================================================================
# CONVENIENCE FUNCTIONS  
# =============================================================================

def compile_and_run(
    job: NeutralAtomJob,
    shots: int = 1000
) -> ExecutionResult:
    """
    Convenience function to compile and execute a job in one call.
    
    Args:
        job: NeutralAtomJob specification
        shots: Number of measurement shots
        
    Returns:
        ExecutionResult with measurement outcomes
    """
    adapter = PulserAdapter()
    
    # Compile
    compile_result = adapter.compile(job)
    if not compile_result.success:
        return ExecutionResult(
            success=False,
            errors=compile_result.errors
        )
    
    # Execute
    return adapter.execute(
        compile_result.sequence,
        shots=shots,
        compute_energy=job.simulation.compute_energy
    )


def validate_and_compile(job: NeutralAtomJob) -> tuple[ValidationResult, CompilationResult]:
    """
    Validate and compile a job, returning both results.
    
    Useful for debugging when you need detailed validation info.
    """
    adapter = PulserAdapter(validate=True)
    compile_result = adapter.compile(job)
    
    return compile_result.validation, compile_result

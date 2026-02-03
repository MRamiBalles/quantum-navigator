"""
Quantum Navigator v2.0 - Neutral Atom Driver Tests
===================================================

Unit tests for the neutral atom driver components:
- Schema validation
- Physics constraint validator
- Pulser adapter compilation
"""

import pytest
import json
from pathlib import Path

# Import driver components
from drivers.neutral_atom.schema import (
    NeutralAtomJob,
    NeutralAtomRegister,
    AtomPosition,
    TrapRole,
    LayoutType,
    DeviceConfig,
    SimulationConfig,
    GlobalPulse,
    LocalDetuning,
    ShuttleMove,
    RydbergGate,
    Measurement,
    WaveformSpec,
    WaveformType,
    create_example_job,
)
from drivers.neutral_atom.validator import (
    PulserValidator,
    TopologicalViolationError,
    CollisionError,
    VelocityExceededError,
    BlockadeDistanceError,
    validate_job,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def simple_register() -> NeutralAtomRegister:
    """Create a simple 4-atom register."""
    return NeutralAtomRegister(
        layout_type=LayoutType.ARBITRARY,
        min_atom_distance=4.0,
        blockade_radius=8.0,
        atoms=[
            AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.SLM),
            AtomPosition(id=1, x=6.0, y=0.0, role=TrapRole.SLM),
            AtomPosition(id=2, x=3.0, y=5.2, role=TrapRole.SLM),
            AtomPosition(id=3, x=9.0, y=5.2, role=TrapRole.AOD, aod_row=0, aod_col=0),
        ]
    )


@pytest.fixture
def simple_job(simple_register: NeutralAtomRegister) -> NeutralAtomJob:
    """Create a simple test job."""
    return NeutralAtomJob(
        name="Test Job",
        device=DeviceConfig(backend_id="simulator"),
        register=simple_register,
        operations=[
            GlobalPulse(
                start_time=0,
                omega=WaveformSpec(type=WaveformType.BLACKMAN, duration=1000, area=3.14159),
            ),
            Measurement(start_time=1100, atom_ids=[0, 1, 2, 3])
        ],
        simulation=SimulationConfig(backend="qutip", shots=100)
    )


# =============================================================================
# SCHEMA TESTS
# =============================================================================

class TestSchema:
    """Tests for the Pydantic schema models."""
    
    def test_create_example_job(self):
        """Example job should be valid."""
        job = create_example_job()
        assert job.name == "MIS Demo - 4 atoms"
        assert len(job.register.atoms) == 4
        assert len(job.operations) == 2
    
    def test_atom_position_validation(self):
        """Atom positions should validate correctly."""
        atom = AtomPosition(id=0, x=5.0, y=3.0, role=TrapRole.SLM)
        assert atom.x == 5.0
        assert atom.role == TrapRole.SLM
    
    def test_duplicate_atom_ids_rejected(self):
        """Register should reject duplicate atom IDs."""
        with pytest.raises(ValueError, match="Duplicate atom IDs"):
            NeutralAtomRegister(
                atoms=[
                    AtomPosition(id=0, x=0.0, y=0.0),
                    AtomPosition(id=0, x=5.0, y=0.0),  # Duplicate!
                ]
            )
    
    def test_waveform_constant_requires_amplitude(self):
        """Constant waveform must have amplitude."""
        with pytest.raises(ValueError, match="requires 'amplitude'"):
            WaveformSpec(type=WaveformType.CONSTANT, duration=100)
    
    def test_waveform_blackman_requires_area(self):
        """Blackman waveform must have area."""
        with pytest.raises(ValueError, match="requires 'area'"):
            WaveformSpec(type=WaveformType.BLACKMAN, duration=100)
    
    def test_interpolated_waveform_length_match(self):
        """Interpolated waveform times/values must match."""
        with pytest.raises(ValueError, match="same length"):
            WaveformSpec(
                type=WaveformType.INTERPOLATED,
                duration=100,
                times=[0, 50, 100],
                values=[0, 1]  # Wrong length!
            )
    
    def test_operation_references_valid_atoms(self, simple_register):
        """Operations must reference existing atoms."""
        with pytest.raises(ValueError, match="non-existent atom IDs"):
            NeutralAtomJob(
                device=DeviceConfig(backend_id="simulator"),
                register=simple_register,
                operations=[
                    Measurement(start_time=0, atom_ids=[0, 1, 999])  # 999 doesn't exist
                ]
            )
    
    def test_job_total_duration(self, simple_job):
        """Job should calculate total duration correctly."""
        duration = simple_job.get_total_duration()
        # GlobalPulse from 0-1000ns, Measurement at 1100ns
        assert duration >= 1100
    
    def test_json_serialization(self, simple_job):
        """Job should serialize to JSON correctly."""
        json_str = json.dumps(simple_job.model_dump())
        assert "simulator" in json_str
        assert "global_pulse" in json_str


# =============================================================================
# VALIDATOR TESTS
# =============================================================================

class TestValidator:
    """Tests for the physics constraint validator."""
    
    def test_valid_job_passes(self, simple_job):
        """Valid job should pass validation."""
        result = validate_job(simple_job)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_collision_detected(self):
        """Atoms too close should fail."""
        register = NeutralAtomRegister(
            min_atom_distance=4.0,
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0),
                AtomPosition(id=1, x=2.0, y=0.0),  # Too close! < 4µm
            ]
        )
        job = NeutralAtomJob(
            device=DeviceConfig(backend_id="simulator"),
            register=register,
            operations=[Measurement(start_time=0, atom_ids=[0, 1])]
        )
        
        result = validate_job(job)
        assert not result.is_valid
        assert any(isinstance(e, CollisionError) for e in result.errors)
    
    def test_blockade_distance_error(self):
        """Rydberg gate on distant atoms should fail."""
        register = NeutralAtomRegister(
            blockade_radius=8.0,
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0),
                AtomPosition(id=1, x=20.0, y=0.0),  # Too far for blockade!
            ]
        )
        job = NeutralAtomJob(
            device=DeviceConfig(backend_id="simulator"),
            register=register,
            operations=[
                RydbergGate(control_atom=0, target_atom=1, start_time=0)
            ]
        )
        
        result = validate_job(job)
        assert not result.is_valid
        assert any(isinstance(e, BlockadeDistanceError) for e in result.errors)
    
    def test_velocity_exceeded_error(self):
        """Fast AOD movement should fail."""
        register = NeutralAtomRegister(
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.AOD, aod_row=0, aod_col=0),
            ]
        )
        job = NeutralAtomJob(
            device=DeviceConfig(backend_id="simulator"),
            register=register,
            operations=[
                ShuttleMove(
                    atom_ids=[0],
                    start_time=0,
                    duration=100,  # 100ns to move 100µm = 1 µm/µs > 0.55 limit
                    target_positions=[(100.0, 0.0)]
                ),
                Measurement(start_time=200, atom_ids=[0])
            ]
        )
        
        result = validate_job(job)
        assert not result.is_valid
        assert any(isinstance(e, VelocityExceededError) for e in result.errors)
    
    def test_slm_atom_cannot_shuttle(self):
        """SLM (static) atoms cannot be shuttled."""
        register = NeutralAtomRegister(
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.SLM),  # Static!
            ]
        )
        job = NeutralAtomJob(
            device=DeviceConfig(backend_id="simulator"),
            register=register,
            operations=[
                ShuttleMove(
                    atom_ids=[0],
                    start_time=0,
                    duration=10000,
                    target_positions=[(5.0, 0.0)]
                ),
                Measurement(start_time=11000, atom_ids=[0])
            ]
        )
        
        result = validate_job(job)
        assert not result.is_valid
    
    def test_decoherence_cost_tracking(self):
        """Validator should track movement decoherence cost."""
        register = NeutralAtomRegister(
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.AOD, aod_row=0, aod_col=0),
            ]
        )
        job = NeutralAtomJob(
            device=DeviceConfig(backend_id="simulator"),
            register=register,
            operations=[
                ShuttleMove(
                    atom_ids=[0],
                    start_time=0,
                    duration=50000,  # Slow enough to be valid
                    target_positions=[(10.0, 0.0)]
                ),
                Measurement(start_time=60000, atom_ids=[0])
            ]
        )
        
        result = validate_job(job)
        # Even if valid, should have non-zero decoherence cost
        assert result.total_movement_distance == 10.0
        assert result.estimated_decoherence_cost > 0


# =============================================================================
# INTEGRATION TESTS (require Pulser)
# =============================================================================

class TestPulserAdapter:
    """Integration tests for PulserAdapter (requires pulser-core)."""
    
    @pytest.fixture
    def skip_if_no_pulser(self):
        """Skip test if Pulser is not installed."""
        try:
            import pulser
        except ImportError:
            pytest.skip("Pulser not installed")
    
    def test_compile_simple_job(self, simple_job, skip_if_no_pulser):
        """Simple job should compile successfully."""
        from drivers.neutral_atom.pulser_adapter import PulserAdapter
        
        adapter = PulserAdapter()
        result = adapter.compile(simple_job)
        
        assert result.success
        assert result.sequence is not None
        assert result.errors == []
    
    def test_compile_and_run(self, simple_job, skip_if_no_pulser):
        """Should be able to compile and execute on simulator."""
        from drivers.neutral_atom.pulser_adapter import compile_and_run
        
        result = compile_and_run(simple_job, shots=10)
        
        assert result.success
        assert result.counts is not None
        assert result.shots_executed == 10


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

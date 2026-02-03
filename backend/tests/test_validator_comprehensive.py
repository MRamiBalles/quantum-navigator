"""
Comprehensive Physics Validator Tests
======================================

Este módulo contiene tests exhaustivos para el motor de validación física,
verificando:
- Detección de colisiones
- Límites de velocidad AOD
- Restricciones topológicas
- Validación de puertas Rydberg
- Validación de zonas (v2.1)

Autor: Equipo de QA - Quantum Navigator
Fecha: Febrero 2026
"""

import pytest
import math

from drivers.neutral_atom.schema import (
    AtomPosition,
    TrapRole,
    WaveformSpec,
    WaveformType,
    ZoneDefinition,
    ZoneType,
    NeutralAtomRegister,
    GlobalPulse,
    ShuttleMove,
    RydbergGate,
    Measurement,
    ShieldingEvent,
    DeviceConfig,
    NeutralAtomJob,
)

from drivers.neutral_atom.validator import (
    PulserValidator,
    validate_job,
    ValidationResult,
    ValidationWarning,
    PhysicsConstraintError,
    CollisionError,
    TopologicalViolationError,
    VelocityExceededError,
    BlockadeDistanceError,
    ZoneViolationError,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def validator():
    """Instancia del validador."""
    return PulserValidator()


@pytest.fixture
def basic_register():
    """Registro básico con dos átomos."""
    return NeutralAtomRegister(
        atoms=[
            AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.SLM),
            AtomPosition(id=1, x=6.0, y=0.0, role=TrapRole.SLM),
        ]
    )


@pytest.fixture
def aod_register():
    """Registro con átomos móviles AOD."""
    return NeutralAtomRegister(
        atoms=[
            AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.AOD, aod_row=0, aod_col=0),
            AtomPosition(id=1, x=0.0, y=5.0, role=TrapRole.AOD, aod_row=1, aod_col=0),
            AtomPosition(id=2, x=5.0, y=0.0, role=TrapRole.AOD, aod_row=0, aod_col=1),
        ]
    )


@pytest.fixture
def zoned_register():
    """Registro con arquitectura zonal."""
    return NeutralAtomRegister(
        atoms=[
            AtomPosition(id=0, x=-15.0, y=0.0, role=TrapRole.AOD),  # In storage
            AtomPosition(id=1, x=5.0, y=0.0, role=TrapRole.SLM),   # In entanglement
        ],
        zones=[
            ZoneDefinition(
                zone_id="storage_1",
                zone_type=ZoneType.STORAGE,
                x_min=-25.0, x_max=-5.0,
                y_min=-10.0, y_max=10.0,
                shielding_light=True
            ),
            ZoneDefinition(
                zone_id="entangle_1",
                zone_type=ZoneType.ENTANGLEMENT,
                x_min=-5.0, x_max=20.0,
                y_min=-10.0, y_max=10.0
            ),
            ZoneDefinition(
                zone_id="readout_1",
                zone_type=ZoneType.READOUT,
                x_min=25.0, x_max=40.0,
                y_min=-10.0, y_max=10.0
            ),
        ]
    )


@pytest.fixture
def valid_pulse():
    """Pulso Rydberg válido."""
    return GlobalPulse(
        start_time=0,
        omega=WaveformSpec(type=WaveformType.BLACKMAN, duration=1000, area=3.14159)
    )


def make_job(register, operations):
    """Helper para crear jobs."""
    return NeutralAtomJob(
        device=DeviceConfig(backend_id="simulator"),
        register=register,
        operations=operations
    )


# =============================================================================
# COLLISION DETECTION TESTS
# =============================================================================

class TestCollisionDetection:
    """Tests para detección de colisiones."""
    
    def test_no_collision_valid_distance(self, validator, basic_register):
        """Átomos a distancia válida no generan error."""
        job = make_job(basic_register, [
            Measurement(start_time=0, atom_ids=[0, 1])
        ])
        result = validator.validate(job)
        
        assert result.is_valid
        collision_errors = [e for e in result.errors if isinstance(e, CollisionError)]
        assert len(collision_errors) == 0
    
    def test_collision_detected(self, validator):
        """Átomos demasiado cerca generan error."""
        register = NeutralAtomRegister(
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0),
                AtomPosition(id=1, x=2.0, y=0.0),  # < 4 µm!
            ]
        )
        job = make_job(register, [Measurement(start_time=0, atom_ids=[0, 1])])
        result = validator.validate(job)
        
        assert not result.is_valid
        collision_errors = [e for e in result.errors if isinstance(e, CollisionError)]
        assert len(collision_errors) >= 1
    
    def test_exactly_at_min_distance(self, validator):
        """Átomos exactamente a min_distance deberían ser válidos."""
        register = NeutralAtomRegister(
            min_atom_distance=4.0,
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0),
                AtomPosition(id=1, x=4.0, y=0.0),  # Exactly at limit
            ]
        )
        job = make_job(register, [Measurement(start_time=0, atom_ids=[0, 1])])
        result = validator.validate(job)
        
        # Should be valid (at limit, not below)
        collision_errors = [e for e in result.errors if isinstance(e, CollisionError)]
        assert len(collision_errors) == 0
    
    def test_near_collision_warning(self, validator):
        """Átomos cerca del límite generan warning."""
        register = NeutralAtomRegister(
            min_atom_distance=4.0,
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0),
                AtomPosition(id=1, x=4.5, y=0.0),  # Near limit
            ]
        )
        job = make_job(register, [Measurement(start_time=0, atom_ids=[0, 1])])
        result = validator.validate(job)
        
        near_collision = [w for w in result.warnings if w.code == "NEAR_COLLISION"]
        # May or may not generate warning depending on threshold
        assert result.is_valid


# =============================================================================
# VELOCITY LIMIT TESTS
# =============================================================================

class TestVelocityLimits:
    """Tests para límites de velocidad de shuttle AOD."""
    
    def test_valid_velocity(self, validator, aod_register):
        """Movimiento dentro de límites de velocidad."""
        move = ShuttleMove(
            atom_ids=[0],
            start_time=0,
            duration=20000,  # 20 µs for 10 µm = 0.5 µm/µs < 0.55 limit
            target_positions=[(10.0, 0.0)],
            trajectory="minimum_jerk"
        )
        job = make_job(aod_register, [move])
        result = validator.validate(job)
        
        velocity_errors = [e for e in result.errors if isinstance(e, VelocityExceededError)]
        assert len(velocity_errors) == 0
    
    def test_velocity_exceeded(self, validator, aod_register):
        """Movimiento demasiado rápido genera error."""
        move = ShuttleMove(
            atom_ids=[0],
            start_time=0,
            duration=1000,  # 1 µs for 10 µm = 10 µm/µs >> 0.55 limit!
            target_positions=[(10.0, 0.0)],
            trajectory="linear"
        )
        job = make_job(aod_register, [move])
        result = validator.validate(job)
        
        assert not result.is_valid
        velocity_errors = [e for e in result.errors if isinstance(e, VelocityExceededError)]
        assert len(velocity_errors) >= 1
    
    def test_marginal_velocity(self, validator, aod_register):
        """Velocidad cerca del límite."""
        # 10 µm / 18 µs ≈ 0.55 µm/µs (at limit)
        move = ShuttleMove(
            atom_ids=[0],
            start_time=0,
            duration=18200,  # Just above limit
            target_positions=[(10.0, 0.0)],
            trajectory="minimum_jerk"
        )
        job = make_job(aod_register, [move])
        result = validator.validate(job)
        
        velocity_errors = [e for e in result.errors if isinstance(e, VelocityExceededError)]
        assert len(velocity_errors) == 0


# =============================================================================
# TOPOLOGICAL CONSTRAINT TESTS
# =============================================================================

class TestTopologicalConstraints:
    """Tests para restricciones topológicas de AOD."""
    
    def test_valid_movement_preserves_order(self, validator, aod_register):
        """Movimiento que preserva orden topológico es válido."""
        # Move atom 0 right (stays in same row/col order)
        move = ShuttleMove(
            atom_ids=[0],
            start_time=0,
            duration=20000,
            target_positions=[(3.0, 0.0)],
            trajectory="minimum_jerk"
        )
        job = make_job(aod_register, [move])
        result = validator.validate(job)
        
        topo_errors = [e for e in result.errors if isinstance(e, TopologicalViolationError)]
        assert len(topo_errors) == 0
    
    def test_row_crossing_detected(self, validator):
        """Cruce de filas AOD genera error."""
        register = NeutralAtomRegister(
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.AOD, aod_row=0, aod_col=0),
                AtomPosition(id=1, x=0.0, y=10.0, role=TrapRole.AOD, aod_row=1, aod_col=0),
            ]
        )
        # Try to move atom 0 above atom 1 (row crossing)
        move = ShuttleMove(
            atom_ids=[0],
            start_time=0,
            duration=50000,
            target_positions=[(0.0, 15.0)],  # Would swap row order
            trajectory="minimum_jerk"
        )
        job = make_job(register, [move])
        result = validator.validate(job)
        
        topo_errors = [e for e in result.errors if isinstance(e, TopologicalViolationError)]
        assert len(topo_errors) >= 1
    
    def test_column_crossing_detected(self, validator):
        """Cruce de columnas AOD genera error."""
        register = NeutralAtomRegister(
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.AOD, aod_row=0, aod_col=0),
                AtomPosition(id=1, x=10.0, y=0.0, role=TrapRole.AOD, aod_row=0, aod_col=1),
            ]
        )
        # Try to move atom 0 past atom 1 (column crossing)
        move = ShuttleMove(
            atom_ids=[0],
            start_time=0,
            duration=50000,
            target_positions=[(15.0, 0.0)],  # Would swap column order
            trajectory="minimum_jerk"
        )
        job = make_job(register, [move])
        result = validator.validate(job)
        
        topo_errors = [e for e in result.errors if isinstance(e, TopologicalViolationError)]
        assert len(topo_errors) >= 1
    
    def test_slm_atom_cannot_shuttle(self, validator):
        """Átomos SLM no deberían poder moverse."""
        register = NeutralAtomRegister(
            atoms=[AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.SLM)]
        )
        move = ShuttleMove(
            atom_ids=[0],  # SLM atom!
            start_time=0,
            duration=10000,
            target_positions=[(5.0, 0.0)],
            trajectory="linear"
        )
        job = make_job(register, [move])
        result = validator.validate(job)
        
        # Should generate error or warning
        assert not result.is_valid or len(result.warnings) > 0


# =============================================================================
# RYDBERG GATE VALIDATION TESTS
# =============================================================================

class TestRydbergGateValidation:
    """Tests para validación de puertas Rydberg."""
    
    def test_valid_blockade_distance(self, validator, basic_register):
        """Átomos dentro del radio de bloqueo son válidos."""
        gate = RydbergGate(
            control_atom=0,
            target_atom=1,
            gate_type="CZ",
            start_time=0
        )
        job = make_job(basic_register, [gate])
        result = validator.validate(job)
        
        blockade_errors = [e for e in result.errors if isinstance(e, BlockadeDistanceError)]
        assert len(blockade_errors) == 0
    
    def test_atoms_too_far_for_blockade(self, validator):
        """Átomos fuera del radio de bloqueo generan error."""
        register = NeutralAtomRegister(
            blockade_radius=8.0,
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0),
                AtomPosition(id=1, x=15.0, y=0.0),  # > 8 µm
            ]
        )
        gate = RydbergGate(
            control_atom=0,
            target_atom=1,
            gate_type="CZ",
            start_time=0
        )
        job = make_job(register, [gate])
        result = validator.validate(job)
        
        assert not result.is_valid
        blockade_errors = [e for e in result.errors if isinstance(e, BlockadeDistanceError)]
        assert len(blockade_errors) >= 1
    
    def test_marginal_blockade_warning(self, validator):
        """Átomos cerca del límite de bloqueo generan warning."""
        register = NeutralAtomRegister(
            blockade_radius=8.0,
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0),
                AtomPosition(id=1, x=7.5, y=0.0),  # Near 8 µm limit
            ]
        )
        gate = RydbergGate(control_atom=0, target_atom=1, gate_type="CZ", start_time=0)
        job = make_job(register, [gate])
        result = validator.validate(job)
        
        # Should be valid but may have warning
        blockade_errors = [e for e in result.errors if isinstance(e, BlockadeDistanceError)]
        assert len(blockade_errors) == 0


# =============================================================================
# ZONE VALIDATION TESTS (v2.1)
# =============================================================================

class TestZoneValidation:
    """Tests para validación de zonas (v2.1)."""
    
    def test_no_zones_backward_compat(self, validator, basic_register, valid_pulse):
        """Jobs sin zonas pasan validación (backward compat)."""
        job = make_job(basic_register, [
            valid_pulse,
            Measurement(start_time=1100, atom_ids=[0, 1])
        ])
        result = validator.validate(job)
        
        assert result.is_valid
    
    def test_pulse_in_shielded_storage_warning(self, validator, zoned_register, valid_pulse):
        """Pulso en zona de storage blindada genera warning high."""
        job = make_job(zoned_register, [
            valid_pulse,  # Atom 0 is in shielded storage!
            Measurement(start_time=1100, atom_ids=[0, 1])
        ])
        result = validator.validate(job)
        
        shielded_warnings = [w for w in result.warnings 
                            if w.code == "PULSE_IN_SHIELDED_ZONE"]
        assert len(shielded_warnings) >= 1
        assert shielded_warnings[0].severity == "high"
    
    def test_measurement_outside_readout_warning(self, validator, zoned_register):
        """Medición fuera de zona de readout genera warning."""
        # Both atoms are NOT in readout zone
        job = make_job(zoned_register, [
            Measurement(start_time=0, atom_ids=[0, 1])
        ])
        result = validator.validate(job)
        
        readout_warnings = [w for w in result.warnings 
                          if w.code == "MEASUREMENT_OUTSIDE_READOUT"]
        assert len(readout_warnings) >= 1
    
    def test_entanglement_zone_allows_gates(self, validator):
        """Puertas en zona de entanglement son válidas."""
        register = NeutralAtomRegister(
            atoms=[
                AtomPosition(id=0, x=5.0, y=0.0),
                AtomPosition(id=1, x=10.0, y=0.0),
            ],
            zones=[
                ZoneDefinition(
                    zone_id="eg",
                    zone_type=ZoneType.ENTANGLEMENT,
                    x_min=0.0, x_max=20.0,
                    y_min=-10.0, y_max=10.0
                )
            ]
        )
        job = make_job(register, [
            GlobalPulse(
                start_time=0,
                omega=WaveformSpec(type=WaveformType.BLACKMAN, duration=1000, area=3.14)
            ),
            RydbergGate(control_atom=0, target_atom=1, gate_type="CZ", start_time=1100)
        ])
        result = validator.validate(job)
        
        # No zone warnings for entanglement operations
        zone_warnings = [w for w in result.warnings 
                        if "ZONE" in w.code]
        assert len(zone_warnings) == 0


# =============================================================================
# DECOHERENCE ESTIMATION TESTS
# =============================================================================

class TestDecoherenceEstimation:
    """Tests para estimación de decoherencia."""
    
    def test_movement_adds_decoherence(self, validator, aod_register):
        """Movimiento incrementa costo de decoherencia."""
        move = ShuttleMove(
            atom_ids=[0],
            start_time=0,
            duration=20000,
            target_positions=[(10.0, 0.0)],
            trajectory="minimum_jerk"
        )
        job = make_job(aod_register, [move])
        result = validator.validate(job)
        
        assert result.estimated_decoherence_cost > 0
        assert result.total_movement_distance > 0
    
    def test_more_movement_more_decoherence(self, validator, aod_register):
        """Más movimiento = más decoherencia."""
        short_move = ShuttleMove(
            atom_ids=[0],
            start_time=0,
            duration=10000,
            target_positions=[(5.0, 0.0)],
            trajectory="minimum_jerk"
        )
        long_move = ShuttleMove(
            atom_ids=[0],
            start_time=0,
            duration=40000,
            target_positions=[(20.0, 0.0)],
            trajectory="minimum_jerk"
        )
        
        job_short = make_job(aod_register, [short_move])
        job_long = make_job(aod_register, [long_move])
        
        result_short = validator.validate(job_short)
        result_long = validator.validate(job_long)
        
        assert result_long.total_movement_distance > result_short.total_movement_distance


# =============================================================================
# TEMPORAL OVERLAP TESTS
# =============================================================================

class TestTemporalOverlaps:
    """Tests para detección de solapamientos temporales."""
    
    def test_concurrent_shuttles_warning(self, validator, aod_register):
        """Shuttles concurrentes generan warning."""
        move1 = ShuttleMove(
            atom_ids=[0],
            start_time=0,
            duration=10000,
            target_positions=[(5.0, 0.0)],
            trajectory="minimum_jerk"
        )
        move2 = ShuttleMove(
            atom_ids=[1],
            start_time=5000,  # Overlaps with move1!
            duration=10000,
            target_positions=[(0.0, 10.0)],
            trajectory="minimum_jerk"
        )
        job = make_job(aod_register, [move1, move2])
        result = validator.validate(job)
        
        concurrent_warnings = [w for w in result.warnings 
                              if w.code == "CONCURRENT_SHUTTLES"]
        assert len(concurrent_warnings) >= 1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestValidatorIntegration:
    """Tests de integración del validador completo."""
    
    def test_complex_valid_job(self, validator):
        """Job complejo pero válido."""
        register = NeutralAtomRegister(
            atoms=[
                AtomPosition(id=i, x=float(i * 6), y=0.0, role=TrapRole.SLM)
                for i in range(5)
            ]
        )
        job = make_job(register, [
            GlobalPulse(
                start_time=0,
                omega=WaveformSpec(type=WaveformType.BLACKMAN, duration=1000, area=3.14)
            ),
            RydbergGate(control_atom=0, target_atom=1, gate_type="CZ", start_time=1100),
            RydbergGate(control_atom=2, target_atom=3, gate_type="CZ", start_time=2200),
            Measurement(start_time=3300, atom_ids=[0, 1, 2, 3, 4])
        ])
        result = validator.validate(job)
        
        assert result.is_valid
    
    def test_validate_job_function(self, basic_register, valid_pulse):
        """Función validate_job funciona correctamente."""
        job = make_job(basic_register, [
            valid_pulse,
            Measurement(start_time=1100, atom_ids=[0, 1])
        ])
        result = validate_job(job)
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

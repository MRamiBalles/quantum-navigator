"""
Comprehensive Schema Validation Tests
=====================================

Este módulo contiene tests exhaustivos para el esquema de datos
del driver de átomos neutros, verificando:
- Validaciones de Pydantic
- Restricciones de límites
- Integridad referencial
- Casos edge y errores esperados

Autor: Equipo de QA - Quantum Navigator
Fecha: Febrero 2026
"""

import pytest
from pydantic import ValidationError
import math

from drivers.neutral_atom.schema import (
    # Enums
    TrapRole,
    WaveformType,
    LayoutType,
    ZoneType,
    
    # Models
    AtomPosition,
    WaveformSpec,
    ZoneDefinition,
    NeutralAtomRegister,
    GlobalPulse,
    LocalDetuning,
    ShuttleMove,
    RydbergGate,
    Measurement,
    ShieldingEvent,
    DeviceConfig,
    SimulationConfig,
    NeutralAtomJob,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def valid_atom():
    """Átomo válido básico."""
    return AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.SLM)


@pytest.fixture
def valid_waveform():
    """Waveform válido básico."""
    return WaveformSpec(
        type=WaveformType.BLACKMAN,
        duration=1000,
        area=3.14159
    )


@pytest.fixture
def valid_zone():
    """Zona válida básica."""
    return ZoneDefinition(
        zone_id="test_zone",
        zone_type=ZoneType.ENTANGLEMENT,
        x_min=-10.0, x_max=10.0,
        y_min=-10.0, y_max=10.0
    )


@pytest.fixture
def minimal_register():
    """Registro con un solo átomo."""
    return NeutralAtomRegister(
        atoms=[AtomPosition(id=0, x=0.0, y=0.0)]
    )


@pytest.fixture
def two_atom_register():
    """Registro con dos átomos a distancia válida."""
    return NeutralAtomRegister(
        atoms=[
            AtomPosition(id=0, x=0.0, y=0.0),
            AtomPosition(id=1, x=6.0, y=0.0),  # > min_distance
        ]
    )


# =============================================================================
# ATOMPOSITION TESTS
# =============================================================================

class TestAtomPosition:
    """Tests para el modelo AtomPosition."""
    
    def test_valid_atom(self):
        """Átomo con todos los campos válidos."""
        atom = AtomPosition(id=0, x=10.5, y=-5.2, role=TrapRole.AOD)
        assert atom.id == 0
        assert atom.x == 10.5
        assert atom.y == -5.2
        assert atom.role == TrapRole.AOD
    
    def test_default_role_is_slm(self):
        """El rol por defecto debe ser SLM."""
        atom = AtomPosition(id=0, x=0.0, y=0.0)
        assert atom.role == TrapRole.SLM
    
    def test_negative_id_fails(self):
        """IDs negativos deben fallar."""
        with pytest.raises(ValidationError) as exc_info:
            AtomPosition(id=-1, x=0.0, y=0.0)
        assert "ge" in str(exc_info.value) or "greater" in str(exc_info.value).lower()
    
    def test_aod_with_grid_coords(self):
        """Átomos AOD pueden tener coordenadas de grilla."""
        atom = AtomPosition(
            id=5, x=10.0, y=20.0, 
            role=TrapRole.AOD,
            aod_row=2, aod_col=3
        )
        assert atom.aod_row == 2
        assert atom.aod_col == 3
    
    def test_storage_role(self):
        """Rol STORAGE disponible para v2.1."""
        atom = AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.STORAGE)
        assert atom.role == TrapRole.STORAGE
    
    def test_float_coordinates(self):
        """Coordenadas pueden ser floats arbitrarios."""
        atom = AtomPosition(id=0, x=1.23456789, y=-9.87654321)
        assert abs(atom.x - 1.23456789) < 1e-9
        assert abs(atom.y - (-9.87654321)) < 1e-9


# =============================================================================
# WAVEFORMSPEC TESTS
# =============================================================================

class TestWaveformSpec:
    """Tests para el modelo WaveformSpec."""
    
    def test_constant_waveform(self):
        """Waveform constante con valor fijo."""
        wf = WaveformSpec(
            type=WaveformType.CONSTANT,
            duration=500,
            value=2.5
        )
        assert wf.type == WaveformType.CONSTANT
        assert wf.value == 2.5
    
    def test_blackman_waveform_with_area(self):
        """Waveform Blackman con área especificada."""
        wf = WaveformSpec(
            type=WaveformType.BLACKMAN,
            duration=1000,
            area=3.14159
        )
        assert wf.area == pytest.approx(3.14159, rel=1e-5)
    
    def test_gaussian_waveform(self):
        """Waveform Gaussiano."""
        wf = WaveformSpec(
            type=WaveformType.GAUSSIAN,
            duration=800,
            area=1.5708  # π/2
        )
        assert wf.type == WaveformType.GAUSSIAN
    
    def test_zero_duration_fails(self):
        """Duración cero debe fallar."""
        with pytest.raises(ValidationError):
            WaveformSpec(type=WaveformType.CONSTANT, duration=0, value=1.0)
    
    def test_negative_duration_fails(self):
        """Duración negativa debe fallar."""
        with pytest.raises(ValidationError):
            WaveformSpec(type=WaveformType.CONSTANT, duration=-100, value=1.0)
    
    def test_interpolated_waveform_needs_samples(self):
        """Waveform interpolado debería tener samples (si se implementa)."""
        wf = WaveformSpec(
            type=WaveformType.INTERPOLATED,
            duration=1000,
            samples=[0.0, 0.5, 1.0, 0.5, 0.0]
        )
        assert wf.samples is not None
        assert len(wf.samples) == 5


# =============================================================================
# ZONEDEFINITION TESTS
# =============================================================================

class TestZoneDefinition:
    """Tests para el modelo ZoneDefinition (v2.1)."""
    
    def test_valid_zone(self):
        """Zona con todos los campos válidos."""
        zone = ZoneDefinition(
            zone_id="entangle_1",
            zone_type=ZoneType.ENTANGLEMENT,
            x_min=-5.0, x_max=15.0,
            y_min=-10.0, y_max=10.0
        )
        assert zone.zone_id == "entangle_1"
        assert zone.zone_type == ZoneType.ENTANGLEMENT
    
    def test_shielded_storage_zone(self):
        """Zona de storage con shielding."""
        zone = ZoneDefinition(
            zone_id="storage_main",
            zone_type=ZoneType.STORAGE,
            x_min=-40.0, x_max=-10.0,
            y_min=-20.0, y_max=20.0,
            shielding_light=True
        )
        assert zone.shielding_light is True
    
    def test_preparation_zone(self):
        """Zona de preparación (v2.1)."""
        zone = ZoneDefinition(
            zone_id="prep_zone",
            zone_type=ZoneType.PREPARATION,
            x_min=-50.0, x_max=-40.0,
            y_min=-25.0, y_max=25.0
        )
        assert zone.zone_type == ZoneType.PREPARATION
    
    def test_reservoir_zone(self):
        """Zona de reservorio (v2.1)."""
        zone = ZoneDefinition(
            zone_id="MOT_reservoir",
            zone_type=ZoneType.RESERVOIR,
            x_min=-60.0, x_max=-50.0,
            y_min=-30.0, y_max=30.0
        )
        assert zone.zone_type == ZoneType.RESERVOIR
    
    def test_inverted_bounds_fails(self):
        """x_min > x_max debe fallar."""
        with pytest.raises(ValidationError):
            ZoneDefinition(
                zone_id="bad_zone",
                zone_type=ZoneType.BUFFER,
                x_min=10.0, x_max=5.0,  # Inverted!
                y_min=0.0, y_max=10.0
            )
    
    def test_contains_point(self, valid_zone):
        """Método contains_point debe funcionar."""
        assert valid_zone.contains_point(0.0, 0.0) is True
        assert valid_zone.contains_point(9.9, 9.9) is True
        assert valid_zone.contains_point(15.0, 0.0) is False
        assert valid_zone.contains_point(0.0, -15.0) is False
    
    def test_contains_atom(self, valid_zone, valid_atom):
        """Método contains_atom debe funcionar."""
        assert valid_zone.contains_atom(valid_atom) is True
        
        outside_atom = AtomPosition(id=1, x=50.0, y=50.0)
        assert valid_zone.contains_atom(outside_atom) is False


# =============================================================================
# NEUTRALATOMREGISTER TESTS
# =============================================================================

class TestNeutralAtomRegister:
    """Tests para el modelo NeutralAtomRegister."""
    
    def test_minimal_register(self, minimal_register):
        """Registro con un solo átomo es válido."""
        assert len(minimal_register.atoms) == 1
    
    def test_default_parameters(self, minimal_register):
        """Parámetros por defecto correctos."""
        assert minimal_register.layout_type == LayoutType.ARBITRARY
        assert minimal_register.min_atom_distance == 4.0
        assert minimal_register.blockade_radius == 8.0
    
    def test_custom_parameters(self):
        """Parámetros personalizados."""
        reg = NeutralAtomRegister(
            layout_type=LayoutType.TRIANGULAR,
            min_atom_distance=5.0,
            blockade_radius=10.0,
            atoms=[AtomPosition(id=0, x=0.0, y=0.0)]
        )
        assert reg.layout_type == LayoutType.TRIANGULAR
        assert reg.min_atom_distance == 5.0
        assert reg.blockade_radius == 10.0
    
    def test_duplicate_ids_fail(self):
        """IDs duplicados deben fallar."""
        with pytest.raises(ValidationError) as exc_info:
            NeutralAtomRegister(
                atoms=[
                    AtomPosition(id=0, x=0.0, y=0.0),
                    AtomPosition(id=0, x=10.0, y=0.0),  # Duplicate!
                ]
            )
        assert "duplicate" in str(exc_info.value).lower()
    
    def test_empty_atoms_fail(self):
        """Lista vacía de átomos debe fallar."""
        with pytest.raises(ValidationError):
            NeutralAtomRegister(atoms=[])
    
    def test_max_atoms(self):
        """Máximo 256 átomos."""
        atoms = [AtomPosition(id=i, x=float(i % 16 * 5), y=float(i // 16 * 5)) 
                 for i in range(256)]
        reg = NeutralAtomRegister(atoms=atoms)
        assert len(reg.atoms) == 256
    
    def test_too_many_atoms_fail(self):
        """Más de 256 átomos debe fallar."""
        atoms = [AtomPosition(id=i, x=float(i % 16 * 5), y=float(i // 16 * 5)) 
                 for i in range(257)]
        with pytest.raises(ValidationError):
            NeutralAtomRegister(atoms=atoms)
    
    def test_get_atom_by_id(self, two_atom_register):
        """Buscar átomo por ID."""
        atom = two_atom_register.get_atom_by_id(1)
        assert atom is not None
        assert atom.x == 6.0
        
        none_atom = two_atom_register.get_atom_by_id(999)
        assert none_atom is None
    
    def test_get_aod_atoms(self):
        """Filtrar átomos AOD."""
        reg = NeutralAtomRegister(atoms=[
            AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.SLM),
            AtomPosition(id=1, x=5.0, y=0.0, role=TrapRole.AOD),
            AtomPosition(id=2, x=10.0, y=0.0, role=TrapRole.AOD),
        ])
        aod_atoms = reg.get_aod_atoms()
        assert len(aod_atoms) == 2
        assert all(a.role == TrapRole.AOD for a in aod_atoms)
    
    def test_register_with_zones(self, valid_zone):
        """Registro con zonas definidas."""
        reg = NeutralAtomRegister(
            atoms=[AtomPosition(id=0, x=0.0, y=0.0)],
            zones=[valid_zone]
        )
        assert reg.zones is not None
        assert len(reg.zones) == 1
    
    def test_get_zone_at_position(self, valid_zone):
        """Obtener zona para una posición."""
        reg = NeutralAtomRegister(
            atoms=[AtomPosition(id=0, x=0.0, y=0.0)],
            zones=[valid_zone]
        )
        zone = reg.get_zone_at_position(0.0, 0.0)
        assert zone is not None
        assert zone.zone_id == "test_zone"
        
        no_zone = reg.get_zone_at_position(100.0, 100.0)
        assert no_zone is None
    
    def test_get_zones_by_type(self):
        """Filtrar zonas por tipo."""
        reg = NeutralAtomRegister(
            atoms=[AtomPosition(id=0, x=0.0, y=0.0)],
            zones=[
                ZoneDefinition(
                    zone_id="s1", zone_type=ZoneType.STORAGE,
                    x_min=-20, x_max=-5, y_min=-10, y_max=10
                ),
                ZoneDefinition(
                    zone_id="e1", zone_type=ZoneType.ENTANGLEMENT,
                    x_min=-5, x_max=15, y_min=-10, y_max=10
                ),
                ZoneDefinition(
                    zone_id="s2", zone_type=ZoneType.STORAGE,
                    x_min=15, x_max=30, y_min=-10, y_max=10
                ),
            ]
        )
        storage_zones = reg.get_zones_by_type(ZoneType.STORAGE)
        assert len(storage_zones) == 2
        
        entangle_zones = reg.get_zones_by_type(ZoneType.ENTANGLEMENT)
        assert len(entangle_zones) == 1


# =============================================================================
# OPERATION TESTS
# =============================================================================

class TestOperations:
    """Tests para modelos de operaciones."""
    
    def test_global_pulse(self, valid_waveform):
        """GlobalPulse válido."""
        pulse = GlobalPulse(
            start_time=0,
            omega=valid_waveform
        )
        assert pulse.op_type == "global_pulse"
        assert pulse.start_time == 0
    
    def test_shuttle_move(self):
        """ShuttleMove válido."""
        move = ShuttleMove(
            atom_ids=[0, 1],
            start_time=1000,
            duration=2000,
            target_positions=[(10.0, 0.0), (15.0, 0.0)],
            trajectory="minimum_jerk"
        )
        assert move.op_type == "shuttle"
        assert len(move.atom_ids) == len(move.target_positions)
    
    def test_shuttle_mismatched_positions_fail(self):
        """ShuttleMove con posiciones desalineadas debe fallar."""
        with pytest.raises(ValidationError):
            ShuttleMove(
                atom_ids=[0, 1, 2],
                start_time=0,
                duration=1000,
                target_positions=[(10.0, 0.0)]  # Solo 1 posición para 3 átomos
            )
    
    def test_rydberg_gate(self):
        """RydbergGate válido."""
        gate = RydbergGate(
            control_atom=0,
            target_atom=1,
            gate_type="CZ",
            start_time=2000
        )
        assert gate.op_type == "rydberg_gate"
        assert gate.gate_type == "CZ"
    
    def test_measurement(self):
        """Measurement válido."""
        meas = Measurement(
            atom_ids=[0, 1, 2],
            start_time=5000,
            basis="computational"
        )
        assert meas.op_type == "measure"
        assert meas.basis == "computational"
    
    def test_shielding_event(self):
        """ShieldingEvent válido (v2.1)."""
        shield = ShieldingEvent(
            start_time=0,
            duration=10000,
            zone_ids=["storage_1"],
            mode="activate"
        )
        assert shield.op_type == "shielding"
        assert shield.mode == "activate"
    
    def test_shielding_deactivate(self):
        """ShieldingEvent desactivación."""
        shield = ShieldingEvent(
            start_time=50000,
            duration=1000,
            zone_ids=["storage_1"],
            mode="deactivate"
        )
        assert shield.mode == "deactivate"


# =============================================================================
# FULL JOB TESTS
# =============================================================================

class TestNeutralAtomJob:
    """Tests para NeutralAtomJob completo."""
    
    def test_minimal_job(self, two_atom_register, valid_waveform):
        """Job mínimo válido."""
        job = NeutralAtomJob(
            device=DeviceConfig(backend_id="simulator"),
            register=two_atom_register,
            operations=[
                GlobalPulse(start_time=0, omega=valid_waveform),
                Measurement(start_time=1100, atom_ids=[0, 1])
            ]
        )
        assert job.device.backend_id == "simulator"
        assert len(job.operations) == 2
    
    def test_job_with_all_operation_types(self, two_atom_register, valid_waveform):
        """Job con todos los tipos de operación."""
        job = NeutralAtomJob(
            device=DeviceConfig(backend_id="simulator", shots=100),
            register=two_atom_register,
            operations=[
                GlobalPulse(start_time=0, omega=valid_waveform),
                LocalDetuning(
                    atom_id=0, start_time=1000,
                    detuning=WaveformSpec(type=WaveformType.CONSTANT, duration=500, value=1.0)
                ),
                RydbergGate(control_atom=0, target_atom=1, gate_type="CZ", start_time=1500),
                Measurement(start_time=2500, atom_ids=[0, 1])
            ]
        )
        assert len(job.operations) == 4
    
    def test_job_with_zones(self, valid_waveform, valid_zone):
        """Job con arquitectura zonal."""
        reg = NeutralAtomRegister(
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0),
                AtomPosition(id=1, x=6.0, y=0.0),
            ],
            zones=[valid_zone]
        )
        job = NeutralAtomJob(
            device=DeviceConfig(backend_id="simulator"),
            register=reg,
            operations=[
                ShieldingEvent(start_time=0, duration=50000, zone_ids=["test_zone"], mode="activate"),
                GlobalPulse(start_time=0, omega=valid_waveform),
                Measurement(start_time=1100, atom_ids=[0, 1])
            ]
        )
        assert job.register.zones is not None
        assert any(isinstance(op, ShieldingEvent) for op in job.operations)


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests para casos límite y edge cases."""
    
    def test_atom_at_origin(self):
        """Átomo exactamente en el origen."""
        atom = AtomPosition(id=0, x=0.0, y=0.0)
        assert atom.x == 0.0 and atom.y == 0.0
    
    def test_very_small_zone(self):
        """Zona muy pequeña pero válida."""
        zone = ZoneDefinition(
            zone_id="tiny",
            zone_type=ZoneType.BUFFER,
            x_min=0.0, x_max=0.001,
            y_min=0.0, y_max=0.001
        )
        assert zone.x_max > zone.x_min
    
    def test_zero_area_zone_fails(self):
        """Zona con área cero debe fallar."""
        with pytest.raises(ValidationError):
            ZoneDefinition(
                zone_id="zero",
                zone_type=ZoneType.BUFFER,
                x_min=5.0, x_max=5.0,  # Same!
                y_min=0.0, y_max=10.0
            )
    
    def test_large_coordinate_values(self):
        """Coordenadas grandes pero válidas."""
        atom = AtomPosition(id=0, x=1000.0, y=-1000.0)
        assert atom.x == 1000.0
    
    def test_unicode_zone_id(self):
        """Zone ID con caracteres Unicode."""
        zone = ZoneDefinition(
            zone_id="zona_preparación_1",
            zone_type=ZoneType.PREPARATION,
            x_min=0.0, x_max=10.0,
            y_min=0.0, y_max=10.0
        )
        assert "preparación" in zone.zone_id


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

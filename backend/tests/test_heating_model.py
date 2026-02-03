"""
Heating Model Tests (v3.0)
==========================

Tests for vibrational heating and atom loss models.
"""

import pytest

from drivers.neutral_atom.schema import (
    HeatingModel,
    AtomLossModel,
    AtomPosition,
    TrapRole,
    NeutralAtomRegister,
    ShuttleMove,
    DeviceConfig,
    NeutralAtomJob,
    Measurement,
)

from drivers.neutral_atom.validator import (
    PulserValidator,
    validate_job,
)


class TestHeatingModel:
    """Tests for HeatingModel physics calculations."""
    
    def test_calculate_nvib_increase(self):
        """Basic n_vib calculation."""
        # 10 µm at 0.5 µm/µs = 10 × 0.5 × 0.01 = 0.05
        delta = HeatingModel.calculate_nvib_increase(10.0, 0.5)
        assert delta == pytest.approx(0.05, rel=1e-3)
    
    def test_high_velocity_high_heating(self):
        """High velocity causes high heating."""
        slow = HeatingModel.calculate_nvib_increase(10.0, 0.1)
        fast = HeatingModel.calculate_nvib_increase(10.0, 0.5)
        assert fast > slow
    
    def test_long_distance_high_heating(self):
        """Longer distance causes more heating."""
        short = HeatingModel.calculate_nvib_increase(5.0, 0.3)
        long = HeatingModel.calculate_nvib_increase(20.0, 0.3)
        assert long > short
    
    def test_fidelity_loss_estimate(self):
        """Fidelity loss scales with n_vib."""
        low_nvib = HeatingModel.estimate_fidelity_loss(5.0)
        high_nvib = HeatingModel.estimate_fidelity_loss(20.0)
        
        assert low_nvib < high_nvib
        assert low_nvib == pytest.approx(0.04, rel=1e-2)  # 5 × 0.008
        assert high_nvib == pytest.approx(0.16, rel=1e-2)  # 20 × 0.008
    
    def test_fidelity_loss_capped(self):
        """Fidelity loss caps at 1.0."""
        extreme = HeatingModel.estimate_fidelity_loss(200.0)
        assert extreme == 1.0


class TestAtomLossModel:
    """Tests for AtomLossModel predictions."""
    
    def test_base_loss_rate(self):
        """Below threshold, only base rate."""
        p = AtomLossModel.calculate_loss_probability(10.0)  # Below 18
        assert p == pytest.approx(0.001, rel=1e-2)
    
    def test_heating_increases_loss(self):
        """Above threshold, heating adds to loss."""
        p_low = AtomLossModel.calculate_loss_probability(15.0)
        p_high = AtomLossModel.calculate_loss_probability(25.0)
        assert p_high > p_low
    
    def test_loss_probability_formula(self):
        """Verify formula: base + factor × excess."""
        # nvib=25, threshold=18, excess=7
        # p = 0.001 + 0.005 × 7 = 0.036
        p = AtomLossModel.calculate_loss_probability(25.0)
        assert p == pytest.approx(0.036, rel=1e-2)
    
    def test_loss_capped_at_one(self):
        """Loss probability caps at 1.0."""
        p = AtomLossModel.calculate_loss_probability(1000.0)
        assert p == 1.0


class TestHeatingWarningsIntegration:
    """Integration tests for heating warnings in validator."""
    
    @pytest.fixture
    def aod_register(self):
        return NeutralAtomRegister(
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.AOD),
                AtomPosition(id=1, x=10.0, y=0.0, role=TrapRole.SLM),
            ]
        )
    
    def test_slow_movement_no_heating_warning(self, aod_register):
        """Slow movement should not trigger heating warnings."""
        move = ShuttleMove(
            atom_ids=[0],
            start_time=0,
            duration=50000,  # 50 µs for 5 µm = 0.1 µm/µs (slow)
            target_positions=[(5.0, 0.0)],
            trajectory="minimum_jerk"
        )
        job = NeutralAtomJob(
            device=DeviceConfig(backend_id="simulator"),
            register=aod_register,
            operations=[move]
        )
        result = validate_job(job)
        
        heating_warnings = [w for w in result.warnings if "HEATING" in w.code]
        assert len(heating_warnings) == 0
    
    def test_fast_movement_triggers_heating_warning(self, aod_register):
        """Fast, long movement should trigger heating warning."""
        move = ShuttleMove(
            atom_ids=[0],
            start_time=0,
            duration=5000,  # 5 µs for 20 µm = 4 µm/µs (VERY fast)
            target_positions=[(20.0, 0.0)],
            trajectory="linear"
        )
        job = NeutralAtomJob(
            device=DeviceConfig(backend_id="simulator"),
            register=aod_register,
            operations=[move]
        )
        result = validate_job(job)
        
        # Should have velocity error (exceeds limit) OR heating warning
        has_heating = any("HEATING" in w.code for w in result.warnings)
        has_velocity = any("VELOCITY" in w.code or "velocity" in w.message.lower() 
                          for w in result.warnings)
        has_velocity_error = not result.is_valid
        
        assert has_heating or has_velocity or has_velocity_error


class TestBusRole:
    """Tests for BUS (flying ancilla) role."""
    
    def test_bus_role_exists(self):
        """BUS role is available."""
        assert TrapRole.BUS.value == "BUS"
    
    def test_create_bus_atom(self):
        """Can create atom with BUS role."""
        atom = AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.BUS)
        assert atom.role == TrapRole.BUS
    
    def test_bus_in_register(self):
        """Register accepts BUS atoms."""
        reg = NeutralAtomRegister(
            atoms=[
                AtomPosition(id=0, x=0.0, y=0.0, role=TrapRole.SLM),  # Data
                AtomPosition(id=1, x=5.0, y=0.0, role=TrapRole.BUS),  # Ancilla
            ]
        )
        bus_atoms = [a for a in reg.atoms if a.role == TrapRole.BUS]
        assert len(bus_atoms) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

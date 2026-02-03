#!/usr/bin/env python3
"""
Experiment D: Zoned Architecture Cycle Analysis
================================================

Simulates error correction cycles in a zoned neutral atom architecture.
Measures heating per cycle and predicts qubit lifetime before replacement.

Based on: Harvard/MIT 2025 continuous-operation processor
- Storage Zone: Shielded via Autler-Townes effect
- Entanglement Zone: Active Rydberg gates
- Readout Zone: Fluorescence measurement
- Reservoir: Atom replenishment (~300k/s)

Author: Quantum Navigator Research Team
Date: February 2026
"""

import json
import csv
import math
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from enum import Enum

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from drivers.neutral_atom.schema import (
    HeatingModel,
    AtomLossModel,
    AtomPosition,
    TrapRole,
    NeutralAtomRegister,
    ZoneDefinition,
    ZoneType,
)


# =============================================================================
# ZONED ARCHITECTURE PARAMETERS
# =============================================================================

@dataclass
class ZonedArchitecture:
    """
    Defines a zoned neutral atom processor layout.
    Based on Harvard 2025 continuous-operation design.
    """
    # Zone positions (center, µm)
    storage_center: Tuple[float, float] = (-30.0, 0.0)
    entanglement_center: Tuple[float, float] = (0.0, 0.0)
    readout_center: Tuple[float, float] = (30.0, 0.0)
    reservoir_center: Tuple[float, float] = (-50.0, 0.0)
    
    # Zone sizes (half-width, µm)
    storage_size: float = 15.0
    entanglement_size: float = 20.0
    readout_size: float = 10.0
    
    # Transport distances (µm)
    storage_to_entanglement: float = 30.0
    entanglement_to_readout: float = 30.0
    storage_to_readout: float = 60.0
    reservoir_to_storage: float = 20.0
    
    def get_zone_definitions(self) -> List[ZoneDefinition]:
        """Generate ZoneDefinition objects."""
        return [
            ZoneDefinition(
                zone_id="storage",
                zone_type=ZoneType.STORAGE,
                x_min=self.storage_center[0] - self.storage_size,
                x_max=self.storage_center[0] + self.storage_size,
                y_min=-self.storage_size,
                y_max=self.storage_size,
                shielding_light=True
            ),
            ZoneDefinition(
                zone_id="entanglement",
                zone_type=ZoneType.ENTANGLEMENT,
                x_min=self.entanglement_center[0] - self.entanglement_size,
                x_max=self.entanglement_center[0] + self.entanglement_size,
                y_min=-self.entanglement_size,
                y_max=self.entanglement_size
            ),
            ZoneDefinition(
                zone_id="readout",
                zone_type=ZoneType.READOUT,
                x_min=self.readout_center[0] - self.readout_size,
                x_max=self.readout_center[0] + self.readout_size,
                y_min=-self.readout_size,
                y_max=self.readout_size
            ),
            ZoneDefinition(
                zone_id="reservoir",
                zone_type=ZoneType.RESERVOIR,
                x_min=self.reservoir_center[0] - 5,
                x_max=self.reservoir_center[0] + 5,
                y_min=-20,
                y_max=20
            )
        ]


# =============================================================================
# ERROR CORRECTION CYCLE MODEL
# =============================================================================

@dataclass
class ECCycleConfig:
    """Configuration for error correction cycle."""
    
    # Cycle timing
    syndrome_extraction_time_us: float = 100.0  # Time for one syndrome round
    gate_time_us: float = 1.0  # Two-qubit gate time
    measurement_time_us: float = 50.0  # Readout time
    
    # Transport parameters
    transport_velocity_um_per_us: float = 0.40  # Conservative velocity
    
    # Error correction parameters
    code_distance: int = 3  # Surface code distance
    
    @property
    def data_qubits(self) -> int:
        """Number of data qubits for surface code."""
        return self.code_distance ** 2
    
    @property
    def ancilla_qubits(self) -> int:
        """Number of ancilla qubits."""
        return (self.code_distance - 1) ** 2 * 2  # X and Z stabilizers


@dataclass
class CycleResult:
    """Result of one error correction cycle."""
    cycle_number: int
    data_qubits_moved: int
    ancilla_qubits_moved: int
    total_distance_um: float
    nvib_accumulated: float
    nvib_per_qubit_avg: float
    atom_loss_probability: float
    cycle_fidelity: float
    cumulative_fidelity: float


@dataclass
class LifetimeAnalysis:
    """Analysis of qubit lifetime in cyclic operation."""
    cycles_until_replacement: int
    total_distance_traveled_um: float
    final_nvib: float
    final_fidelity: float
    time_to_replacement_us: float


# =============================================================================
# CYCLE SIMULATOR
# =============================================================================

class ZonedCycleSimulator:
    """
    Simulates error correction cycles in zoned architecture.
    """
    
    def __init__(
        self,
        architecture: ZonedArchitecture,
        cycle_config: ECCycleConfig,
        physics: Optional[Dict] = None
    ):
        self.arch = architecture
        self.config = cycle_config
        self.physics = physics or {
            'heating_coeff': 0.01,
            'critical_nvib': 18.0,
            'fidelity_rate': 0.008,
            'replacement_threshold': 0.90  # Replace when fidelity < 90%
        }
        
        # State tracking
        self.qubit_nvib: Dict[int, float] = {}
        self.qubit_distance: Dict[int, float] = {}
        self.cycle_count = 0
    
    def initialize_qubits(self) -> None:
        """Initialize qubits in storage zone."""
        total_qubits = self.config.data_qubits + self.config.ancilla_qubits
        self.qubit_nvib = {i: 0.0 for i in range(total_qubits)}
        self.qubit_distance = {i: 0.0 for i in range(total_qubits)}
        self.cycle_count = 0
    
    def simulate_single_cycle(self) -> CycleResult:
        """
        Simulate one error correction cycle.
        
        Cycle phases:
        1. Move data qubits: Storage → Entanglement
        2. Perform stabilizer measurements (gates)
        3. Move ancillas: Entanglement → Readout
        4. Measure ancillas
        5. Move data qubits: Entanglement → Storage
        6. Move ancillas: Readout → Entanglement (or replace)
        """
        self.cycle_count += 1
        cycle_nvib = 0.0
        cycle_distance = 0.0
        
        v = self.config.transport_velocity_um_per_us
        
        # Phase 1: Data qubits Storage → Entanglement
        d1 = self.arch.storage_to_entanglement
        for i in range(self.config.data_qubits):
            delta = HeatingModel.calculate_nvib_increase(d1, v)
            self.qubit_nvib[i] += delta
            self.qubit_distance[i] += d1
            cycle_nvib += delta
            cycle_distance += d1
        
        # Phase 2: Gates (minimal heating, mostly time)
        # Heating during gate execution is negligible
        
        # Phase 3: Ancillas Entanglement → Readout  
        d2 = self.arch.entanglement_to_readout
        ancilla_start = self.config.data_qubits
        for i in range(ancilla_start, ancilla_start + self.config.ancilla_qubits):
            delta = HeatingModel.calculate_nvib_increase(d2, v)
            self.qubit_nvib[i] += delta
            self.qubit_distance[i] += d2
            cycle_nvib += delta
            cycle_distance += d2
        
        # Phase 4: Measurement (ancillas are measured)
        # No heating during measurement
        
        # Phase 5: Data qubits Entanglement → Storage
        for i in range(self.config.data_qubits):
            delta = HeatingModel.calculate_nvib_increase(d1, v)
            self.qubit_nvib[i] += delta
            self.qubit_distance[i] += d1
            cycle_nvib += delta
            cycle_distance += d1
        
        # Phase 6: Ancillas Readout → Entanglement (or fresh from reservoir)
        # Assume fresh ancillas each cycle (from reservoir)
        for i in range(ancilla_start, ancilla_start + self.config.ancilla_qubits):
            self.qubit_nvib[i] = 0.0  # Fresh ancilla
            self.qubit_distance[i] = 0.0
        
        # Calculate metrics
        data_nvib = [self.qubit_nvib[i] for i in range(self.config.data_qubits)]
        avg_nvib = sum(data_nvib) / len(data_nvib) if data_nvib else 0
        max_nvib = max(data_nvib) if data_nvib else 0
        
        # Fidelity based on worst qubit
        fidelity_loss = HeatingModel.estimate_fidelity_loss(max_nvib)
        cycle_fidelity = 1.0 - fidelity_loss
        
        # Atom loss probability
        p_loss = AtomLossModel.calculate_loss_probability(max_nvib)
        
        return CycleResult(
            cycle_number=self.cycle_count,
            data_qubits_moved=self.config.data_qubits * 2,  # Round trip
            ancilla_qubits_moved=self.config.ancilla_qubits,
            total_distance_um=cycle_distance,
            nvib_accumulated=cycle_nvib,
            nvib_per_qubit_avg=avg_nvib,
            atom_loss_probability=p_loss,
            cycle_fidelity=cycle_fidelity,
            cumulative_fidelity=cycle_fidelity  # Updated below
        )
    
    def simulate_until_replacement(self) -> Tuple[List[CycleResult], LifetimeAnalysis]:
        """
        Simulate cycles until qubit needs replacement.
        """
        self.initialize_qubits()
        results = []
        cumulative_fidelity = 1.0
        threshold = self.physics['replacement_threshold']
        
        while cumulative_fidelity > threshold and self.cycle_count < 1000:
            result = self.simulate_single_cycle()
            cumulative_fidelity *= result.cycle_fidelity
            result.cumulative_fidelity = cumulative_fidelity
            results.append(result)
        
        # Total stats
        total_distance = sum(r.total_distance_um for r in results)
        final_nvib = max(self.qubit_nvib.values()) if self.qubit_nvib else 0
        cycle_time_us = (
            self.config.syndrome_extraction_time_us +
            2 * self.arch.storage_to_entanglement / self.config.transport_velocity_um_per_us +
            self.arch.entanglement_to_readout / self.config.transport_velocity_um_per_us +
            self.config.measurement_time_us
        )
        
        lifetime = LifetimeAnalysis(
            cycles_until_replacement=len(results),
            total_distance_traveled_um=total_distance,
            final_nvib=final_nvib,
            final_fidelity=cumulative_fidelity,
            time_to_replacement_us=len(results) * cycle_time_us
        )
        
        return results, lifetime


# =============================================================================
# EXPERIMENT RUNNER
# =============================================================================

@dataclass
class ExperimentConfig:
    """Configuration for Experiment D."""
    code_distances: List[int] = field(default_factory=lambda: [3, 5, 7, 9])
    velocities: List[float] = field(default_factory=lambda: [0.20, 0.30, 0.40, 0.50])
    output_dir: str = "./benchmark_results"


def run_zone_experiment(config: ExperimentConfig) -> List[dict]:
    """Run zoned architecture cycling experiment."""
    arch = ZonedArchitecture()
    results = []
    
    print(f"\n{'='*90}")
    print("EXPERIMENT D: Zoned Architecture Cycle Analysis")
    print(f"{'='*90}")
    print(f"Code distances: {config.code_distances}")
    print(f"Velocities: {config.velocities} µm/µs")
    print(f"Architecture: Storage←{arch.storage_to_entanglement}µm→Entanglement"
          f"←{arch.entanglement_to_readout}µm→Readout")
    print(f"{'='*90}\n")
    
    print(f"{'d':<4} {'v (µm/µs)':<12} {'Data Q':<8} {'Cycles':<8} "
          f"{'Distance':<12} {'Final F':<10} {'Time (ms)':<12}")
    print("-" * 90)
    
    for d in config.code_distances:
        for v in config.velocities:
            cycle_config = ECCycleConfig(
                code_distance=d,
                transport_velocity_um_per_us=v
            )
            
            simulator = ZonedCycleSimulator(arch, cycle_config)
            cycle_results, lifetime = simulator.simulate_until_replacement()
            
            time_ms = lifetime.time_to_replacement_us / 1000
            
            print(f"{d:<4} {v:<12.2f} {cycle_config.data_qubits:<8} "
                  f"{lifetime.cycles_until_replacement:<8} "
                  f"{lifetime.total_distance_traveled_um:<12.1f} "
                  f"{lifetime.final_fidelity:<10.4f} {time_ms:<12.2f}")
            
            results.append({
                'code_distance': d,
                'velocity': v,
                'data_qubits': cycle_config.data_qubits,
                'ancilla_qubits': cycle_config.ancilla_qubits,
                'cycles_until_replacement': lifetime.cycles_until_replacement,
                'total_distance_um': lifetime.total_distance_traveled_um,
                'final_nvib': lifetime.final_nvib,
                'final_fidelity': lifetime.final_fidelity,
                'time_to_replacement_ms': time_ms,
                'heating_per_cycle': (lifetime.final_nvib / 
                                     max(1, lifetime.cycles_until_replacement))
            })
    
    return results


def save_results(results: List[dict], config: ExperimentConfig):
    """Save results."""
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / "experiment_d_zoned_cycles.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    json_path = output_dir / "experiment_d_zoned_cycles.json"
    with open(json_path, 'w') as f:
        json.dump({
            'config': asdict(config),
            'architecture': asdict(ZonedArchitecture()),
            'results': results,
            'metadata': {
                'experiment': 'D: Zoned Architecture Cycles',
                'reference': 'Harvard/MIT 2025 Continuous Operation'
            }
        }, f, indent=2)
    
    print(f"\n📊 Results saved to: {csv_path}")


def generate_analysis(results: List[dict]):
    """Generate summary analysis."""
    print(f"\n{'='*90}")
    print("ANALYSIS: Qubit Lifetime in Zoned Architecture")
    print(f"{'='*90}")
    
    # Best configuration
    best = max(results, key=lambda r: r['cycles_until_replacement'])
    print(f"\n🏆 BEST CONFIGURATION:")
    print(f"   Code distance: {best['code_distance']}")
    print(f"   Velocity: {best['velocity']} µm/µs")
    print(f"   Cycles before replacement: {best['cycles_until_replacement']}")
    print(f"   Qubit lifetime: {best['time_to_replacement_ms']:.1f} ms")
    
    # Heating analysis
    print(f"\n📈 HEATING RATE ANALYSIS:")
    for d in sorted(set(r['code_distance'] for r in results)):
        subset = [r for r in results if r['code_distance'] == d]
        avg_heating = sum(r['heating_per_cycle'] for r in subset) / len(subset)
        print(f"   d={d}: Avg Δn_vib/cycle = {avg_heating:.4f}")
    
    # Velocity recommendation
    print(f"\n⚡ VELOCITY RECOMMENDATION:")
    by_v = {}
    for r in results:
        v = r['velocity']
        if v not in by_v:
            by_v[v] = []
        by_v[v].append(r['cycles_until_replacement'])
    
    for v, cycles in sorted(by_v.items()):
        avg_cycles = sum(cycles) / len(cycles)
        print(f"   v={v} µm/µs: Avg {avg_cycles:.0f} cycles")
    
    print(f"\n{'='*90}")
    print("CONCLUSION: Slower transport significantly extends qubit lifetime")
    print("Trade-off: Slower velocity = longer cycle time but more cycles possible")
    print(f"{'='*90}")


def main():
    """Run Experiment D."""
    config = ExperimentConfig(
        code_distances=[3, 5, 7, 9],
        velocities=[0.20, 0.30, 0.40, 0.50],
        output_dir="./benchmark_results"
    )
    
    results = run_zone_experiment(config)
    save_results(results, config)
    generate_analysis(results)
    
    return results


if __name__ == "__main__":
    main()

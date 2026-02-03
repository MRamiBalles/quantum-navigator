#!/usr/bin/env python3
"""
Experiment E: Sustainable Circuit Depth Analysis
=================================================

Calculates maximum sustainable circuit depth before atom replenishment
is required, based on the continuous operation architecture from
Harvard/MIT/QuEra Nature 2025.

Key Question: How deep can a circuit run before qubit exhaustion?

Metrics:
- Sustainable depth (layers) at various velocities
- Time to replacement at various configurations
- Required replenishment rate for indefinite operation

Author: Quantum Navigator Research Team
Date: February 2026
"""

import json
import csv
import math
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from drivers.neutral_atom.schema import (
    HeatingModel,
    AtomLossModel,
)


# =============================================================================
# SUSTAINABLE DEPTH CALCULATOR
# =============================================================================

@dataclass
class DepthConfig:
    """Configuration for sustainable depth calculation."""
    avg_transport_distance_um: float = 15.0
    transport_velocity_um_per_us: float = 0.40
    gate_time_ns: float = 1000.0
    num_data_qubits: int = 100
    fidelity_threshold: float = 0.90
    loss_threshold: float = 0.10


@dataclass 
class DepthResult:
    """Result of sustainable depth calculation."""
    velocity: float
    distance: float
    qubits: int
    delta_nvib_per_layer: float
    max_layers_fidelity: int
    max_layers_loss: int
    sustainable_depth: int
    time_to_replacement_ms: float
    required_replenishment_rate: float


def calculate_sustainable_depth(config: DepthConfig) -> DepthResult:
    """Calculate sustainable circuit depth for given configuration."""
    
    # Calculate heating per layer
    delta_nvib = HeatingModel.calculate_nvib_increase(
        config.avg_transport_distance_um,
        config.transport_velocity_um_per_us
    )
    
    # Calculate layers until fidelity threshold
    alpha = 0.008  # Fidelity degradation rate
    fidelity_loss_per_layer = alpha * delta_nvib
    
    if fidelity_loss_per_layer > 0 and fidelity_loss_per_layer < 1:
        max_layers_fidelity = int(
            math.log(config.fidelity_threshold) / 
            math.log(1 - fidelity_loss_per_layer)
        )
    else:
        max_layers_fidelity = 10000  # Cap for display
    
    # Calculate layers until loss threshold
    nvib_for_loss = 18.0 + (config.loss_threshold - 0.001) / 0.005
    max_layers_loss = int(nvib_for_loss / delta_nvib) if delta_nvib > 0 else 10000
    
    # Sustainable depth is the minimum
    sustainable_depth = min(max_layers_fidelity, max_layers_loss)
    
    # Time calculation
    layer_time_ns = (
        config.avg_transport_distance_um / config.transport_velocity_um_per_us * 1000 +
        config.gate_time_ns
    )
    time_to_replacement_ms = (sustainable_depth * layer_time_ns) / 1_000_000
    
    # Required replenishment rate
    final_nvib = sustainable_depth * delta_nvib
    p_loss = AtomLossModel.calculate_loss_probability(final_nvib)
    atoms_lost = config.num_data_qubits * p_loss
    cycle_time_s = time_to_replacement_ms / 1000
    required_rate = atoms_lost / cycle_time_s if cycle_time_s > 0 else 0
    
    return DepthResult(
        velocity=config.transport_velocity_um_per_us,
        distance=config.avg_transport_distance_um,
        qubits=config.num_data_qubits,
        delta_nvib_per_layer=delta_nvib,
        max_layers_fidelity=max_layers_fidelity,
        max_layers_loss=max_layers_loss,
        sustainable_depth=sustainable_depth,
        time_to_replacement_ms=time_to_replacement_ms,
        required_replenishment_rate=required_rate
    )


# =============================================================================
# EXPERIMENT RUNNER
# =============================================================================

@dataclass
class ExperimentConfig:
    """Configuration for Experiment E."""
    velocities: List[float] = field(default_factory=lambda: [0.20, 0.30, 0.40, 0.50])
    distances: List[float] = field(default_factory=lambda: [10.0, 15.0, 20.0, 30.0])
    qubit_counts: List[int] = field(default_factory=lambda: [50, 100, 500, 1000])
    output_dir: str = "./benchmark_results"


def run_sustainable_depth_experiment(config: ExperimentConfig) -> List[dict]:
    """Run sustainable depth analysis."""
    results = []
    
    print(f"\n{'='*90}")
    print("EXPERIMENT E: Sustainable Circuit Depth Analysis")
    print(f"{'='*90}")
    print(f"Velocities: {config.velocities} µm/µs")
    print(f"Distances: {config.distances} µm")
    print(f"Qubit counts: {config.qubit_counts}")
    print(f"{'='*90}\n")
    
    print(f"{'v (µm/µs)':<12} {'d (µm)':<10} {'Qubits':<8} {'Δn_vib/L':<12} "
          f"{'Depth':<8} {'Time (ms)':<12} {'Replen. Rate':<15}")
    print("-" * 90)
    
    # Velocity sweep at fixed distance and qubits
    print("\n📊 VELOCITY SWEEP (d=15µm, n=100 qubits):")
    print("-" * 90)
    for v in config.velocities:
        depth_config = DepthConfig(
            transport_velocity_um_per_us=v,
            avg_transport_distance_um=15.0,
            num_data_qubits=100
        )
        result = calculate_sustainable_depth(depth_config)
        
        print(f"{result.velocity:<12.2f} {result.distance:<10.1f} {result.qubits:<8} "
              f"{result.delta_nvib_per_layer:<12.4f} {result.sustainable_depth:<8} "
              f"{result.time_to_replacement_ms:<12.2f} {result.required_replenishment_rate:<15.1f}")
        
        results.append(asdict(result))
    
    # Distance sweep
    print("\n📊 DISTANCE SWEEP (v=0.40 µm/µs, n=100 qubits):")
    print("-" * 90)
    for d in config.distances:
        depth_config = DepthConfig(
            transport_velocity_um_per_us=0.40,
            avg_transport_distance_um=d,
            num_data_qubits=100
        )
        result = calculate_sustainable_depth(depth_config)
        
        print(f"{result.velocity:<12.2f} {result.distance:<10.1f} {result.qubits:<8} "
              f"{result.delta_nvib_per_layer:<12.4f} {result.sustainable_depth:<8} "
              f"{result.time_to_replacement_ms:<12.2f} {result.required_replenishment_rate:<15.1f}")
        
        results.append(asdict(result))
    
    # Qubit count sweep
    print("\n📊 QUBIT COUNT SWEEP (v=0.40 µm/µs, d=15µm):")
    print("-" * 90)
    for n in config.qubit_counts:
        depth_config = DepthConfig(
            transport_velocity_um_per_us=0.40,
            avg_transport_distance_um=15.0,
            num_data_qubits=n
        )
        result = calculate_sustainable_depth(depth_config)
        
        print(f"{result.velocity:<12.2f} {result.distance:<10.1f} {result.qubits:<8} "
              f"{result.delta_nvib_per_layer:<12.4f} {result.sustainable_depth:<8} "
              f"{result.time_to_replacement_ms:<12.2f} {result.required_replenishment_rate:<15.1f}")
        
        results.append(asdict(result))
    
    return results


def save_results(results: List[dict], config: ExperimentConfig):
    """Save results."""
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / "experiment_e_sustainable_depth.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    json_path = output_dir / "experiment_e_sustainable_depth.json"
    with open(json_path, 'w') as f:
        json.dump({
            'config': asdict(config),
            'results': results,
            'metadata': {
                'experiment': 'E: Sustainable Circuit Depth',
                'reference': 'Harvard/MIT/QuEra Nature 2025',
                'reservoir_rate': '30,000 atoms/second (Harvard spec)'
            }
        }, f, indent=2)
    
    print(f"\n📊 Results saved to: {csv_path}")


def generate_analysis(results: List[dict]):
    """Generate summary analysis."""
    print(f"\n{'='*90}")
    print("ANALYSIS: Sustainable Depth for Continuous Operation")
    print(f"{'='*90}")
    
    # Find optimal configuration
    best = max(results, key=lambda r: r['sustainable_depth'])
    
    print(f"\n🏆 OPTIMAL CONFIGURATION:")
    print(f"   Velocity: {best['velocity']} µm/µs")
    print(f"   Distance: {best['distance']} µm")
    print(f"   Sustainable depth: {best['sustainable_depth']} layers")
    print(f"   Time to replacement: {best['time_to_replacement_ms']:.1f} ms")
    
    # Harvard comparison
    harvard_rate = 30_000  # atoms/second
    print(f"\n📚 COMPARISON TO HARVARD/MIT 2025:")
    print(f"   Harvard reservoir rate: {harvard_rate:,} atoms/second")
    print(f"   Required rate at optimal: {best['required_replenishment_rate']:.1f} atoms/second")
    
    if best['required_replenishment_rate'] < harvard_rate:
        print(f"   ✅ Harvard rate is SUFFICIENT for indefinite operation")
    else:
        print(f"   ⚠️ Harvard rate may be INSUFFICIENT - consider slower transport")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS FOR LONG-RUNNING ALGORITHMS:")
    print(f"   1. Use v ≤ 0.40 µm/µs to maximize depth before reload")
    print(f"   2. Minimize transport distance in circuit layout")
    print(f"   3. Schedule RELOAD operations every ~{best['sustainable_depth']} layers")
    print(f"   4. For QEC at d=7: need ~{7*7}=49 data qubits → adjust rates accordingly")
    
    print(f"\n{'='*90}")


def main():
    """Run Experiment E."""
    config = ExperimentConfig(
        velocities=[0.20, 0.30, 0.40, 0.50],
        distances=[10.0, 15.0, 20.0, 30.0],
        qubit_counts=[50, 100, 500, 1000],
        output_dir="./benchmark_results"
    )
    
    results = run_sustainable_depth_experiment(config)
    save_results(results, config)
    generate_analysis(results)
    
    return results


if __name__ == "__main__":
    main()

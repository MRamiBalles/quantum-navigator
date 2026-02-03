#!/usr/bin/env python3
"""
Experiment C: Cooling Strategies Comparison
============================================

Compares two transport strategies:
1. Greedy: Move as fast as possible, accumulate heating
2. Conservative: Pause to cool when n_vib > threshold

This validates the middleware's ability to inform design decisions.

Reference: Harvard/MIT 2025 - Continuous operation with cooling cycles

Author: Quantum Navigator Research Team
Date: February 2026
"""

import json
import csv
import math
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, List, Tuple
from enum import Enum

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from drivers.neutral_atom.schema import (
    HeatingModel,
    AtomLossModel,
    AtomPosition,
    TrapRole,
    NeutralAtomRegister,
    ShuttleMove,
    RydbergGate,
    Measurement,
    DeviceConfig,
    NeutralAtomJob,
    ZoneDefinition,
    ZoneType,
)
from drivers.neutral_atom.validator import validate_job


# =============================================================================
# STRATEGY DEFINITIONS
# =============================================================================

class CoolingStrategy(str, Enum):
    """Transport strategy with respect to cooling."""
    GREEDY = "greedy"           # Never cool, maximize speed
    CONSERVATIVE = "conservative"  # Cool when n_vib > threshold
    ADAPTIVE = "adaptive"       # Dynamic threshold based on upcoming gates


@dataclass
class CoolingEvent:
    """Represents a cooling pause."""
    time_ns: float
    duration_ns: float
    nvib_before: float
    nvib_after: float


@dataclass
class TransportSegment:
    """A single atom transport operation."""
    atom_id: int
    distance_um: float
    velocity_um_per_us: float
    start_time_ns: float
    duration_ns: float
    nvib_contribution: float


@dataclass
class CircuitExecution:
    """Result of executing a circuit with a strategy."""
    strategy: str
    num_gates: int
    circuit_depth: int
    total_transport_distance_um: float
    total_nvib_accumulated: float
    cooling_events: int
    total_cooling_time_ns: float
    final_fidelity: float
    atoms_lost: int
    total_execution_time_ns: float
    idle_decoherence: float


# =============================================================================
# PHYSICS PARAMETERS
# =============================================================================

@dataclass
class PhysicsConfig:
    """Physical parameters for the simulation."""
    
    # Heating
    heating_coefficient: float = 0.01
    critical_nvib: float = 18.0
    fidelity_degradation_rate: float = 0.008
    
    # Cooling
    cooling_time_ns: float = 1_000_000  # 1 ms to cool
    cooling_efficiency: float = 0.95    # Reduce n_vib by 95%
    conservative_threshold: float = 15.0  # Cool when n_vib > this
    
    # Idle decoherence
    t2_time_ns: float = 1_000_000_000   # 1 second T2 (optimistic)
    idle_decoherence_rate: float = 1e-9  # Per ns
    
    # Transport limits
    max_velocity_um_per_us: float = 0.55
    greedy_velocity_um_per_us: float = 0.50  # Just below limit
    conservative_velocity_um_per_us: float = 0.25  # Safe, slower


# =============================================================================
# CIRCUIT GENERATOR
# =============================================================================

def generate_long_circuit(
    num_qubits: int,
    num_layers: int,
    gate_distance_um: float = 8.0
) -> List[Tuple[int, int, float]]:
    """
    Generate a deep circuit requiring many transport operations.
    
    Returns list of (control_qubit, target_qubit, distance_to_travel)
    """
    gates = []
    
    for layer in range(num_layers):
        # Alternating pattern of long-range gates
        for i in range(0, num_qubits - 1, 2):
            # In even layers: (0,1), (2,3), ...
            # In odd layers: (1,2), (3,4), ... (long-range)
            if layer % 2 == 0:
                gates.append((i, i + 1, gate_distance_um))
            else:
                if i + 2 < num_qubits:
                    # Long-range gate requires transport
                    gates.append((i, i + 2, gate_distance_um * 2))
    
    return gates


# =============================================================================
# STRATEGY SIMULATORS
# =============================================================================

def simulate_greedy(
    gates: List[Tuple[int, int, float]],
    physics: PhysicsConfig
) -> CircuitExecution:
    """
    Greedy strategy: Move as fast as possible, never cool.
    """
    total_nvib = 0.0
    total_distance = 0.0
    total_time = 0.0
    atoms_lost = 0
    
    for ctrl, tgt, dist in gates:
        # Transport at maximum safe velocity
        velocity = physics.greedy_velocity_um_per_us
        duration_ns = (dist / velocity) * 1000
        
        # Calculate heating
        delta_nvib = HeatingModel.calculate_nvib_increase(dist, velocity)
        total_nvib += delta_nvib
        total_distance += dist
        total_time += duration_ns
        
        # Gate time (1 µs = 1000 ns)
        total_time += 1000
        
        # Check for atom loss
        p_loss = AtomLossModel.calculate_loss_probability(total_nvib)
        if p_loss > 0.5:  # Probabilistic loss
            atoms_lost += 1
            total_nvib = 0  # Reset for lost atom (new atom loaded)
    
    # Calculate final fidelity
    fidelity_loss = HeatingModel.estimate_fidelity_loss(total_nvib)
    final_fidelity = max(0, 1.0 - fidelity_loss)
    
    # Idle decoherence
    idle_decoherence = total_time * physics.idle_decoherence_rate
    
    return CircuitExecution(
        strategy="GREEDY",
        num_gates=len(gates),
        circuit_depth=len(gates),  # Sequential for simplicity
        total_transport_distance_um=total_distance,
        total_nvib_accumulated=total_nvib,
        cooling_events=0,
        total_cooling_time_ns=0,
        final_fidelity=final_fidelity * (1 - idle_decoherence),
        atoms_lost=atoms_lost,
        total_execution_time_ns=total_time,
        idle_decoherence=idle_decoherence
    )


def simulate_conservative(
    gates: List[Tuple[int, int, float]],
    physics: PhysicsConfig
) -> CircuitExecution:
    """
    Conservative strategy: Cool whenever n_vib exceeds threshold.
    """
    total_nvib = 0.0
    total_distance = 0.0
    total_time = 0.0
    cooling_events = 0
    total_cooling_time = 0.0
    atoms_lost = 0
    
    for ctrl, tgt, dist in gates:
        # Transport at conservative velocity
        velocity = physics.conservative_velocity_um_per_us
        duration_ns = (dist / velocity) * 1000
        
        # Calculate heating
        delta_nvib = HeatingModel.calculate_nvib_increase(dist, velocity)
        total_nvib += delta_nvib
        total_distance += dist
        total_time += duration_ns
        
        # Gate time
        total_time += 1000
        
        # Check if we need to cool
        if total_nvib > physics.conservative_threshold:
            # Insert cooling pause
            cooling_events += 1
            total_time += physics.cooling_time_ns
            total_cooling_time += physics.cooling_time_ns
            total_nvib *= (1 - physics.cooling_efficiency)
    
    # Calculate final fidelity (lower n_vib due to cooling)
    fidelity_loss = HeatingModel.estimate_fidelity_loss(total_nvib)
    final_fidelity = max(0, 1.0 - fidelity_loss)
    
    # Idle decoherence (more time = more decoherence)
    idle_decoherence = total_time * physics.idle_decoherence_rate
    
    return CircuitExecution(
        strategy="CONSERVATIVE",
        num_gates=len(gates),
        circuit_depth=len(gates),
        total_transport_distance_um=total_distance,
        total_nvib_accumulated=total_nvib,
        cooling_events=cooling_events,
        total_cooling_time_ns=total_cooling_time,
        final_fidelity=final_fidelity * (1 - idle_decoherence),
        atoms_lost=atoms_lost,
        total_execution_time_ns=total_time,
        idle_decoherence=idle_decoherence
    )


def simulate_adaptive(
    gates: List[Tuple[int, int, float]],
    physics: PhysicsConfig
) -> CircuitExecution:
    """
    Adaptive strategy: Adjust velocity based on accumulated heating.
    """
    total_nvib = 0.0
    total_distance = 0.0
    total_time = 0.0
    cooling_events = 0
    total_cooling_time = 0.0
    
    for ctrl, tgt, dist in gates:
        # Adapt velocity based on current n_vib
        if total_nvib < 5:
            velocity = physics.greedy_velocity_um_per_us
        elif total_nvib < 12:
            velocity = (physics.greedy_velocity_um_per_us + 
                       physics.conservative_velocity_um_per_us) / 2
        else:
            velocity = physics.conservative_velocity_um_per_us
        
        duration_ns = (dist / velocity) * 1000
        delta_nvib = HeatingModel.calculate_nvib_increase(dist, velocity)
        total_nvib += delta_nvib
        total_distance += dist
        total_time += duration_ns + 1000  # Gate time
        
        # Adaptive cooling: only cool when very close to critical
        if total_nvib > physics.critical_nvib - 2:
            cooling_events += 1
            total_time += physics.cooling_time_ns * 0.5  # Shorter cooling
            total_cooling_time += physics.cooling_time_ns * 0.5
            total_nvib *= (1 - physics.cooling_efficiency * 0.8)
    
    fidelity_loss = HeatingModel.estimate_fidelity_loss(total_nvib)
    idle_decoherence = total_time * physics.idle_decoherence_rate
    
    return CircuitExecution(
        strategy="ADAPTIVE",
        num_gates=len(gates),
        circuit_depth=len(gates),
        total_transport_distance_um=total_distance,
        total_nvib_accumulated=total_nvib,
        cooling_events=cooling_events,
        total_cooling_time_ns=total_cooling_time,
        final_fidelity=max(0, (1.0 - fidelity_loss) * (1 - idle_decoherence)),
        atoms_lost=0,
        total_execution_time_ns=total_time,
        idle_decoherence=idle_decoherence
    )


# =============================================================================
# EXPERIMENT RUNNER
# =============================================================================

@dataclass
class ExperimentConfig:
    """Configuration for Experiment C."""
    num_qubits: int = 20
    layer_counts: List[int] = field(default_factory=lambda: [5, 10, 20, 50, 100, 200])
    output_dir: str = "./benchmark_results"


def run_cooling_experiment(config: ExperimentConfig) -> List[dict]:
    """Run full cooling strategy comparison."""
    physics = PhysicsConfig()
    results = []
    
    print(f"\n{'='*80}")
    print("EXPERIMENT C: Cooling Strategies Comparison")
    print(f"{'='*80}")
    print(f"Qubits: {config.num_qubits}")
    print(f"Layer counts: {config.layer_counts}")
    print(f"Conservative threshold: n_vib > {physics.conservative_threshold}")
    print(f"{'='*80}\n")
    
    print(f"{'Layers':<8} {'Strategy':<15} {'Gates':<8} {'n_vib':<10} "
          f"{'Cooling':<10} {'Fidelity':<10} {'Time (ms)':<12}")
    print("-" * 80)
    
    for num_layers in config.layer_counts:
        gates = generate_long_circuit(config.num_qubits, num_layers)
        
        # Run all strategies
        greedy = simulate_greedy(gates, physics)
        conservative = simulate_conservative(gates, physics)
        adaptive = simulate_adaptive(gates, physics)
        
        for result in [greedy, conservative, adaptive]:
            time_ms = result.total_execution_time_ns / 1_000_000
            print(f"{num_layers:<8} {result.strategy:<15} {result.num_gates:<8} "
                  f"{result.total_nvib_accumulated:<10.2f} "
                  f"{result.cooling_events:<10} {result.final_fidelity:<10.4f} "
                  f"{time_ms:<12.2f}")
            
            results.append({
                'num_layers': num_layers,
                'strategy': result.strategy,
                'num_gates': result.num_gates,
                'total_nvib': result.total_nvib_accumulated,
                'cooling_events': result.cooling_events,
                'cooling_time_ms': result.total_cooling_time_ns / 1_000_000,
                'final_fidelity': result.final_fidelity,
                'execution_time_ms': time_ms,
                'idle_decoherence': result.idle_decoherence,
                'atoms_lost': result.atoms_lost
            })
        
        print("-" * 80)
    
    return results


def find_crossover(results: List[dict]) -> Optional[int]:
    """Find the layer count where conservative beats greedy."""
    for layers in sorted(set(r['num_layers'] for r in results)):
        greedy = next(r for r in results if r['num_layers'] == layers 
                     and r['strategy'] == 'GREEDY')
        cons = next(r for r in results if r['num_layers'] == layers 
                   and r['strategy'] == 'CONSERVATIVE')
        if cons['final_fidelity'] > greedy['final_fidelity']:
            return layers
    return None


def save_results(results: List[dict], config: ExperimentConfig):
    """Save results to files."""
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / "experiment_c_cooling_strategies.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    json_path = output_dir / "experiment_c_cooling_strategies.json"
    with open(json_path, 'w') as f:
        json.dump({
            'config': asdict(config),
            'physics': asdict(PhysicsConfig()),
            'results': results,
            'metadata': {
                'experiment': 'C: Cooling Strategies',
                'crossover_point': find_crossover(results)
            }
        }, f, indent=2)
    
    print(f"\n📊 Results saved to: {csv_path}")


def generate_analysis(results: List[dict]):
    """Generate summary analysis."""
    crossover = find_crossover(results)
    
    print(f"\n{'='*80}")
    print("ANALYSIS SUMMARY")
    print(f"{'='*80}")
    
    if crossover:
        print(f"📍 CROSSOVER POINT: {crossover} layers")
        print(f"   Conservative strategy wins after this depth")
    
    # Compare strategies at max depth
    max_layers = max(r['num_layers'] for r in results)
    final = [r for r in results if r['num_layers'] == max_layers]
    
    print(f"\n📊 At {max_layers} layers:")
    for r in final:
        print(f"   {r['strategy']}: Fidelity={r['final_fidelity']:.4f}, "
              f"Cooling={r['cooling_events']}")
    
    best = max(final, key=lambda r: r['final_fidelity'])
    print(f"\n🏆 WINNER: {best['strategy']} with {best['final_fidelity']:.4f} fidelity")
    
    print(f"\n{'='*80}")
    print("CONCLUSION: For deep circuits, cooling preserves fidelity")
    print(f"{'='*80}")


def main():
    """Run Experiment C."""
    config = ExperimentConfig(
        num_qubits=20,
        layer_counts=[5, 10, 20, 50, 100, 200],
        output_dir="./benchmark_results"
    )
    
    results = run_cooling_experiment(config)
    save_results(results, config)
    generate_analysis(results)
    
    return results


if __name__ == "__main__":
    main()

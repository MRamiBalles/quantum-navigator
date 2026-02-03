#!/usr/bin/env python3
"""
Benchmark Plotting Utilities
============================

Generates publication-quality figures from benchmark results.
Requires matplotlib and seaborn.

Usage:
    python plot_results.py

Output:
    ./benchmark_results/figures/
        fig1_velocity_fidelity.pdf
        fig2_depth_comparison.pdf
        fig3_cooling_strategies.pdf
        fig4_zoned_lifetime.pdf

Author: Quantum Navigator Research Team
Date: February 2026
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️ matplotlib not found. Install with: pip install matplotlib")

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


# =============================================================================
# STYLE CONFIGURATION
# =============================================================================

def setup_style():
    """Configure publication-quality plot style."""
    if HAS_SEABORN:
        sns.set_theme(style="whitegrid", palette="deep")
    
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'legend.fontsize': 11,
        'figure.figsize': (8, 6),
        'figure.dpi': 150,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'axes.grid': True,
        'grid.alpha': 0.3,
    })


# =============================================================================
# FIGURE 1: VELOCITY VS FIDELITY
# =============================================================================

def plot_velocity_fidelity(results_dir: Path, output_dir: Path):
    """Plot Experiment A: Velocity-Fidelity trade-off."""
    json_path = results_dir / "experiment_a_velocity_fidelity.json"
    
    if not json_path.exists():
        print(f"⚠️ {json_path} not found. Run experiment A first.")
        return
    
    with open(json_path) as f:
        data = json.load(f)
    
    results = data['results']
    velocities = [r['velocity_um_per_us'] for r in results]
    fidelities = [r['fidelity'] for r in results]
    nvib = [r['delta_nvib'] for r in results]
    exceeds = [r['exceeds_critical'] for r in results]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Left: Fidelity vs Velocity
    colors = ['red' if e else 'blue' for e in exceeds]
    ax1.scatter(velocities, fidelities, c=colors, s=100, zorder=5)
    ax1.plot(velocities, fidelities, 'b--', alpha=0.5, zorder=1)
    ax1.axvline(x=0.55, color='red', linestyle=':', linewidth=2, 
                label='Critical Limit (0.55 µm/µs)')
    ax1.set_xlabel('Transport Velocity (µm/µs)')
    ax1.set_ylabel('Gate Fidelity')
    ax1.set_title('(a) Velocity-Fidelity Trade-off')
    ax1.legend()
    ax1.set_ylim(0.99, 1.001)
    
    # Right: Heating vs Velocity
    ax2.bar(velocities, nvib, width=0.03, color=colors, edgecolor='black')
    ax2.axhline(y=18, color='red', linestyle=':', linewidth=2,
                label='Critical n_vib = 18')
    ax2.axhline(y=10, color='orange', linestyle=':', linewidth=2,
                label='Warning n_vib = 10')
    ax2.set_xlabel('Transport Velocity (µm/µs)')
    ax2.set_ylabel('Δn_vib (vibrational heating)')
    ax2.set_title('(b) Heating vs Velocity')
    ax2.legend()
    
    plt.tight_layout()
    output_path = output_dir / "fig1_velocity_fidelity.pdf"
    plt.savefig(output_path)
    plt.savefig(output_dir / "fig1_velocity_fidelity.png")
    print(f"✅ Saved {output_path}")
    plt.close()


# =============================================================================
# FIGURE 2: DEPTH COMPARISON
# =============================================================================

def plot_depth_comparison(results_dir: Path, output_dir: Path):
    """Plot Experiment B: Flying Ancillas vs SWAP."""
    json_path = results_dir / "experiment_b_ancilla_vs_swap.json"
    
    if not json_path.exists():
        print(f"⚠️ {json_path} not found. Run experiment B first.")
        return
    
    with open(json_path) as f:
        data = json.load(f)
    
    results = data['results']
    
    # Group by circuit type
    circuits = sorted(set(r['circuit'] for r in results))
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for idx, circuit in enumerate(circuits):
        ax = axes[idx]
        subset = [r for r in results if r['circuit'] == circuit]
        
        qubits = [r['num_qubits'] for r in subset]
        swap_depth = [r['swap_depth'] for r in subset]
        ancilla_depth = [r['ancilla_depth'] for r in subset]
        
        x = np.arange(len(qubits))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, swap_depth, width, label='SWAP', color='#ff7f0e')
        bars2 = ax.bar(x + width/2, ancilla_depth, width, label='Flying Ancilla', color='#1f77b4')
        
        ax.set_xlabel('Number of Qubits')
        ax.set_ylabel('Circuit Depth')
        ax.set_title(f'{circuit} Circuit')
        ax.set_xticks(x)
        ax.set_xticklabels(qubits)
        ax.legend()
        ax.set_yscale('log')
        
        # Add speedup annotations
        for i, (s, a) in enumerate(zip(swap_depth, ancilla_depth)):
            speedup = s / a
            ax.annotate(f'{speedup:.1f}×', 
                       xy=(i, a), 
                       xytext=(0, 5),
                       textcoords='offset points',
                       ha='center', 
                       fontsize=9,
                       color='green',
                       fontweight='bold')
    
    plt.tight_layout()
    output_path = output_dir / "fig2_depth_comparison.pdf"
    plt.savefig(output_path)
    plt.savefig(output_dir / "fig2_depth_comparison.png")
    print(f"✅ Saved {output_path}")
    plt.close()


# =============================================================================
# FIGURE 3: COOLING STRATEGIES
# =============================================================================

def plot_cooling_strategies(results_dir: Path, output_dir: Path):
    """Plot Experiment C: Cooling strategies comparison."""
    json_path = results_dir / "experiment_c_cooling_strategies.json"
    
    if not json_path.exists():
        print(f"⚠️ {json_path} not found. Run experiment C first.")
        return
    
    with open(json_path) as f:
        data = json.load(f)
    
    results = data['results']
    
    strategies = ['GREEDY', 'CONSERVATIVE', 'ADAPTIVE']
    colors = {'GREEDY': '#d62728', 'CONSERVATIVE': '#2ca02c', 'ADAPTIVE': '#9467bd'}
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Left: Fidelity vs Circuit Depth
    for strategy in strategies:
        subset = [r for r in results if r['strategy'] == strategy]
        layers = [r['num_layers'] for r in subset]
        fidelity = [r['final_fidelity'] for r in subset]
        ax1.plot(layers, fidelity, 'o-', label=strategy, color=colors[strategy], 
                linewidth=2, markersize=8)
    
    ax1.axhline(y=0.9, color='gray', linestyle=':', label='90% Threshold')
    ax1.set_xlabel('Circuit Layers')
    ax1.set_ylabel('Final Fidelity')
    ax1.set_title('(a) Fidelity vs Circuit Depth')
    ax1.legend()
    ax1.set_ylim(0.5, 1.05)
    
    # Right: n_vib accumulation
    for strategy in strategies:
        subset = [r for r in results if r['strategy'] == strategy]
        layers = [r['num_layers'] for r in subset]
        nvib = [r['total_nvib'] for r in subset]
        ax2.plot(layers, nvib, 's--', label=strategy, color=colors[strategy],
                linewidth=2, markersize=8)
    
    ax2.axhline(y=18, color='red', linestyle=':', label='Critical n_vib')
    ax2.set_xlabel('Circuit Layers')
    ax2.set_ylabel('Total n_vib Accumulated')
    ax2.set_title('(b) Heating Accumulation')
    ax2.legend()
    
    plt.tight_layout()
    output_path = output_dir / "fig3_cooling_strategies.pdf"
    plt.savefig(output_path)
    plt.savefig(output_dir / "fig3_cooling_strategies.png")
    print(f"✅ Saved {output_path}")
    plt.close()


# =============================================================================
# FIGURE 4: ZONED ARCHITECTURE
# =============================================================================

def plot_zoned_lifetime(results_dir: Path, output_dir: Path):
    """Plot Experiment D: Qubit lifetime in zoned architecture."""
    json_path = results_dir / "experiment_d_zoned_cycles.json"
    
    if not json_path.exists():
        print(f"⚠️ {json_path} not found. Run experiment D first.")
        return
    
    with open(json_path) as f:
        data = json.load(f)
    
    results = data['results']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Left: Cycles vs Code Distance for different velocities
    velocities = sorted(set(r['velocity'] for r in results))
    colors = plt.cm.viridis(np.linspace(0, 0.8, len(velocities)))
    
    for v, color in zip(velocities, colors):
        subset = [r for r in results if r['velocity'] == v]
        distances = [r['code_distance'] for r in subset]
        cycles = [r['cycles_until_replacement'] for r in subset]
        ax1.plot(distances, cycles, 'o-', label=f'v={v} µm/µs', 
                color=color, linewidth=2, markersize=8)
    
    ax1.set_xlabel('Surface Code Distance (d)')
    ax1.set_ylabel('Cycles Until Replacement')
    ax1.set_title('(a) Qubit Lifetime vs Code Distance')
    ax1.legend()
    
    # Right: Lifetime (ms) heatmap-style
    code_distances = sorted(set(r['code_distance'] for r in results))
    
    width = 0.15
    x = np.arange(len(code_distances))
    
    for i, v in enumerate(velocities):
        subset = [r for r in results if r['velocity'] == v]
        times = [r['time_to_replacement_ms'] for r in subset]
        ax2.bar(x + i*width, times, width, label=f'v={v}', color=colors[i])
    
    ax2.set_xlabel('Surface Code Distance (d)')
    ax2.set_ylabel('Time to Replacement (ms)')
    ax2.set_title('(b) Qubit Lifetime Duration')
    ax2.set_xticks(x + width * 1.5)
    ax2.set_xticklabels(code_distances)
    ax2.legend()
    
    plt.tight_layout()
    output_path = output_dir / "fig4_zoned_lifetime.pdf"
    plt.savefig(output_path)
    plt.savefig(output_dir / "fig4_zoned_lifetime.png")
    print(f"✅ Saved {output_path}")
    plt.close()


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Generate all figures."""
    if not HAS_MATPLOTLIB:
        print("❌ Cannot generate figures without matplotlib")
        sys.exit(1)
    
    results_dir = Path("./benchmark_results")
    output_dir = results_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("GENERATING PUBLICATION FIGURES")
    print("="*60)
    
    setup_style()
    
    plot_velocity_fidelity(results_dir, output_dir)
    plot_depth_comparison(results_dir, output_dir)
    plot_cooling_strategies(results_dir, output_dir)
    plot_zoned_lifetime(results_dir, output_dir)
    
    print("\n" + "="*60)
    print(f"All figures saved to: {output_dir.absolute()}")
    print("="*60)


if __name__ == "__main__":
    main()

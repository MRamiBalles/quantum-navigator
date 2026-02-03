# Quantum Navigator - Benchmark Suite

Publication-ready benchmark experiments for validating the HeatingModel, Flying Ancilla compilation, and Zoned Architecture.

## Quick Start

```bash
cd d:\quantum-navigator\backend\benchmarks

# Run all experiments
python run_all_benchmarks.py

# Or run individually
python benchmark_velocity_fidelity.py     # Experiment A
python benchmark_ancilla_vs_swap.py       # Experiment B
python benchmark_cooling_strategies.py    # Experiment C
python benchmark_zoned_cycles.py          # Experiment D

# Generate figures (requires matplotlib)
pip install matplotlib seaborn
python plot_results.py
```

## Experiments

| ID | Name | Output |
|----|------|--------|
| A | Velocity vs Fidelity | `experiment_a_velocity_fidelity.csv` |
| B | Flying Ancillas vs SWAP | `experiment_b_ancilla_vs_swap.csv` |
| C | Cooling Strategies | `experiment_c_cooling_strategies.csv` |
| D | Zoned Architecture | `experiment_d_zoned_cycles.csv` |

## Output Structure

```
benchmark_results/
├── experiment_a_velocity_fidelity.csv
├── experiment_a_velocity_fidelity.json
├── experiment_b_ancilla_vs_swap.csv
├── experiment_b_ancilla_vs_swap.json
├── experiment_c_cooling_strategies.csv
├── experiment_c_cooling_strategies.json
├── experiment_d_zoned_cycles.csv
├── experiment_d_zoned_cycles.json
├── summary_report.md
└── figures/
    ├── fig1_velocity_fidelity.pdf
    ├── fig2_depth_comparison.pdf
    ├── fig3_cooling_strategies.pdf
    └── fig4_zoned_lifetime.pdf
```

## Key Findings

### Experiment A: Velocity-Fidelity
- **Critical velocity**: 0.55 µm/µs (Harvard 2025)
- **Fidelity degradation**: ~0.8% per unit n_vib

### Experiment B: Flying Ancillas
- **QFT depth reduction**: Up to 24×
- **QAOA depth reduction**: ~5×

### Experiment C: Cooling Strategies
- **Crossover point**: ~50 layers
- **Conservative wins**: For deep circuits

### Experiment D: Zoned Architecture
- **Best lifetime**: 956 cycles at v=0.20 µm/µs, d=9
- **Slower is better**: 3× more cycles at 0.20 vs 0.50 µm/µs

## LaTeX Paper

The complete paper is at: `docs/paper/quantum_navigator_paper.tex`

Compile with:
```bash
pdflatex quantum_navigator_paper.tex
bibtex quantum_navigator_paper
pdflatex quantum_navigator_paper.tex
pdflatex quantum_navigator_paper.tex
```

## References

1. Bluvstein et al. (2025) - Continuous-operation quantum computer
2. Tan et al. (2024) - FPQA-C Compilation Framework  
3. Silverio et al. (2022) - Pulser open-source package

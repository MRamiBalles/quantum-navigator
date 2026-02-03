"""
Benchmark: QRAM vs Angle Encoding Cost Analysis
==============================================
Simulates the hardware overhead of data loading for Quantum Machine Learning (QML).
Compares:
1. Angle Encoding (Deep circuits, O(N) gates)
2. Amplitude Encoding via Bucket Brigade QRAM (Shallow circuits, O(N) hardware cost, O(log N) depth)

Based on:
- "Limitations of Amplitude Encoding on Quantum Classification" (Wang et al., 2025)
- "Bucket Brigade QRAM" architecture (Gioannini et al.)
"""

import math
import json
import os
import sys

def calculate_qram_cost(dataset_size_n: int):
    """
    Calculates resources for Bucket Brigade QRAM.
    """
    # Address qubits: log2(N)
    qubits_address = math.ceil(math.log2(dataset_size_n))
    
    # Bus qubits (for signal routing)
    qubits_bus = 1
    
    # QRAM Hardware Nodes (Physical Qubits / Transmons / Atomic Arrays)
    # A full binary tree has 2^k - 1 nodes.
    # For Bucket Brigade, we need switches at each node.
    # Cost ~ O(N) physical resources
    physical_resources_qram = dataset_size_n - 1 + qubits_address
    
    # Depth for loading: O(log N) active switches per access
    depth_load = qubits_address * 2 # Forward and backward path
    
    return {
        "qubits_logical": qubits_address + 1, # Address + Target
        "physical_components": physical_resources_qram,
        "circuit_depth_per_access": depth_load,
        "fidelity_load": 0.999 ** depth_load # Heuristic 2-qubit gate fidelity
    }

def calculate_angle_encoding_cost(dataset_size_n: int):
    """
    Calculates resources for Angle Encoding (Rotation per feature).
    """
    # Simply N rotations. If serial: Depth N. If parallel: Width N.
    # Usually standard angle encoding puts N features into N qubits (width) or 1 qubit (depth N).
    # Dense Angle Encoding: N features into N qubits. Depth 1 (parallel).
    # Disadvantage: Uses N logic qubits.
    
    qubits_logical = dataset_size_n
    circuit_depth = 1 # R_y(x_i) on each qubit
    
    return {
        "qubits_logical": qubits_logical,
        "physical_components": dataset_size_n, # 1:1 mapping
        "circuit_depth_per_access": circuit_depth,
        "fidelity_load": 0.999 # Single qubit gate is high fidelity
    }

def run_benchmark():
    # Dataset sizes: MNIST (784), CIFAR (1024 / 3072), LLM-Embed (4096)
    sizes = [16, 64, 256, 784, 1024, 4096]
    results = []
    
    for n in sizes:
        qram = calculate_qram_cost(n)
        angle = calculate_angle_encoding_cost(n)
        
        # Arbitrary "Economic Cost" metric
        # Cost = (Logical Qubits * 1000) + (Physical Components * 10) + (Depth * 5)
        cost_qram = (qram["qubits_logical"] * 1000) + (qram["physical_components"] * 10) + (qram["circuit_depth_per_access"] * 5)
        cost_angle = (angle["qubits_logical"] * 1000) + (angle["physical_components"] * 10) + (angle["circuit_depth_per_access"] * 5)
        
        results.append({
            "dataset_size": n,
            "qram": qram,
            "angle": angle,
            "economic_cost_qram": cost_qram,
            "economic_cost_angle": cost_angle,
            "ratio_cost": round(cost_angle / cost_qram, 2)
        })
        
    return results

if __name__ == "__main__":
    data = run_benchmark()
    
    # Save results
    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "benchmark_results")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, "experiment_qram_loading.json"), 'w') as f:
        json.dump(data, f, indent=4)
        
    print(json.dumps(data, indent=2))

"""
Benchmark: Cryptographic Resilience (Shor vs PQC)
================================================
Estimates logical qubit requirements and time-to-break for classical vs post-quantum primitives.
Based on:
- NIST FIPS 203/204 (ML-KEM, ML-DSA)
- "Harvest Now, Decrypt Later" threat model
"""

import math

def estimate_shor_resources(key_size_bits: int, algorithm: str = "RSA"):
    """
    Estimates resources to break classical crypto using Shor's Algorithm.
    Ref: Gidney & Ekera "How to factor 2048 bit RSA integers in 8 hours using 20 million noisy qubits"
    """
    if algorithm == "RSA":
        # Beauregard's implementation: 2n + 2 logical qubits
        logical_qubits = 2 * key_size_bits + 2
        # T-depth approx: 40 * n^3 (naive) or optimized O(n^2 log n)
        # Using sophisticated valid estimation from Gidney:
        # To break RSA-2048 in ~8 hours requires ~20M physical qubits (surface code d~27)
        # We simplify to: Logical Qubits required.
        
        return {
            "target": f"RSA-{key_size_bits}",
            "logical_qubits_needed": logical_qubits,
            "physical_qubits_estimation": logical_qubits * 1000, # d=30 surface code overhead
            "vulnerable": True,
            "estimated_break_time_hours": 8 # With 20M qubits
        }
    elif algorithm == "ECC":
        # Proos and Zalka: ~9n + O(1) logical qubits for ECDLP
        logical_qubits = 9 * key_size_bits
        return {
            "target": f"ECC-{key_size_bits}",
            "logical_qubits_needed": logical_qubits,
            "physical_qubits_estimation": logical_qubits * 1000,
            "vulnerable": True,
            "estimated_break_time_hours": 2 # Smaller key size than RSA
        }

def estimate_pqc_resilience(algorithm: str, security_level: int):
    """
    Estimates resistance of PQC algorithms (Lattice-based).
    Shor's algorithm does NOT apply. Grover's gives only quadratic speedup.
    """
    # NIST Security Levels:
    # Level 1: AES-128
    # Level 3: AES-192
    # Level 5: AES-256
    
    if "ML-KEM" in algorithm or "Kyber" in algorithm:
        # Module-Lattice Key Encapsulation
        # Best known attack: Dual lattice attack
        return {
            "target": f"{algorithm} (Level {security_level})",
            "logical_qubits_needed": "N/A (Shor Immune)",
            "physical_qubits_estimation": "> 10^30", # Infeasible
            "vulnerable": False,
            "estimated_break_time_hours": "Billions of Years"
        }
    
    return {}

def run_crypto_benchmark():
    scenarios = [
        estimate_shor_resources(2048, "RSA"),
        estimate_shor_resources(256, "ECC"),
        estimate_pqc_resilience("ML-KEM", 3), # Kyber-768
        estimate_shor_resources(4096, "RSA")
    ]
    return scenarios

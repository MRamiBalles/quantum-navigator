"""
Benchmark: Cryptographic Resilience (Shor vs PQC)
================================================
Estimates logical qubit requirements and time-to-break for classical vs post-quantum primitives.
Includes Hardware Roadmap Projections (IBM, QuEra, Google).

Based on:
- NIST FIPS 203/204 (ML-KEM, ML-DSA)
- "Harvest Now, Decrypt Later" threat model
- Gidney & Ekerå (2021): "How to factor 2048 bit RSA integers..."
"""

import math

def estimate_qubit_capacity_by_year(year: int) -> int:
    """
    Returns projected LOGICAL qubits based on major vendor roadmaps.
    Aggregated from IBM (Starling/Blue Jay), QuEra, Google, PsiQuantum.
    """
    # Conservative/Realistic Projections
    roadmap = {
        2025: 10,     # Experimental logical qubits (Harvard/AWS)
        2026: 40,     # IBM 'Starling' (Logical memory)
        2027: 100,    # Fault-tolerant prototypes
        2028: 200,    # IBM 'Blue Jay'
        2029: 500,    # Scaling phase
        2030: 1000,   # Industrial utility
        2032: 2000,
        2033: 4000,   # Breaking RSA-2048 becomes plausible
        2035: 10000   # Full FTQC
    }
    
    # Linear interpolation or nearest neighbor
    if year in roadmap:
        return roadmap[year]
    
    # Fallback/Extrapolation
    if year < 2025: return 0
    if year > 2035: return 20000
    
    # Simple closer neighbor
    closest_year = min(roadmap.keys(), key=lambda x: abs(x-year))
    return roadmap[closest_year]

def estimate_shor_resources(key_size_bits: int, algorithm: str = "RSA", current_year_capacity: int = 0):
    """
    Estimates resources to break classical crypto using Shor's Algorithm.
    Ref: Gidney & Ekera "How to factor 2048 bit RSA integers in 8 hours using 20 million noisy qubits"
    """
    if algorithm == "RSA":
        # Beauregard's implementation: 2n + 2 logical qubits
        logical_qubits_needed = 2 * key_size_bits + 2
        
        # Risk assessment
        risk_level = "SAFE"
        if current_year_capacity >= logical_qubits_needed:
            risk_level = "BROKEN"
        elif current_year_capacity >= logical_qubits_needed * 0.1:
            risk_level = "CRITICAL" # Approaching risk
        
        return {
            "target": f"RSA-{key_size_bits}",
            "logical_qubits_needed": logical_qubits_needed,
            "physical_qubits_estimation": logical_qubits_needed * 1000, # d=30 surface code overhead
            "vulnerable": True,
            "projected_capacity": current_year_capacity,
            "risk_status": risk_level,
            "estimated_break_time_hours": 8 if risk_level == "BROKEN" else "Infinite"
        }
    elif algorithm == "ECC":
        # Proos and Zalka: ~9n + O(1) logical qubits for ECDLP
        logical_qubits_needed = 9 * key_size_bits
        
        risk_level = "SAFE"
        if current_year_capacity >= logical_qubits_needed:
            risk_level = "BROKEN"
        
        return {
            "target": f"ECC-{key_size_bits}",
            "logical_qubits_needed": logical_qubits_needed,
            "physical_qubits_estimation": logical_qubits_needed * 1000,
            "vulnerable": True,
            "projected_capacity": current_year_capacity,
            "risk_status": risk_level,
            "estimated_break_time_hours": 2 if risk_level == "BROKEN" else "Infinite"
        }

def estimate_pqc_resilience(algorithm: str, security_level: int):
    """
    Estimates resistance of PQC algorithms (Lattice-based).
    Shor's algorithm does NOT apply. Grover's gives only quadratic speedup.
    """
    if "ML-KEM" in algorithm or "Kyber" in algorithm:
        return {
            "target": f"{algorithm} (Level {security_level})",
            "logical_qubits_needed": "N/A (Shor Immune)",
            "physical_qubits_estimation": "> 10^30", # Infeasible
            "vulnerable": False,
            "risk_status": "SECURE",
            "estimated_break_time_hours": "Billions of Years"
        }
    
    return {}

def run_crypto_benchmark(target_year: int = 2026):
    capacity = estimate_qubit_capacity_by_year(target_year)
    
    scenarios = [
        estimate_shor_resources(2048, "RSA", capacity),
        estimate_shor_resources(256, "ECC", capacity),
        estimate_pqc_resilience("ML-KEM", 3), # Kyber-768
        estimate_shor_resources(4096, "RSA", capacity)
    ]
    return scenarios

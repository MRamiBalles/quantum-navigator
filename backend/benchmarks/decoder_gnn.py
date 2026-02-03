import math
import random
from typing import Dict, Any, List

class GNNDecoderSimulator:
    """
    Simulador de Decodificador Neuronal basado en Grafos (GNN).
    Compara el rendimiento de inferencia de GNN vs MWPM (Minimum Weight Perfect Matching).
    Basado en arquitecturas de inferencia de baja latencia para códigos qLDPC.
    """
    
    def __init__(self):
        # Parámetros de Hardware Neural (FPGA/ASIC) para inferencia GNN
        self.INFERENCE_TIME_PER_LAYER = 50e-9  # 50ns por capa de Message Passing (MPNN)
        self.COMMUNICATION_LATENCY = 20e-9     # Latencia de interconexión/Io
        self.LAYERS = 8                        # Profundidad típica para Surface Codes d=7
        
        # Parámetros MWPM (CPU/Classical)
        self.MWPM_BASE_TIME = 200e-9           # Overhead base
        self.MWPM_SCALING_FACTOR = 150e-9      # Factor de escalado por error
        
    def simulate_metric(self, num_qubits: int, error_rate: float) -> Dict[str, Any]:
        """
        Simula un ciclo de decodificación y calcula latencias.
        
        Args:
            num_qubits: Tamaño del sistema.
            error_rate: Probabilidad de error físico (p).
        """
        if num_qubits <= 0:
            return {}

        # 1. GNN Inference Time (Deterministic / Constant Reliability)
        # El tiempo de inferencia de GNN es O(1) paralelizable (depende de capas, no de N o errores)
        # Esto es cierto si tenemos hardware dedicado para cada nodo/vecindario.
        gnn_time = (self.INFERENCE_TIME_PER_LAYER * self.LAYERS) + self.COMMUNICATION_LATENCY
        
        # 2. MWPM Latency (Heuristic Approximation)
        # Edmonds' Blossom algorithm scales approx O(E^2 log E) or O(N^3) in worst case.
        # Pero en QEC, depende fuertemente de la cantidad de síndromes (detecciones de error).
        # Num Syndromes ~ num_qubits * error_rate
        num_syndromes = max(1, int(num_qubits * error_rate))
        
        # Modelo simplificado: T ~ Base + Factor * Syndromes^2
        mwpm_time = self.MWPM_BASE_TIME + (self.MWPM_SCALING_FACTOR * (num_syndromes ** 1.5))
        
        # Add slight jitter/variance
        mwpm_time *= random.uniform(0.9, 1.1)
        
        return {
            "system_size_qubits": num_qubits,
            "error_rate_p": error_rate,
            "gnn_latency_ns": round(gnn_time * 1e9, 2),
            "mwpm_latency_ns": round(mwpm_time * 1e9, 2),
            "advantage_ratio": round(mwpm_time / gnn_time, 2),
            "is_gnn_faster": gnn_time < mwpm_time
        }

def run_decoder_benchmark() -> List[Dict[str, Any]]:
    """
    Ejecuta un barrido de tasa de error para comparar decodificadores.
    """
    sim = GNNDecoderSimulator()
    results = []
    
    # Sistema fijo (e.g., 1000 qubits para un código Surface d=7 grande o qLDPC medio)
    qubits = 1000
    
    # Barrido de tasa de error física p de 0.001 (0.1%) a 0.02 (2%)
    error_rates = [0.001, 0.002, 0.005, 0.008, 0.01, 0.015, 0.02]
    
    for p in error_rates:
        metrics = sim.simulate_metric(qubits, p)
        results.append(metrics)
        
    return results

if __name__ == "__main__":
    import json
    print(json.dumps(run_decoder_benchmark(), indent=2))

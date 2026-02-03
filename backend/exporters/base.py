from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseExporter(ABC):
    """Base class for all Quantum Orchestration Middleware exporters."""
    
    @abstractmethod
    def export(self, data: Dict[str, Any]) -> str:
        """
        Export internal middleware representation to a target language/format.
        
        Args:
            data: Dictionary containing circuit/layout/pulse information.
            
        Returns:
            A string representing the output (e.g., Julia code, QASM script).
        """
        pass

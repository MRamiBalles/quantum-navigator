"""
Quantum Navigator Backend API - v4.0
=====================================
FastAPI server with WebSocket support for real-time benchmark telemetry.

MIT License (c) 2026 Harvard/MIT Quantum Computing Research
"""

import os
import subprocess
import json
import asyncio
import logging
import random
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Quantum Navigator Backend API", version="4.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PYTHON_EXE = r"C:\Users\Manu\AppData\Local\Programs\Python\Python312\python.exe"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BENCHMARKS_DIR = os.path.join(BASE_DIR, "benchmarks")
FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")

# ============================================================================
# Data Models
# ============================================================================

class RunBenchmarkRequest(BaseModel):
    benchmark_type: str

class ComparisonConfig(BaseModel):
    id: Optional[str] = None
    name: str
    benchmark: str
    circuits: List[str]
    strategies: List[str]
    chartType: str

class TelemetryPayload(BaseModel):
    """
    Physics-based telemetry for real-time benchmark monitoring.
    Based on Harvard/QuEra 2025 continuous operation architecture.
    """
    status: str  # CONNECTING, RUNNING, COMPLETED, ERROR
    percentage: float
    cycle: int
    atoms_lost: int
    n_vib: float  # Vibrational quantum number (heating indicator)
    fidelity: float
    decoder_backlog_ms: float
    timestamp: str

# ============================================================================
# WebSocket Manager
# ============================================================================

class BenchmarkConnectionManager:
    """Manages active WebSocket connections for benchmark telemetry."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.running_benchmarks: Dict[str, bool] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.running_benchmarks[client_id] = True
        logger.info(f"WebSocket connected: {client_id}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.running_benchmarks:
            del self.running_benchmarks[client_id]
        logger.info(f"WebSocket disconnected: {client_id}")
    
    async def send_telemetry(self, client_id: str, telemetry: TelemetryPayload):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(telemetry.model_dump())
    
    def stop_benchmark(self, client_id: str):
        if client_id in self.running_benchmarks:
            self.running_benchmarks[client_id] = False

manager = BenchmarkConnectionManager()

# ============================================================================
# Benchmark Simulation Engine (Physics-Based)
# ============================================================================

async def simulate_benchmark_execution(
    client_id: str,
    benchmark_type: str,
    total_cycles: int = 50
):
    """
    Simulates benchmark execution with physics-based telemetry.
    
    Based on Harvard/MIT 2025 FPQA continuous operation:
    - ~20ms per zone reordering cycle
    - Atom loss probability per cycle
    - Heating accumulation (n_vib)
    - Decoder latency simulation
    """
    
    # Physical parameters (from v4.0 schema)
    ZONE_REORDER_TIME_MS = 20.0  # Harvard 2025
    ATOM_LOSS_PROB_PER_CYCLE = 0.003  # 0.3% per cycle
    HEATING_RATE = 0.05  # n_vib increase per cycle
    COOLING_THRESHOLD = 1.5  # When to "cool"
    REPLENISHMENT_RATE = 30000  # atoms/second
    
    n_vib = 0.0
    total_atoms_lost = 0
    fidelity = 0.9999
    
    for cycle in range(1, total_cycles + 1):
        # Check if benchmark was stopped
        if not manager.running_benchmarks.get(client_id, False):
            await manager.send_telemetry(client_id, TelemetryPayload(
                status="STOPPED",
                percentage=100.0 * cycle / total_cycles,
                cycle=cycle,
                atoms_lost=total_atoms_lost,
                n_vib=n_vib,
                fidelity=fidelity,
                decoder_backlog_ms=0,
                timestamp=datetime.now().isoformat()
            ))
            return
        
        # Simulate zone reordering latency (~20ms)
        await asyncio.sleep(ZONE_REORDER_TIME_MS / 1000)
        
        # Physics: Atom loss
        atoms_lost_this_cycle = 1 if random.random() < ATOM_LOSS_PROB_PER_CYCLE else 0
        total_atoms_lost += atoms_lost_this_cycle
        
        # Physics: Heating accumulation
        n_vib += HEATING_RATE * (1 + random.uniform(-0.1, 0.1))
        
        # Physics: Cooling (if threshold exceeded)
        if n_vib > COOLING_THRESHOLD:
            n_vib = 0.1  # Reset after cooling
        
        # Physics: Fidelity decay
        fidelity *= (1 - 0.0001 * n_vib)
        
        # Simulate decoder backlog (random spikes)
        decoder_backlog = random.uniform(0.5, 2.0)
        if cycle % 15 == 0:  # Occasional spike
            decoder_backlog = random.uniform(5.0, 15.0)
        
        # Send telemetry
        telemetry = TelemetryPayload(
            status="RUNNING",
            percentage=100.0 * cycle / total_cycles,
            cycle=cycle,
            atoms_lost=total_atoms_lost,
            n_vib=round(n_vib, 3),
            fidelity=round(fidelity, 6),
            decoder_backlog_ms=round(decoder_backlog, 2),
            timestamp=datetime.now().isoformat()
        )
        
        await manager.send_telemetry(client_id, telemetry)
    
    # Final telemetry
    await manager.send_telemetry(client_id, TelemetryPayload(
        status="COMPLETED",
        percentage=100.0,
        cycle=total_cycles,
        atoms_lost=total_atoms_lost,
        n_vib=round(n_vib, 3),
        fidelity=round(fidelity, 6),
        decoder_backlog_ms=0,
        timestamp=datetime.now().isoformat()
    ))

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {"status": "online", "version": "4.0", "websocket": "/ws/benchmarks/{client_id}"}

@app.websocket("/ws/benchmarks/{client_id}")
async def websocket_benchmark(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time benchmark telemetry.
    
    Connect with: ws://localhost:8000/ws/benchmarks/<unique_client_id>
    
    The server will stream JSON telemetry payloads with:
    - status: CONNECTING, RUNNING, COMPLETED, STOPPED, ERROR
    - percentage: 0-100
    - cycle: Current QEC cycle number
    - atoms_lost: Cumulative atom loss count
    - n_vib: Vibrational quantum number (heating indicator)
    - fidelity: Current logical fidelity
    - decoder_backlog_ms: Decoder latency
    - timestamp: ISO timestamp
    """
    await manager.connect(client_id, websocket)
    
    try:
        # Wait for start command
        data = await websocket.receive_json()
        benchmark_type = data.get("benchmark_type", "velocity_fidelity")
        total_cycles = data.get("cycles", 50)
        
        # Send initial telemetry
        await manager.send_telemetry(client_id, TelemetryPayload(
            status="CONNECTING",
            percentage=0,
            cycle=0,
            atoms_lost=0,
            n_vib=0,
            fidelity=1.0,
            decoder_backlog_ms=0,
            timestamp=datetime.now().isoformat()
        ))
        
        # Run simulation in background
        await simulate_benchmark_execution(client_id, benchmark_type, total_cycles)
        
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {str(e)}")
        manager.disconnect(client_id)

@app.post("/ws/benchmarks/{client_id}/stop")
async def stop_benchmark(client_id: str):
    """Stop a running benchmark via HTTP POST."""
    manager.stop_benchmark(client_id)
    return {"status": "stop_requested", "client_id": client_id}

@app.post("/api/benchmarks/run")
async def run_benchmark(request: RunBenchmarkRequest):
    """
    Executes a benchmark script and returns the result.
    For real-time updates, use the WebSocket endpoint instead.
    """
    script_name = f"benchmark_{request.benchmark_type}.py"
    script_path = os.path.join(BENCHMARKS_DIR, script_name)
    
    if not os.path.exists(script_path):
        if request.benchmark_type == "full":
            script_path = os.path.join(BENCHMARKS_DIR, "run_all_benchmarks.py")
        else:
            raise HTTPException(status_code=404, detail=f"Benchmark script {script_name} not found")

    try:
        result_dir = os.path.join(BASE_DIR, "benchmark_results")
        
        logger.info(f"Running benchmark: {script_path}")
        process = subprocess.run(
            [PYTHON_EXE, script_path],
            capture_output=True,
            text=True,
            check=False,
            cwd=BASE_DIR
        )
        
        if process.returncode != 0:
            logger.error(f"Benchmark failed: {process.stderr}")
            
        json_file = os.path.join(result_dir, f"experiment_{request.benchmark_type[0]}_{request.benchmark_type}.json")
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                data = json.load(f)
            return data
        
        return {"status": "completed", "output": process.stdout}
        
    except Exception as e:
        logger.error(f"Error running benchmark: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/favorites/load")
async def load_favorites():
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading favorites: {str(e)}")
        return []

@app.post("/api/favorites/save")
async def save_favorite(config: ComparisonConfig):
    favorites = await load_favorites()
    
    if not config.id:
        config.id = str(uuid.uuid4())
        
    favorites.append(config.model_dump())
    
    try:
        with open(FAVORITES_FILE, 'w') as f:
            json.dump(favorites, f, indent=4)
        return {"status": "success", "id": config.id}
    except Exception as e:
        logger.error(f"Error saving favorite: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

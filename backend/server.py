"""
Quantum Navigator Backend API - v5.1 Industrial-Grade
======================================================
FastAPI server with WebSocket support for real-time benchmark telemetry.

MIT License (c) 2026 Harvard/MIT Quantum Computing Research

SECURITY NOTES:
- API_KEY must be set via QUANTUM_API_KEY environment variable (no hardcoded defaults)
- WebSocket authentication uses first-message token validation
- All inputs validated via whitelist and regex patterns
"""

import os
import sys
import re
import subprocess
import json
import asyncio
import logging
import random
import uuid
import secrets
from typing import List, Optional, Dict, Any, Set
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from optimizer import SpectralAODRouter
from benchmarks.benchmark_qram import run_benchmark as run_qram_benchmark
from benchmarks.benchmark_crypto import run_crypto_benchmark
from exporters.bloqade import BloqadeExporter
from exporters.openqasm3 import OpenQASM3Exporter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Quantum Navigator Backend API", version="5.1")

# ============================================================================
# Security Configuration
# ============================================================================

# API Key - MUST be set via environment variable in production
# No hardcoded fallbacks to prevent accidental key exposure in source code
API_KEY = os.getenv("QUANTUM_API_KEY")
IS_DEV_MODE = os.getenv("ENV", "development").lower() != "production"

def _validate_api_key_on_startup():
    """Validates API key is properly configured at startup."""
    global API_KEY
    if not API_KEY:
        if not IS_DEV_MODE:
            raise ValueError(
                "QUANTUM_API_KEY environment variable must be set in production. "
                "Use a secrets management service (AWS Secrets Manager, HashiCorp Vault, etc.)"
            )
        else:
            # Generate ephemeral key for dev mode only
            API_KEY = f"dev-{secrets.token_hex(16)}"
            logger.warning(
                "⚠️ QUANTUM_API_KEY not set. Running in INSECURE dev mode with ephemeral key. "
                "Set QUANTUM_API_KEY for production deployment."
            )
    else:
        logger.info("✓ API key configured from environment variable")

_validate_api_key_on_startup()

# Allowed origins - configure via environment variable for production
# Format: comma-separated list of origins
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:8080,http://localhost:3000,http://127.0.0.1:5173"
).split(",")

# Enable CORS with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-API-Key"],
)

# Use system Python interpreter instead of hardcoded path
PYTHON_EXE = os.getenv("PYTHON_EXE", sys.executable)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BENCHMARKS_DIR = os.path.join(BASE_DIR, "benchmarks")
FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")

# ============================================================================
# Input Validation - Whitelist of allowed benchmark types
# ============================================================================

ALLOWED_BENCHMARK_TYPES: Set[str] = {
    "velocity_fidelity",
    "ancilla_vs_swap",
    "cooling_strategies",
    "zoned_cycles",
    "sustainable_depth",
    "full"
}

# Regex pattern for valid benchmark type format (alphanumeric + underscore only)
BENCHMARK_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,49}$")

def validate_benchmark_type(benchmark_type: str) -> str:
    """
    Validates benchmark_type against whitelist and pattern to prevent injection attacks.
    
    Raises:
        ValueError: If benchmark_type is not in allowed list or contains invalid characters
    """
    if not benchmark_type:
        raise ValueError("Benchmark type cannot be empty")
    
    # Normalize and strip
    benchmark_type = benchmark_type.strip().lower()
    
    # Check against whitelist first (most secure)
    if benchmark_type not in ALLOWED_BENCHMARK_TYPES:
        raise ValueError(
            f"Invalid benchmark type '{benchmark_type}'. "
            f"Allowed types: {', '.join(sorted(ALLOWED_BENCHMARK_TYPES))}"
        )
    
    # Additional pattern validation (defense in depth)
    if not BENCHMARK_TYPE_PATTERN.match(benchmark_type):
        raise ValueError("Benchmark type contains invalid characters")
    
    return benchmark_type

def verify_api_key(provided_key: Optional[str]) -> bool:
    """Securely verifies API key using constant-time comparison."""
    if not API_KEY or not provided_key:
        # In dev mode without key, allow access (but log warning)
        if IS_DEV_MODE and not API_KEY:
            return True
        return False
    return secrets.compare_digest(provided_key, API_KEY)

# ============================================================================
# Data Models with Validation
# ============================================================================

class RunBenchmarkRequest(BaseModel):
    benchmark_type: str
    
    @field_validator('benchmark_type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        return validate_benchmark_type(v)

class ComparisonConfig(BaseModel):
    id: Optional[str] = None
    name: str
    benchmark: str
    circuits: List[str]
    strategies: List[str]
    chartType: str
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v) > 100:
            raise ValueError("Name must be 1-100 characters")
        # Only allow safe characters for name
        if not re.match(r'^[\w\s\-\.]+$', v):
            raise ValueError("Name contains invalid characters")
        return v.strip()
    
    @field_validator('benchmark')
    @classmethod
    def validate_benchmark(cls, v: str) -> str:
        return validate_benchmark_type(v)
    
    @field_validator('chartType')
    @classmethod
    def validate_chart_type(cls, v: str) -> str:
        allowed_charts = {"bar", "radar", "line", "pie"}
        if v.lower() not in allowed_charts:
            raise ValueError(f"Invalid chart type. Allowed: {allowed_charts}")
        return v.lower()

class TelemetryPayload(BaseModel):
    """
    Physics-based telemetry for real-time benchmark monitoring.
    Based on Harvard/QuEra 2025 continuous operation architecture.
    """
    status: str  # CONNECTING, RUNNING, COMPLETED, ERROR, AUTH_REQUIRED
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
        self.authenticated_clients: Set[str] = set()
    
    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connected (pending auth): {client_id}")
    
    def authenticate(self, client_id: str):
        self.authenticated_clients.add(client_id)
        self.running_benchmarks[client_id] = True
        logger.info(f"WebSocket authenticated: {client_id}")
    
    def is_authenticated(self, client_id: str) -> bool:
        return client_id in self.authenticated_clients
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.running_benchmarks:
            del self.running_benchmarks[client_id]
        self.authenticated_clients.discard(client_id)
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
    
    # Validate benchmark_type again (defense in depth)
    try:
        benchmark_type = validate_benchmark_type(benchmark_type)
    except ValueError as e:
        logger.error(f"Invalid benchmark type in simulation: {e}")
        return
    
    # Validate total_cycles
    total_cycles = max(1, min(total_cycles, 1000))  # Clamp to reasonable range
    
    # Physical parameters (from v4.0 schema)
    ZONE_REORDER_TIME_MS = 20.0  # Harvard 2025
    ATOM_LOSS_PROB_PER_CYCLE = 0.003  # 0.3% per cycle
    HEATING_RATE = 0.05  # n_vib increase per cycle
    COOLING_THRESHOLD = 1.5  # When to "cool"
    
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
        
        # Physics: Decoder Backlog (Queue Simulation)
        # Based on Riverlane LCD / Google Willow:
        # If Decoding Rate < Syndrome Generation Rate, the queue explodes (Death Point).
        
        # Initialize queue state
        if cycle == 1:
            syndrome_queue = 0.0
        
        # 1. Syndrome Generation (R_syn)
        # Assume 1 syndrome batch per cycle
        new_syndromes = 1.0 
        
        # 2. Decoding Capacity (R_dec)
        # Capacity drops exponentially with code distance 'd'
        d = 3
        if cycle > 15: d = 5 
        if cycle > 30: d = 7
        
        # Capacity equation: C = C0 * exp(-alpha * d)
        c0 = 10.0 
        alpha = 0.4
        decoding_capacity = c0 * math.exp(-alpha * d) * random.uniform(0.9, 1.1)
        
        # 3. Queue Update
        if 'syndrome_queue' not in locals(): 
            syndrome_queue = 0.0
            
        syndrome_queue += new_syndromes
        processed = min(syndrome_queue, decoding_capacity)
        syndrome_queue -= processed
        
        # 4. Convert Queue Size to Time Latency
        time_to_clear = (syndrome_queue / decoding_capacity) * ZONE_REORDER_TIME_MS
        
        if syndrome_queue < 0.01:
            latency = (1.0 / decoding_capacity) * ZONE_REORDER_TIME_MS
        else:
            latency = time_to_clear
            
        # Expose as 'decoder_backlog' for telemetry (unrounded, rounded later)
        decoder_backlog = latency
        decoder_backlog_ms = round(latency, 2)
        
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
    return {"status": "online", "version": "5.1", "websocket": "/ws/benchmarks/{client_id}"}

@app.websocket("/ws/benchmarks/{client_id}")
async def websocket_benchmark(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time benchmark telemetry with first-message authentication.
    
    Connection Protocol:
    1. Connect: ws://localhost:8000/ws/benchmarks/<unique_client_id>
    2. First message MUST be auth: {"type": "auth", "token": "<api_key>"}
    3. Then send benchmark command: {"benchmark_type": "...", "cycles": 50}
    
    The server will stream JSON telemetry payloads with:
    - status: AUTH_REQUIRED, CONNECTING, RUNNING, COMPLETED, STOPPED, ERROR
    - percentage: 0-100
    - cycle: Current QEC cycle number
    - atoms_lost: Cumulative atom loss count
    - n_vib: Vibrational quantum number (heating indicator)
    - fidelity: Current logical fidelity
    - decoder_backlog_ms: Decoder latency
    - timestamp: ISO timestamp
    """
    # Validate client_id format to prevent injection
    if not re.match(r'^[a-zA-Z0-9_\-]{1,64}$', client_id):
        await websocket.close(code=4000, reason="Invalid client ID format")
        return
    
    await manager.connect(client_id, websocket)
    
    try:
        # SECURITY: First message must be authentication
        # This is more secure than query parameters (not logged in URLs/proxies)
        auth_data = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
        
        if auth_data.get("type") != "auth":
            await manager.send_telemetry(client_id, TelemetryPayload(
                status="AUTH_REQUIRED",
                percentage=0,
                cycle=0,
                atoms_lost=0,
                n_vib=0,
                fidelity=0,
                decoder_backlog_ms=0,
                timestamp=datetime.now().isoformat()
            ))
            await websocket.close(code=4001, reason="First message must be auth")
            manager.disconnect(client_id)
            return
        
        provided_token = auth_data.get("token", "")
        if not verify_api_key(provided_token):
            logger.warning(f"WebSocket auth failed for client: {client_id}")
            await manager.send_telemetry(client_id, TelemetryPayload(
                status="ERROR",
                percentage=0,
                cycle=0,
                atoms_lost=0,
                n_vib=0,
                fidelity=0,
                decoder_backlog_ms=0,
                timestamp=datetime.now().isoformat()
            ))
            await websocket.close(code=4001, reason="Invalid API token")
            manager.disconnect(client_id)
            return
        
        # Mark client as authenticated
        manager.authenticate(client_id)
        
        # Wait for benchmark command
        data = await websocket.receive_json()
        
        # Validate benchmark_type from WebSocket message
        raw_benchmark_type = data.get("benchmark_type", "velocity_fidelity")
        try:
            benchmark_type = validate_benchmark_type(raw_benchmark_type)
        except ValueError as e:
            await manager.send_telemetry(client_id, TelemetryPayload(
                status="ERROR",
                percentage=0,
                cycle=0,
                atoms_lost=0,
                n_vib=0,
                fidelity=0,
                decoder_backlog_ms=0,
                timestamp=datetime.now().isoformat()
            ))
            logger.error(f"Invalid benchmark type from WebSocket: {e}")
            manager.disconnect(client_id)
            return
        
        # Validate cycles parameter
        total_cycles = data.get("cycles", 50)
        if not isinstance(total_cycles, int) or total_cycles < 1 or total_cycles > 1000:
            total_cycles = 50
        
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
        
    except asyncio.TimeoutError:
        logger.warning(f"WebSocket auth timeout for client: {client_id}")
        await websocket.close(code=4002, reason="Authentication timeout")
        manager.disconnect(client_id)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {str(e)}")
        manager.disconnect(client_id)

from fastapi import Header, Depends

async def verify_api_key_header(x_api_key: str = Header(None, alias="X-API-Key")):
    """
    Dependency that validates API key from request header.
    All protected endpoints should use this as a dependency.
    """
    if not verify_api_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key


@app.post("/ws/benchmarks/{client_id}/stop", dependencies=[Depends(verify_api_key_header)])
async def stop_benchmark(client_id: str):
    """Stop a running benchmark via HTTP POST."""
    # Validate client_id format
    if not re.match(r'^[a-zA-Z0-9_\-]{1,64}$', client_id):
        raise HTTPException(status_code=400, detail="Invalid client ID format")
    
    manager.stop_benchmark(client_id)
    return {"status": "stop_requested", "client_id": client_id}


@app.post("/api/benchmarks/run", dependencies=[Depends(verify_api_key_header)])
async def run_benchmark(request: RunBenchmarkRequest):
    """
    Executes a benchmark script and returns the result.
    For real-time updates, use the WebSocket endpoint instead.
    
    Note: benchmark_type is validated by Pydantic model before reaching this handler.
    """
    # benchmark_type is already validated by Pydantic validator
    benchmark_type = request.benchmark_type
    
    script_name = f"benchmark_{benchmark_type}.py"
    script_path = os.path.join(BENCHMARKS_DIR, script_name)
    
    # Verify the resolved path is within BENCHMARKS_DIR (prevent path traversal)
    resolved_path = os.path.realpath(script_path)
    benchmarks_real = os.path.realpath(BENCHMARKS_DIR)
    if not resolved_path.startswith(benchmarks_real):
        logger.error(f"Path traversal attempt detected: {script_path}")
        raise HTTPException(status_code=400, detail="Invalid benchmark type")
    
    if not os.path.exists(script_path):
        if benchmark_type == "full":
            script_path = os.path.join(BENCHMARKS_DIR, "run_all_benchmarks.py")
        else:
            raise HTTPException(status_code=404, detail=f"Benchmark script not found")

    try:
        result_dir = os.path.join(BASE_DIR, "benchmark_results")
        
        logger.info(f"Running benchmark: {script_path}")
        process = subprocess.run(
            [PYTHON_EXE, script_path],
            capture_output=True,
            text=True,
            check=False,
            cwd=BASE_DIR,
            timeout=300  # 5 minute timeout to prevent hanging
        )
        
        if process.returncode != 0:
            logger.error(f"Benchmark failed: {process.stderr}")
            
        json_file = os.path.join(result_dir, f"experiment_{benchmark_type[0]}_{benchmark_type}.json")
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                data = json.load(f)
            return data
        
        return {"status": "completed", "output": process.stdout}
        
    except subprocess.TimeoutExpired:
        logger.error("Benchmark execution timed out")
        raise HTTPException(status_code=504, detail="Benchmark execution timed out")
    except Exception as e:
        logger.error(f"Error running benchmark: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/favorites/load", dependencies=[Depends(verify_api_key_header)])
async def load_favorites():
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading favorites: {str(e)}")
        return []


@app.get("/api/benchmarks/crypto", dependencies=[Depends(verify_api_key_header)])
async def get_crypto_benchmarks(year: int = 2026):
    """
    Returns crypto resilience benchmark data.
    Uses 'year' parameter for hardware roadmap alignment.
    """
    try:
        return run_crypto_benchmark(target_year=year)
    except Exception as e:
        logger.error(f"Crypto benchmark failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/benchmarks/qram", dependencies=[Depends(verify_api_key_header)])
async def get_qram_benchmarks():
    """Returns QRAM vs Angle Encoding cost analysis data."""
    try:
        return run_qram_benchmark()
    except Exception as e:
        logger.error(f"QRAM benchmark failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class OptimizationRequest(BaseModel):
    num_qubits: int = 50
    num_gates: int = 200
    width: int = 20
    height: int = 20

@app.post("/api/topology/optimize", dependencies=[Depends(verify_api_key_header)])
async def optimize_topology(request: OptimizationRequest):
    """
    Runs the Spectral-AOD topological optimizer.
    Returns comparison of heating vs AOD complexity.
    """
    try:
        opt = SpectralAODRouter(request.width, request.height)
        graph = opt.generate_random_circuit_graph(request.num_qubits, request.num_gates)
        result = opt.optimize_mapping(graph)
        return result
    except Exception as e:
        logger.error(f"Optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/favorites/save", dependencies=[Depends(verify_api_key_header)])
async def save_favorite(config: ComparisonConfig):
    """Save a comparison configuration to favorites."""
    favorites = await load_favorites()
    
    # Limit total favorites to prevent DoS
    if len(favorites) >= 100:
        raise HTTPException(status_code=400, detail="Maximum favorites limit reached (100)")
    
    if not config.id:
        config.id = str(uuid.uuid4())
        
    favorites.append(config.model_dump())
    
    try:
        with open(FAVORITES_FILE, 'w') as f:
            json.dump(favorites, f, indent=4)
        return {"status": "success", "id": config.id}
    except Exception as e:
        logger.error(f"Error saving favorite: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save favorite")

# ============================================================================
# HPC-Bridge Export Endpoints
# ============================================================================

class ExportRequest(BaseModel):
    num_qubits: int = 50
    width: float = 20.0
    height: float = 20.0
    layout: Optional[List[Tuple[float, float]]] = None
    gates: Optional[List[Dict[str, Any]]] = None

@app.post("/api/export/bloqade", dependencies=[Depends(verify_api_key_header)])
async def export_bloqade(request: ExportRequest):
    """Export to QuEra Bloqade (Julia)."""
    try:
        exporter = BloqadeExporter()
        script = exporter.export(request.model_dump())
        return {"filename": "experiment.jl", "content": script}
    except Exception as e:
        logger.error(f"Bloqade export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/qasm3", dependencies=[Depends(verify_api_key_header)])
async def export_qasm3(request: ExportRequest):
    """Export to OpenQASM 3.0 (Universal)."""
    try:
        exporter = OpenQASM3Exporter()
        script = exporter.export(request.model_dump())
        return {"filename": "experiment.qasm", "content": script}
    except Exception as e:
        logger.error(f"QASM3 export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

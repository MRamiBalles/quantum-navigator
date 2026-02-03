"""
Quantum Navigator Backend API - v4.0
=====================================
FastAPI server with WebSocket support for real-time benchmark telemetry.
Includes API key authentication and rate limiting for security.

MIT License (c) 2026 Harvard/MIT Quantum Computing Research
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
import time
import secrets
import math
from typing import List, Optional, Dict, Any, Set
from datetime import datetime
from collections import defaultdict

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_429_TOO_MANY_REQUESTS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Quantum Navigator Backend API", version="4.0")

# ============================================================================
# Security Configuration
# ============================================================================

# API Key Authentication
API_KEY_NAME = "X-API-Key"
API_KEY = os.getenv("QUANTUM_API_KEY", "quantum-dev-key-2026")  # Change in production!
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: Optional[str] = Depends(api_key_header)) -> str:
    """Verify API key from header. Raises 401 if invalid."""
    if not api_key or not secrets.compare_digest(api_key, API_KEY):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": API_KEY_NAME}
        )
    return api_key

# ============================================================================
# Rate Limiting (In-Memory)
# ============================================================================

class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_allowed(self, client_id: str, limit: int, window_seconds: int) -> bool:
        """Check if request is allowed for client within rate limit window."""
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old requests
        self.requests[client_id] = [
            ts for ts in self.requests[client_id] if ts > window_start
        ]
        
        # Check limit
        if len(self.requests[client_id]) >= limit:
            return False
        
        # Record this request
        self.requests[client_id].append(now)
        return True
    
    def get_retry_after(self, client_id: str, window_seconds: int) -> int:
        """Get seconds until oldest request expires from window."""
        if not self.requests[client_id]:
            return 0
        oldest = min(self.requests[client_id])
        return max(0, int(window_seconds - (time.time() - oldest)))

rate_limiter = RateLimiter()

# Rate limit configurations
RATE_LIMITS = {
    "benchmarks": {"limit": 5, "window": 60},      # 5 requests per minute
    "favorites": {"limit": 30, "window": 60},      # 30 requests per minute
    "websocket": {"limit": 10, "window": 60},      # 10 connections per minute
}

def get_client_ip(request: Request) -> str:
    """Extract client IP from request (supports proxies)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

async def check_rate_limit(request: Request, limit_type: str):
    """Check rate limit and raise 429 if exceeded."""
    client_ip = get_client_ip(request)
    config = RATE_LIMITS.get(limit_type, {"limit": 60, "window": 60})
    
    if not rate_limiter.is_allowed(f"{limit_type}:{client_ip}", config["limit"], config["window"]):
        retry_after = rate_limiter.get_retry_after(f"{limit_type}:{client_ip}", config["window"])
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

# ============================================================================
# CORS Configuration
# ============================================================================

# Allowed origins - configure via environment variable for production
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
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", API_KEY_NAME],
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
        
        # Physics: Decoder Backlog (Riverlane LCD / Google Willow model)
        # Latency T_dec = k * exp(alpha * d)
        # We vary 'd' (code distance) to simulate complexity spikes
        
        # Base code distance (e.g., d=3, 5, 7) dynamic simulation
        d = 3
        if cycle > 15: d = 5 
        if cycle > 30: d = 7
        
        # Constants from Ziad 2025 (scaled for simulation)
        k = 0.05  # Base processing time in ms
        alpha = 0.8 # Exponential scaling factor
        
        # Add stochastic noise + exponential term
        decoding_latency = k * math.exp(alpha * d) * random.uniform(0.9, 1.1)
        
        # In this simulation, we report the instantaneous latency to see the "Death Point"
        # The frontend will flag if decoding_latency > ZONE_REORDER_TIME_MS (20ms)
        decoder_backlog_ms = round(decoding_latency, 2)
        
        # Send telemetry
        telemetry = TelemetryPayload(
            status="RUNNING",
            percentage=100.0 * cycle / total_cycles,
            cycle=cycle,
            atoms_lost=total_atoms_lost,
            n_vib=round(n_vib, 3),
            fidelity=round(fidelity, 6),
            decoder_backlog_ms=decoder_backlog_ms,
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
async def websocket_benchmark(websocket: WebSocket, client_id: str, token: Optional[str] = Query(None)):
    """
    WebSocket endpoint for real-time benchmark telemetry.
    
    Connect with: ws://localhost:8000/ws/benchmarks/<unique_client_id>?token=<API_KEY>
    
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
    # Validate token for WebSocket authentication
    if not token or not secrets.compare_digest(token, API_KEY):
        await websocket.close(code=4001, reason="Invalid or missing API token")
        logger.warning(f"WebSocket auth failed for client: {client_id}")
        return
    
    # Validate client_id format to prevent injection
    if not re.match(r'^[a-zA-Z0-9_\-]{1,64}$', client_id):
        await websocket.close(code=4000, reason="Invalid client ID format")
        return
    
    # Rate limit WebSocket connections
    client_key = f"websocket:{websocket.client.host if websocket.client else 'unknown'}"
    config = RATE_LIMITS["websocket"]
    if not rate_limiter.is_allowed(client_key, config["limit"], config["window"]):
        await websocket.close(code=4029, reason="Rate limit exceeded")
        logger.warning(f"WebSocket rate limit exceeded for: {client_key}")
        return
    
    await manager.connect(client_id, websocket)
    
    try:
        # Wait for start command
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
        
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {str(e)}")
        manager.disconnect(client_id)

@app.post("/ws/benchmarks/{client_id}/stop")
async def stop_benchmark(
    client_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Stop a running benchmark via HTTP POST."""
    # Validate client_id format
    if not re.match(r'^[a-zA-Z0-9_\-]{1,64}$', client_id):
        raise HTTPException(status_code=400, detail="Invalid client ID format")
    
    manager.stop_benchmark(client_id)
    return {"status": "stop_requested", "client_id": client_id}

@app.post("/api/benchmarks/run")
async def run_benchmark(
    request: RunBenchmarkRequest,
    http_request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Executes a benchmark script and returns the result.
    For real-time updates, use the WebSocket endpoint instead.
    """
    # Check rate limit (5 req/min)
    await check_rate_limit(http_request, "benchmarks")
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

@app.get("/api/favorites/load")
async def load_favorites(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    # Check rate limit (30 req/min)
    await check_rate_limit(request, "favorites")
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading favorites: {str(e)}")
        return []

@app.post("/api/favorites/save")
async def save_favorite(
    config: ComparisonConfig,
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """Save a comparison configuration to favorites."""
    # Check rate limit (30 req/min)
    await check_rate_limit(request, "favorites")
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
# TILT-lite Topological Optimizer Endpoint
# ============================================================================

# ============================================================================
# Spectral-AOD/TILT Endpoint
# ============================================================================

from optimizer import SpectralAODRouter

class OptimizationRequest(BaseModel):
    num_qubits: int = 50
    num_gates: int = 200
    width: int = 20
    height: int = 20

@app.post("/api/topology/optimize")
async def optimize_topology(
    request: OptimizationRequest,
    req: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Runs the Spectral-AOD topological optimizer.
    Returns comparison of heating vs AOD complexity.
    """
    # Check rate limit (10 req/min for compute-heavy optimization)
    await check_rate_limit(req, "benchmarks")
    
    try:
        opt = SpectralAODRouter(request.width, request.height)
        graph = opt.generate_random_circuit_graph(request.num_qubits, request.num_gates)
        result = opt.optimize_mapping(graph)
        return result
    except Exception as e:
        logger.error(f"Optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# QRAM & Data Loading Endpoint
# ============================================================================

from benchmarks.benchmark_qram import run_benchmark as run_qram_benchmark

@app.get("/api/benchmarks/qram")
async def get_qram_analysis(
    req: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Returns QRAM cost analysis vs Angle Encoding.
    """
    await check_rate_limit(req, "benchmarks")
    try:
        data = run_qram_benchmark()
        return data
    except Exception as e:
        logger.error(f"QRAM benchmark failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Cryptographic Resilience Endpoint
# ============================================================================

from benchmarks.benchmark_crypto import run_crypto_benchmark

@app.get("/api/benchmarks/crypto")
async def get_crypto_analysis(
    req: Request,
    year: int = 2026,
    api_key: str = Depends(verify_api_key)
):
    """
    Returns estimated resources to break RSA/ECC vs PQC resilience.
    Uses 'year' parameter for hardware roadmap alignment (IBM/QuEra).
    """
    await check_rate_limit(req, "benchmarks")
    try:
        data = run_crypto_benchmark(target_year=year)
        return data
    except Exception as e:
        logger.error(f"Crypto benchmark failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

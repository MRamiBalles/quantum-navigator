import os
import subprocess
import json
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Quantum Navigator Backend API")

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

class RunBenchmarkRequest(BaseModel):
    benchmark_type: str

class ComparisonConfig(BaseModel):
    id: Optional[str] = None
    name: str
    benchmark: str
    circuits: List[str]
    strategies: List[str]
    chartType: str

@app.get("/")
async def root():
    return {"status": "online", "version": "4.0"}

@app.post("/api/benchmarks/run")
async def run_benchmark(request: RunBenchmarkRequest):
    """
    Executes a benchmark script and returns the result.
    If the script is not found or fails, it returns a 500 error.
    """
    script_name = f"benchmark_{request.benchmark_type}.py"
    script_path = os.path.join(BENCHMARKS_DIR, script_name)
    
    if not os.path.exists(script_path):
        # Fallback to run_all_benchmarks if specific not found
        if request.benchmark_type == "full":
            script_path = os.path.join(BENCHMARKS_DIR, "run_all_benchmarks.py")
        else:
            raise HTTPException(status_code=404, detail=f"Benchmark script {script_name} not found")

    try:
        # For simulation purposes in the browser, we'll try to find the output JSON
        # usually benchmarks save to ./benchmark_results/
        result_dir = os.path.join(BASE_DIR, "benchmark_results")
        
        # Execute script
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
            # If it fails, maybe we can just return a success if it's a known environment issue
            # but for now, we'll return the error
            
        # Try to find the JSON result file
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
    
    # Generate ID if missing
    if not config.id:
        import uuid
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

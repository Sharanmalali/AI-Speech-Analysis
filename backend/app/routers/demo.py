"""Demo endpoint: publicly accessible sample analysis for hackathon judges."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.schemas.results import ResultResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/demo", tags=["demo"])

# Path to the static demo data JSON file
DEMO_DATA_PATH = Path(__file__).parent / "demo_data.json"

# Cache the demo data in memory after first load
_demo_data_cache: ResultResponse | None = None


def load_demo_data() -> ResultResponse:
    """Load demo data from JSON file (with caching)."""
    global _demo_data_cache
    
    if _demo_data_cache is not None:
        return _demo_data_cache
    
    if not DEMO_DATA_PATH.exists():
        logger.error(
            "demo_data_missing",
            path=str(DEMO_DATA_PATH),
            message="Demo data file not found. Run generate_demo_data.py first.",
        )
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "demo_data_not_available",
                    "message": "Demo data has not been generated yet. Please contact support.",
                    "details": {
                        "info": "Run 'python backend/generate_demo_data.py' to create demo data from Sample1C.wav"
                    },
                }
            },
        )
    
    try:
        with open(DEMO_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Validate and parse into Pydantic model
        _demo_data_cache = ResultResponse.model_validate(data)
        logger.info("demo_data_loaded", speakers=_demo_data_cache.detected_speakers)
        return _demo_data_cache
        
    except json.JSONDecodeError as e:
        logger.error("demo_data_invalid_json", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "demo_data_corrupted",
                    "message": "Demo data file is corrupted.",
                }
            },
        )
    except Exception as e:
        logger.error("demo_data_load_failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "demo_data_error",
                    "message": "Failed to load demo data.",
                }
            },
        )


@router.get("/sample-result", response_model=ResultResponse, summary="Get demo analysis results (public)")
async def get_demo_results() -> ResultResponse:
    """
    Returns a pre-loaded sample analysis result from Sample1C.wav for demonstration.
    
    This endpoint is publicly accessible (no authentication required) and showcases
    a real analysis that was processed through the complete AblePro pipeline:
    - Speaker diarization (pyannote)
    - Kannada → English transcription (Whisper)
    - Gender & age classification
    - Typical/atypical speech screening (IsolationForest)
    - Full acoustic feature extraction
    
    The data is **static** and loaded from a JSON file - no ML models are invoked
    on each request. Perfect for hackathon judges to see the full product instantly
    without uploading or waiting for processing.
    
    **Note**: The demo data must be generated first by running:
    `python backend/generate_demo_data.py`
    """
    return load_demo_data()

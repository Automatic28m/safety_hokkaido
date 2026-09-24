import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime import configure_module_paths

configure_module_paths()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_backend")

import uvicorn

from agent_core.memory import global_memory
from agent_core.pipeline import RAGPipeline
from api.app import create_app

try:
    pipeline = RAGPipeline()
except Exception:
    logger.exception("Could not initialize RAG Pipeline. Did you run build_index.py?")
    pipeline = None


def get_pipeline():
    return pipeline


app = create_app(get_pipeline=get_pipeline, reset_memory=global_memory.clear)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

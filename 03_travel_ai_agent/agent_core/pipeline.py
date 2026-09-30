"""Backward-compatible entry point.

``02_api_backend/main.py`` imports ``RAGPipeline`` from here. The orchestration
itself lives in ``agent_core.main.TravelAgent``.
"""
from agent_core.main import TravelAgent

RAGPipeline = TravelAgent

__all__ = ["RAGPipeline", "TravelAgent"]

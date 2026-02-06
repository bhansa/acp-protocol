"""
Adaptive Context Protocol (ACP)
A multi-resolution data serialization framework for token-efficient LLM communication.
"""

from .document import ACPDocument
from .levels import ResolutionLevel
from .generators import LevelGenerator, SchemaBasedGenerator, LLMAssistedGenerator

__version__ = "0.1.0"
__all__ = [
    "ACPDocument",
    "ResolutionLevel",
    "LevelGenerator",
    "SchemaBasedGenerator",
    "LLMAssistedGenerator",
]

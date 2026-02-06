"""
Adaptive Context Protocol (ACP)
A multi-resolution data serialization framework for token-efficient LLM communication.
"""

from .document import ACPDocument
from .generators import LevelGenerator, LLMAssistedGenerator, SchemaBasedGenerator
from .levels import ResolutionLevel

__version__ = "0.1.0"
__all__ = [
    "ACPDocument",
    "ResolutionLevel",
    "LevelGenerator",
    "SchemaBasedGenerator",
    "LLMAssistedGenerator",
]

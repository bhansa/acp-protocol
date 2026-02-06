"""
Resolution levels for ACP documents.
"""

from enum import IntEnum
from typing import Any


class ResolutionLevel(IntEnum):
    """
    Standard ACP resolution levels.

    L0 - Existence: Boolean presence check (1-3 tokens)
    L1 - Summary: Natural language one-liner (10-30 tokens)
    L2 - Key Facts: Structured essential fields (50-150 tokens)
    L3 - Full Detail: Complete data representation (unbounded)
    """
    L0_EXISTENCE = 0
    L1_SUMMARY = 1
    L2_KEY_FACTS = 2
    L3_FULL = 3

    @classmethod
    def from_string(cls, s: str) -> "ResolutionLevel":
        """Parse resolution level from string like 'L0', 'L1', 'l2', 'L3'."""
        mapping = {
            "l0": cls.L0_EXISTENCE,
            "l1": cls.L1_SUMMARY,
            "l2": cls.L2_KEY_FACTS,
            "l3": cls.L3_FULL,
            "existence": cls.L0_EXISTENCE,
            "summary": cls.L1_SUMMARY,
            "key_facts": cls.L2_KEY_FACTS,
            "full": cls.L3_FULL,
        }
        key = s.lower().strip()
        if key in mapping:
            return mapping[key]
        raise ValueError(f"Unknown resolution level: {s}")

    @property
    def typical_tokens(self) -> tuple[int, int]:
        """Return typical (min, max) token range for this level."""
        ranges = {
            self.L0_EXISTENCE: (1, 3),
            self.L1_SUMMARY: (10, 30),
            self.L2_KEY_FACTS: (50, 150),
            self.L3_FULL: (100, 10000),
        }
        return ranges.get(self, (0, 10000))

    def __str__(self) -> str:
        names = {
            self.L0_EXISTENCE: "L0 (Existence)",
            self.L1_SUMMARY: "L1 (Summary)",
            self.L2_KEY_FACTS: "L2 (Key Facts)",
            self.L3_FULL: "L3 (Full Detail)",
        }
        return names.get(self, f"L{self.value}")

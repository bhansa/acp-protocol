"""
Core ACPDocument class for multi-resolution data representation.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Union

from .levels import ResolutionLevel


@dataclass
class ACPDocument:
    """
    An ACP document representing an entity at multiple resolution levels.

    Example:
        >>> doc = ACPDocument.from_dict(
        ...     {"name": "Alice", "role": "engineer", "email": "alice@co.com"},
        ...     entity="user",
        ...     id="user-123"
        ... )
        >>> doc.get(level=ResolutionLevel.L1_SUMMARY)
        'Alice, engineer'
        >>> doc.get(token_budget=50)
        {'name': 'Alice', 'role': 'engineer'}
    """

    entity: str
    id: str
    data: dict[str, Any]

    # Resolution level representations
    l0: str = "exists"
    l1: str = ""
    l2: dict[str, Any] = field(default_factory=dict)
    l3: dict[str, Any] = field(default_factory=dict)

    # Metadata
    token_counts: dict[str, int] = field(default_factory=dict)
    generated_at: Optional[datetime] = None
    confidence: float = 1.0

    # Configuration
    key_fields: list[str] = field(default_factory=list)
    summary_template: Optional[str] = None

    def __post_init__(self):
        """Initialize L3 from data if not set."""
        if not self.l3:
            self.l3 = self.data.copy()
        if not self.generated_at:
            self.generated_at = datetime.now()

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        entity: str,
        id: str,
        key_fields: Optional[list[str]] = None,
        summary_template: Optional[str] = None,
        auto_generate: bool = True,
    ) -> "ACPDocument":
        """
        Create an ACP document from a dictionary.

        Args:
            data: The full data dictionary
            entity: Entity type (e.g., "user", "product", "order")
            id: Unique identifier for this entity
            key_fields: Fields to include in L2 (auto-detected if None)
            summary_template: Template for L1 summary (auto-generated if None)
            auto_generate: Whether to auto-generate all levels

        Returns:
            ACPDocument instance with all levels populated
        """
        doc = cls(
            entity=entity,
            id=id,
            data=data,
            l3=data.copy(),
            key_fields=key_fields or [],
            summary_template=summary_template,
        )

        if auto_generate:
            doc.generate_levels()

        return doc

    def generate_levels(self) -> None:
        """Generate all resolution levels from the source data."""
        from .generators import SchemaBasedGenerator

        generator = SchemaBasedGenerator()

        # L0 is always "exists"
        self.l0 = "exists"

        # Generate L1 (summary)
        self.l1 = generator.generate_l1(self.data, self.entity, self.summary_template)

        # Generate L2 (key facts)
        self.l2 = generator.generate_l2(self.data, self.entity, self.key_fields)

        # L3 is the full data
        self.l3 = self.data.copy()

        # Calculate token counts
        self._calculate_tokens()

    def _calculate_tokens(self) -> None:
        """Calculate approximate token counts for each level."""
        self.token_counts = {
            "L0": _count_tokens(self.l0),
            "L1": _count_tokens(self.l1),
            "L2": _count_tokens(json.dumps(self.l2)),
            "L3": _count_tokens(json.dumps(self.l3)),
        }

    def get(
        self,
        level: Optional[Union[ResolutionLevel, int]] = None,
        token_budget: Optional[int] = None,
    ) -> Any:
        """
        Get data at a specific resolution level or within a token budget.

        Args:
            level: Specific resolution level (L0-L3)
            token_budget: Maximum tokens; returns highest level that fits

        Returns:
            Data at the requested resolution

        Raises:
            ValueError: If neither level nor token_budget specified
        """
        if level is not None:
            return self._get_level(level)

        if token_budget is not None:
            return self._get_by_budget(token_budget)

        raise ValueError("Must specify either 'level' or 'token_budget'")

    def _get_level(self, level: Union[ResolutionLevel, int]) -> Any:
        """Get data at specific level."""
        if isinstance(level, int):
            level = ResolutionLevel(level)

        if level == ResolutionLevel.L0_EXISTENCE:
            return self.l0
        elif level == ResolutionLevel.L1_SUMMARY:
            return self.l1
        elif level == ResolutionLevel.L2_KEY_FACTS:
            return self.l2
        elif level == ResolutionLevel.L3_FULL:
            return self.l3
        else:
            raise ValueError(f"Unknown level: {level}")

    def _get_by_budget(self, budget: int) -> Any:
        """Get highest resolution level that fits within token budget."""
        # Check levels from highest to lowest
        if self.token_counts.get("L3", float("inf")) <= budget:
            return self.l3
        if self.token_counts.get("L2", float("inf")) <= budget:
            return self.l2
        if self.token_counts.get("L1", float("inf")) <= budget:
            return self.l1
        return self.l0

    def to_acp_format(self, level: Optional[ResolutionLevel] = None) -> str:
        """
        Serialize to ACP text format.

        Args:
            level: If specified, include only this level; otherwise all levels

        Returns:
            ACP-formatted string
        """
        lines = [
            "@acp 1.0",
            f"@entity: {self.entity}",
            f"@id: {self.id}",
            "",
        ]

        if level is None or level == ResolutionLevel.L0_EXISTENCE:
            lines.append(f"L0: {self.l0}")
            lines.append("")

        if level is None or level == ResolutionLevel.L1_SUMMARY:
            lines.append(f'L1: "{self.l1}"')
            lines.append("")

        if level is None or level == ResolutionLevel.L2_KEY_FACTS:
            lines.append("L2:")
            for k, v in self.l2.items():
                lines.append(f"  {k}: {v}")
            lines.append("")

        if level is None or level == ResolutionLevel.L3_FULL:
            lines.append("L3:")
            for line in json.dumps(self.l3, indent=2).split("\n"):
                lines.append(f"  {line}")
            lines.append("")

        # Metadata
        lines.append("@meta:")
        lines.append(f"  tokens: {self.token_counts}")
        if self.generated_at:
            lines.append(f"  generated: {self.generated_at.isoformat()}")

        return "\n".join(lines)

    def to_json(self, level: Optional[ResolutionLevel] = None) -> str:
        """Serialize to JSON format."""
        if level is not None:
            return json.dumps(self.get(level=level), indent=2)

        return json.dumps({
            "acp_version": "1.0",
            "entity": self.entity,
            "id": self.id,
            "levels": {
                "L0": self.l0,
                "L1": self.l1,
                "L2": self.l2,
                "L3": self.l3,
            },
            "meta": {
                "tokens": self.token_counts,
                "generated": self.generated_at.isoformat() if self.generated_at else None,
            }
        }, indent=2)

    def __repr__(self) -> str:
        return f"ACPDocument(entity={self.entity!r}, id={self.id!r}, tokens={self.token_counts})"


def _count_tokens(text: str) -> int:
    """
    Count tokens in text.

    Uses tiktoken if available, otherwise approximates.
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # Approximate: ~4 chars per token + special chars
        special = sum(1 for c in text if c in '{}[]():,"\'')
        return len(text) // 4 + special // 2

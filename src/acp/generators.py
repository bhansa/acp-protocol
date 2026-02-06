"""
Level generators for automatically creating ACP resolution levels.
"""

from abc import ABC, abstractmethod
from typing import Any


class LevelGenerator(ABC):
    """Base class for ACP level generators."""

    @abstractmethod
    def generate_l1(
        self,
        data: dict[str, Any],
        entity_type: str,
        template: str | None = None,
    ) -> str:
        """Generate L1 (summary) representation."""
        pass

    @abstractmethod
    def generate_l2(
        self,
        data: dict[str, Any],
        entity_type: str,
        key_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate L2 (key facts) representation."""
        pass


class SchemaBasedGenerator(LevelGenerator):
    """
    Generate resolution levels using schema-based heuristics.

    This generator uses field names and types to automatically
    determine which fields are important for L1/L2.
    """

    # Common field names that are typically important
    HIGH_PRIORITY_FIELDS = {
        "id", "name", "title", "status", "type", "role",
        "email", "category", "price", "total", "state",
    }

    MEDIUM_PRIORITY_FIELDS = {
        "description", "summary", "created_at", "updated_at",
        "author", "owner", "user_id", "department", "company",
        "rating", "quantity", "amount", "currency",
    }

    # Fields typically not needed for summaries
    LOW_PRIORITY_FIELDS = {
        "metadata", "meta", "preferences", "settings", "config",
        "history", "logs", "audit", "internal", "cache",
        "created_by", "modified_by", "version", "revision",
    }

    # Entity-specific key fields
    ENTITY_KEY_FIELDS = {
        "user": ["name", "role", "department", "status", "email"],
        "product": ["name", "category", "price", "in_stock", "rating"],
        "order": ["id", "status", "total", "user_id", "payment_status"],
        "article": ["title", "author", "topic", "status", "word_count"],
        "document": ["title", "type", "author", "status"],
        "transaction": ["id", "type", "amount", "status", "timestamp"],
    }

    def generate_l1(
        self,
        data: dict[str, Any],
        entity_type: str,
        template: str | None = None,
    ) -> str:
        """
        Generate a natural language one-liner summary.

        Args:
            data: Full entity data
            entity_type: Type of entity (user, product, etc.)
            template: Optional template string with {field} placeholders

        Returns:
            One-line summary string
        """
        if template:
            return self._apply_template(data, template)

        # Auto-generate based on entity type
        return self._auto_summary(data, entity_type)

    def _apply_template(self, data: dict[str, Any], template: str) -> str:
        """Apply a template string to data."""
        try:
            return template.format(**self._flatten_data(data))
        except KeyError:
            # Fall back to simple substitution
            result = template
            for key, value in self._flatten_data(data).items():
                result = result.replace("{" + key + "}", str(value))
            return result

    def _auto_summary(self, data: dict[str, Any], entity_type: str) -> str:
        """Automatically generate a summary based on entity type."""
        flat = self._flatten_data(data)

        # Get the most important fields for this entity type
        if entity_type in self.ENTITY_KEY_FIELDS:
            priority_fields = self.ENTITY_KEY_FIELDS[entity_type][:4]
        else:
            # Use generic high-priority fields
            priority_fields = [f for f in self.HIGH_PRIORITY_FIELDS if f in flat][:4]

        # Build summary from available fields
        parts = []
        for field in priority_fields:
            if field in flat and flat[field]:
                value = flat[field]
                # Don't include IDs in summary unless it's the only identifier
                if field == "id" and ("name" in flat or "title" in flat):
                    continue
                parts.append(str(value))

        if not parts:
            # Fallback: use first few non-empty string values
            for key, value in flat.items():
                if isinstance(value, str) and value and len(parts) < 3:
                    parts.append(value)

        return ", ".join(parts) if parts else f"{entity_type} entity"

    def generate_l2(
        self,
        data: dict[str, Any],
        entity_type: str,
        key_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate key facts representation.

        Args:
            data: Full entity data
            entity_type: Type of entity
            key_fields: Explicit list of fields to include

        Returns:
            Dictionary with essential fields only
        """
        if key_fields:
            return self._extract_fields(data, key_fields)

        # Auto-select key fields
        return self._auto_key_facts(data, entity_type)

    def _extract_fields(
        self,
        data: dict[str, Any],
        fields: list[str],
    ) -> dict[str, Any]:
        """Extract specific fields from data."""
        result = {}
        for field in fields:
            if "." in field:
                # Handle nested fields like "author.name"
                value = self._get_nested(data, field)
                if value is not None:
                    result[field.replace(".", "_")] = value
            elif field in data:
                result[field] = self._simplify_value(data[field])
        return result

    def _auto_key_facts(
        self,
        data: dict[str, Any],
        entity_type: str,
    ) -> dict[str, Any]:
        """Automatically select key facts based on entity type."""
        result = {}

        # Use entity-specific fields if available
        if entity_type in self.ENTITY_KEY_FIELDS:
            for field in self.ENTITY_KEY_FIELDS[entity_type]:
                if field in data:
                    result[field] = self._simplify_value(data[field])
                # Check for nested fields
                elif "." in field:
                    value = self._get_nested(data, field)
                    if value is not None:
                        result[field.replace(".", "_")] = value
        else:
            # Generic: use high and medium priority fields
            for field in data:
                if field in self.HIGH_PRIORITY_FIELDS:
                    result[field] = self._simplify_value(data[field])

            # Add medium priority if we have few fields
            if len(result) < 4:
                for field in data:
                    if field in self.MEDIUM_PRIORITY_FIELDS and field not in result:
                        result[field] = self._simplify_value(data[field])
                        if len(result) >= 6:
                            break

        return result

    def _simplify_value(self, value: Any) -> Any:
        """Simplify a value for L2 representation."""
        if isinstance(value, dict):
            # For nested dicts, try to get a representative value
            if "name" in value:
                return value["name"]
            if "id" in value:
                return value["id"]
            if "value" in value:
                return value["value"]
            # Return first string value
            for v in value.values():
                if isinstance(v, str):
                    return v
            return str(value)
        elif isinstance(value, list):
            # For lists, return count or first few items
            if len(value) == 0:
                return []
            if len(value) <= 3 and all(isinstance(x, (str, int, float)) for x in value):
                return value
            return f"[{len(value)} items]"
        return value

    def _flatten_data(self, data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        """Flatten nested data structure."""
        result = {}
        for key, value in data.items():
            full_key = f"{prefix}_{key}" if prefix else key
            if isinstance(value, dict):
                result.update(self._flatten_data(value, full_key))
            else:
                result[full_key] = value
                # Also store without prefix for easy access
                if prefix:
                    result[key] = value
        return result

    def _get_nested(self, data: dict[str, Any], path: str) -> Any:
        """Get a nested value using dot notation."""
        parts = path.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value


class LLMAssistedGenerator(LevelGenerator):
    """
    Generate resolution levels using an LLM for better summaries.

    Requires an LLM client (e.g., anthropic or openai).
    """

    def __init__(self, client: Any = None, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize with an LLM client.

        Args:
            client: Anthropic or OpenAI client instance
            model: Model to use for generation
        """
        self.client = client
        self.model = model
        self._fallback = SchemaBasedGenerator()

    def generate_l1(
        self,
        data: dict[str, Any],
        entity_type: str,
        template: str | None = None,
    ) -> str:
        """Generate L1 using LLM for natural language summary."""
        if template:
            return self._fallback._apply_template(data, template)

        if not self.client:
            return self._fallback.generate_l1(data, entity_type, template)

        try:
            prompt = f"""Summarize this {entity_type} in one brief line (under 20 words).
Include only the most essential identifying information.

Data: {data}

Summary:"""

            # Try Anthropic client
            if hasattr(self.client, "messages"):
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=50,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text.strip()

            # Try OpenAI client
            if hasattr(self.client, "chat"):
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=50,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content.strip()

        except Exception:
            pass

        # Fallback to schema-based
        return self._fallback.generate_l1(data, entity_type, template)

    def generate_l2(
        self,
        data: dict[str, Any],
        entity_type: str,
        key_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate L2 - uses schema-based for consistency."""
        # L2 should be deterministic, so we use schema-based
        return self._fallback.generate_l2(data, entity_type, key_fields)

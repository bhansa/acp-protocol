"""
Tests for ACP library.
"""

import json
import pytest

from acp import ACPDocument, ResolutionLevel
from acp.generators import SchemaBasedGenerator


# Test data fixtures
@pytest.fixture
def user_data():
    return {
        "id": "user-123",
        "name": "Alice Chen",
        "email": "alice@example.com",
        "role": "Senior Engineer",
        "department": "Engineering",
        "status": "active",
        "access_level": "admin",
        "skills": ["Python", "Go", "Kubernetes"],
        "location": {
            "office": "San Francisco",
            "timezone": "America/Los_Angeles",
        },
        "preferences": {
            "theme": "dark",
            "notifications": True,
        },
    }


@pytest.fixture
def product_data():
    return {
        "id": "product-456",
        "name": "Premium Headphones",
        "category": "Electronics",
        "price": 299.99,
        "currency": "USD",
        "in_stock": True,
        "rating": 4.7,
        "description": "High-quality wireless headphones with noise cancellation.",
        "specs": {
            "weight": "250g",
            "battery_life": "30 hours",
        },
    }


class TestResolutionLevel:
    """Tests for ResolutionLevel enum."""

    def test_level_values(self):
        assert ResolutionLevel.L0_EXISTENCE == 0
        assert ResolutionLevel.L1_SUMMARY == 1
        assert ResolutionLevel.L2_KEY_FACTS == 2
        assert ResolutionLevel.L3_FULL == 3

    def test_from_string(self):
        assert ResolutionLevel.from_string("L0") == ResolutionLevel.L0_EXISTENCE
        assert ResolutionLevel.from_string("l1") == ResolutionLevel.L1_SUMMARY
        assert ResolutionLevel.from_string("L2") == ResolutionLevel.L2_KEY_FACTS
        assert ResolutionLevel.from_string("existence") == ResolutionLevel.L0_EXISTENCE
        assert ResolutionLevel.from_string("summary") == ResolutionLevel.L1_SUMMARY

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            ResolutionLevel.from_string("L5")

    def test_typical_tokens(self):
        assert ResolutionLevel.L0_EXISTENCE.typical_tokens == (1, 3)
        assert ResolutionLevel.L1_SUMMARY.typical_tokens == (10, 30)


class TestACPDocument:
    """Tests for ACPDocument class."""

    def test_from_dict_basic(self, user_data):
        doc = ACPDocument.from_dict(
            data=user_data,
            entity="user",
            id="user-123",
        )

        assert doc.entity == "user"
        assert doc.id == "user-123"
        assert doc.l0 == "exists"
        assert doc.l3 == user_data

    def test_auto_generate_l1(self, user_data):
        doc = ACPDocument.from_dict(
            data=user_data,
            entity="user",
            id="user-123",
        )

        # L1 should contain key identifying info
        assert "Alice Chen" in doc.l1
        assert len(doc.l1) < 100  # Should be concise

    def test_auto_generate_l2(self, user_data):
        doc = ACPDocument.from_dict(
            data=user_data,
            entity="user",
            id="user-123",
        )

        # L2 should have essential fields
        assert "name" in doc.l2
        assert "role" in doc.l2
        assert doc.l2["name"] == "Alice Chen"

        # L2 should not have low-priority fields
        assert "preferences" not in doc.l2

    def test_get_by_level(self, user_data):
        doc = ACPDocument.from_dict(
            data=user_data,
            entity="user",
            id="user-123",
        )

        assert doc.get(level=ResolutionLevel.L0_EXISTENCE) == "exists"
        assert isinstance(doc.get(level=ResolutionLevel.L1_SUMMARY), str)
        assert isinstance(doc.get(level=ResolutionLevel.L2_KEY_FACTS), dict)
        assert doc.get(level=ResolutionLevel.L3_FULL) == user_data

    def test_get_by_level_int(self, user_data):
        doc = ACPDocument.from_dict(
            data=user_data,
            entity="user",
            id="user-123",
        )

        assert doc.get(level=0) == "exists"
        assert doc.get(level=3) == user_data

    def test_get_by_budget(self, user_data):
        doc = ACPDocument.from_dict(
            data=user_data,
            entity="user",
            id="user-123",
        )

        # Very small budget should return L0
        result = doc.get(token_budget=5)
        assert result == "exists"

        # Medium budget should return L1 or L2
        result = doc.get(token_budget=100)
        assert result != "exists"

    def test_token_counts(self, user_data):
        doc = ACPDocument.from_dict(
            data=user_data,
            entity="user",
            id="user-123",
        )

        assert "L0" in doc.token_counts
        assert "L1" in doc.token_counts
        assert "L2" in doc.token_counts
        assert "L3" in doc.token_counts

        # Token counts should increase with level
        assert doc.token_counts["L0"] < doc.token_counts["L1"]
        assert doc.token_counts["L1"] < doc.token_counts["L2"]
        assert doc.token_counts["L2"] < doc.token_counts["L3"]

    def test_custom_key_fields(self, user_data):
        doc = ACPDocument.from_dict(
            data=user_data,
            entity="user",
            id="user-123",
            key_fields=["name", "email"],
        )

        assert "name" in doc.l2
        assert "email" in doc.l2
        assert len(doc.l2) == 2

    def test_custom_summary_template(self, user_data):
        doc = ACPDocument.from_dict(
            data=user_data,
            entity="user",
            id="user-123",
            summary_template="{name} ({role})",
        )

        assert doc.l1 == "Alice Chen (Senior Engineer)"

    def test_to_acp_format(self, user_data):
        doc = ACPDocument.from_dict(
            data=user_data,
            entity="user",
            id="user-123",
        )

        acp_str = doc.to_acp_format()

        assert "@acp 1.0" in acp_str
        assert "@entity: user" in acp_str
        assert "@id: user-123" in acp_str
        assert "L0: exists" in acp_str
        assert "L1:" in acp_str
        assert "L2:" in acp_str
        assert "L3:" in acp_str

    def test_to_json(self, user_data):
        doc = ACPDocument.from_dict(
            data=user_data,
            entity="user",
            id="user-123",
        )

        json_str = doc.to_json()
        parsed = json.loads(json_str)

        assert parsed["acp_version"] == "1.0"
        assert parsed["entity"] == "user"
        assert "levels" in parsed
        assert parsed["levels"]["L0"] == "exists"

    def test_to_json_specific_level(self, user_data):
        doc = ACPDocument.from_dict(
            data=user_data,
            entity="user",
            id="user-123",
        )

        json_str = doc.to_json(level=ResolutionLevel.L2_KEY_FACTS)
        parsed = json.loads(json_str)

        # Should just be the L2 data, not wrapped
        assert "name" in parsed
        assert "acp_version" not in parsed


class TestSchemaBasedGenerator:
    """Tests for SchemaBasedGenerator."""

    def test_generate_l1_user(self, user_data):
        gen = SchemaBasedGenerator()
        summary = gen.generate_l1(user_data, "user")

        assert "Alice Chen" in summary
        assert len(summary) < 100

    def test_generate_l1_product(self, product_data):
        gen = SchemaBasedGenerator()
        summary = gen.generate_l1(product_data, "product")

        assert "Premium Headphones" in summary

    def test_generate_l2_user(self, user_data):
        gen = SchemaBasedGenerator()
        l2 = gen.generate_l2(user_data, "user")

        assert "name" in l2
        assert "role" in l2
        assert l2["name"] == "Alice Chen"

    def test_generate_l2_product(self, product_data):
        gen = SchemaBasedGenerator()
        l2 = gen.generate_l2(product_data, "product")

        assert "name" in l2
        assert "price" in l2
        assert "in_stock" in l2

    def test_generate_l2_custom_fields(self, user_data):
        gen = SchemaBasedGenerator()
        l2 = gen.generate_l2(user_data, "user", key_fields=["name", "email"])

        assert set(l2.keys()) == {"name", "email"}

    def test_list_simplification(self):
        gen = SchemaBasedGenerator()
        data = {
            "id": "test",
            "short_list": [1, 2, 3],
            "long_list": list(range(100)),
        }
        l2 = gen.generate_l2(data, "test", key_fields=["short_list", "long_list"])

        # Short list should be preserved
        assert l2["short_list"] == [1, 2, 3]
        # Long list should be summarized
        assert "[100 items]" in str(l2["long_list"])


class TestMCPIntegration:
    """Tests for MCP server integration."""

    def test_acp_resource_decorator(self, user_data):
        from acp.mcp import acp_resource

        @acp_resource(entity="user")
        def get_user(user_id: str) -> dict:
            return user_data

        result = get_user("123")

        assert isinstance(result, ACPDocument)
        assert result.entity == "user"
        assert result.l0 == "exists"

    def test_acp_server(self, user_data):
        from acp.mcp import ACPServer

        server = ACPServer()

        @server.resource("user", key_fields=["name", "role"])
        def get_user(user_id: str) -> dict:
            return user_data

        # Test L0
        result = server.handle_request(
            "user",
            {"user_id": "123"},
            level=ResolutionLevel.L0_EXISTENCE,
        )
        assert result == "exists"

        # Test L2
        result = server.handle_request(
            "user",
            {"user_id": "123"},
            level=ResolutionLevel.L2_KEY_FACTS,
        )
        assert "name" in result

    def test_acp_server_budget(self, user_data):
        from acp.mcp import ACPServer

        server = ACPServer()

        @server.resource("user")
        def get_user(user_id: str) -> dict:
            return user_data

        # Small budget
        result = server.handle_request(
            "user",
            {"user_id": "123"},
            token_budget=5,
        )
        assert result == "exists"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
MCP Server integration for serving ACP documents.
"""

from functools import wraps
from typing import Any, Callable, Optional

from ..document import ACPDocument
from ..levels import ResolutionLevel


def acp_resource(
    entity: str,
    key_fields: Optional[list[str]] = None,
    summary_template: Optional[str] = None,
):
    """
    Decorator to convert a function's return value to an ACP document.

    Usage:
        @acp_resource(entity="user", key_fields=["name", "role"])
        def get_user(user_id: str) -> dict:
            return {"id": user_id, "name": "Alice", "role": "engineer"}

    Args:
        entity: Entity type name
        key_fields: Fields to include in L2
        summary_template: Template for L1 summary
    """
    def decorator(func: Callable[..., dict]) -> Callable[..., ACPDocument]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> ACPDocument:
            data = func(*args, **kwargs)

            # Extract ID from data or use first arg
            entity_id = data.get("id", str(args[0]) if args else "unknown")

            return ACPDocument.from_dict(
                data=data,
                entity=entity,
                id=entity_id,
                key_fields=key_fields,
                summary_template=summary_template,
            )
        return wrapper
    return decorator


class ACPServer:
    """
    Simple ACP-aware server wrapper for MCP integration.

    This provides a middleware layer that automatically handles
    ACP resolution levels based on request headers.

    Usage:
        server = ACPServer()

        @server.resource("user")
        def get_user(user_id: str) -> dict:
            return db.get_user(user_id)

        # Later, handle requests with resolution
        result = server.handle_request(
            "user",
            {"user_id": "123"},
            level=ResolutionLevel.L2_KEY_FACTS
        )
    """

    def __init__(self):
        self._resources: dict[str, Callable] = {}
        self._entity_configs: dict[str, dict] = {}

    def resource(
        self,
        entity: str,
        key_fields: Optional[list[str]] = None,
        summary_template: Optional[str] = None,
    ):
        """Register a resource handler."""
        def decorator(func: Callable[..., dict]) -> Callable[..., dict]:
            self._resources[entity] = func
            self._entity_configs[entity] = {
                "key_fields": key_fields,
                "summary_template": summary_template,
            }
            return func
        return decorator

    def handle_request(
        self,
        entity: str,
        params: dict[str, Any],
        level: Optional[ResolutionLevel] = None,
        token_budget: Optional[int] = None,
    ) -> Any:
        """
        Handle a request and return data at appropriate resolution.

        Args:
            entity: Entity type to fetch
            params: Parameters to pass to the resource handler
            level: Specific resolution level requested
            token_budget: Maximum tokens for response

        Returns:
            Data at the requested resolution level
        """
        if entity not in self._resources:
            raise ValueError(f"Unknown entity type: {entity}")

        # Get raw data from handler
        handler = self._resources[entity]
        data = handler(**params)

        # Get entity ID
        entity_id = data.get("id", params.get("id", "unknown"))

        # Create ACP document
        config = self._entity_configs.get(entity, {})
        doc = ACPDocument.from_dict(
            data=data,
            entity=entity,
            id=entity_id,
            key_fields=config.get("key_fields"),
            summary_template=config.get("summary_template"),
        )

        # Return at requested resolution
        if level is not None:
            return doc.get(level=level)
        if token_budget is not None:
            return doc.get(token_budget=token_budget)

        # Default to L2 for reasonable balance
        return doc.get(level=ResolutionLevel.L2_KEY_FACTS)

    def get_document(self, entity: str, params: dict[str, Any]) -> ACPDocument:
        """Get the full ACP document for an entity."""
        if entity not in self._resources:
            raise ValueError(f"Unknown entity type: {entity}")

        handler = self._resources[entity]
        data = handler(**params)
        entity_id = data.get("id", params.get("id", "unknown"))

        config = self._entity_configs.get(entity, {})
        return ACPDocument.from_dict(
            data=data,
            entity=entity,
            id=entity_id,
            key_fields=config.get("key_fields"),
            summary_template=config.get("summary_template"),
        )


# FastAPI middleware (if FastAPI is available)
def create_fastapi_middleware():
    """
    Create FastAPI middleware for ACP support.

    Usage:
        from fastapi import FastAPI
        from acp.mcp.server import create_fastapi_middleware

        app = FastAPI()
        app.middleware("http")(create_fastapi_middleware())
    """
    async def acp_middleware(request, call_next):
        # Check for ACP headers
        acp_level = request.headers.get("ACP-Level")
        acp_budget = request.headers.get("ACP-Budget")

        # Store in request state for handlers to use
        request.state.acp_level = int(acp_level) if acp_level else None
        request.state.acp_budget = int(acp_budget) if acp_budget else None

        response = await call_next(request)
        return response

    return acp_middleware

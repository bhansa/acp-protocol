# Adaptive Context Resolution

Multi-resolution data serialization for token-efficient LLM communication.

[![PyPI version](https://badge.fury.io/py/adaptive-context-resolution.svg)](https://pypi.org/project/adaptive-context-resolution/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

Adaptive Context Resolution enables data sources to serve information at multiple resolution levels, dramatically reducing token consumption when communicating with LLMs.

| Level | Name | Description | Typical Tokens |
|-------|------|-------------|----------------|
| L0 | Existence | Boolean presence check | 1-3 |
| L1 | Summary | Natural language one-liner | 10-30 |
| L2 | Key Facts | Structured essential fields | 50-150 |
| L3 | Full Detail | Complete data | Unbounded |

**Results:** 88-96% token reduction vs JSON for typical workloads.

## Installation

```bash
pip install adaptive-context-resolution
```

With optional dependencies:
```bash
pip install adaptive-context-resolution[tiktoken]  # Accurate token counting
pip install adaptive-context-resolution[llm]       # LLM-assisted summaries
```

## Quick Start

```python
from acp import ACPDocument, ResolutionLevel

# Your data
user = {
    "id": "user-123",
    "name": "Alice Chen",
    "email": "alice@example.com",
    "role": "Senior Engineer",
    "department": "Platform",
    "status": "active",
    "skills": ["Python", "Go", "Kubernetes"],
    "preferences": {"theme": "dark", "notifications": True}
}

# Create ACP document (auto-generates all levels)
doc = ACPDocument.from_dict(user, entity="user", id="user-123")

# Get data at different resolutions
doc.get(level=ResolutionLevel.L0_EXISTENCE)  # "exists"
doc.get(level=ResolutionLevel.L1_SUMMARY)    # "Alice Chen, Senior Engineer, Platform, active"
doc.get(level=ResolutionLevel.L2_KEY_FACTS)  # {"name": "Alice Chen", "role": "Senior Engineer", ...}
doc.get(level=ResolutionLevel.L3_FULL)       # Full data

# Or specify a token budget
doc.get(token_budget=50)  # Returns highest level that fits
```

## Token Counts

```python
print(doc.token_counts)
# {'L0': 1, 'L1': 12, 'L2': 45, 'L3': 180}
```

## Custom Level Generation

```python
# Specify which fields matter for L2
doc = ACPDocument.from_dict(
    data=user,
    entity="user",
    id="user-123",
    key_fields=["name", "role", "email"],
    summary_template="{name} <{email}>"
)
```

## MCP Integration

```python
from acp.mcp import ACPServer, acp_resource

server = ACPServer()

@server.resource("user", key_fields=["name", "role"])
def get_user(user_id: str) -> dict:
    return database.get_user(user_id)

# Handle requests with resolution control
result = server.handle_request(
    "user",
    {"user_id": "123"},
    level=ResolutionLevel.L2_KEY_FACTS
)
```

## ACP Format Output

```python
print(doc.to_acp_format())
```

```yaml
@acp 1.0
@entity: user
@id: user-123

L0: exists

L1: "Alice Chen, Senior Engineer, Platform, active"

L2:
  name: Alice Chen
  role: Senior Engineer
  department: Platform
  status: active

L3:
  {"id": "user-123", "name": "Alice Chen", ...}

@meta:
  tokens: {L0: 1, L1: 12, L2: 45, L3: 180}
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read our contributing guidelines.

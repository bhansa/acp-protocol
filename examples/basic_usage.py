"""
Basic usage examples for ACP library.
"""

from acp import ACPDocument, ResolutionLevel


def main():
    # Example: User entity
    user_data = {
        "id": "user-12345",
        "name": "Alice Chen",
        "email": "alice.chen@acme.corp",
        "role": "Senior Engineer",
        "department": "Platform Engineering",
        "status": "active",
        "access_level": "admin",
        "skills": ["Python", "Go", "Kubernetes", "AWS"],
        "projects": ["project-101", "project-202", "project-303"],
        "location": {
            "office": "San Francisco",
            "timezone": "America/Los_Angeles",
            "desk": "B-412",
        },
        "preferences": {
            "theme": "dark",
            "notifications": True,
            "language": "en",
        },
        "metrics": {
            "commits_30d": 47,
            "reviews_30d": 23,
            "meetings_30d": 18,
        },
    }

    # Create ACP document with auto-generated levels
    doc = ACPDocument.from_dict(
        data=user_data,
        entity="user",
        id="user-12345",
    )

    print("=" * 60)
    print("ACP Document Example")
    print("=" * 60)

    # Show all levels
    print("\n--- L0 (Existence) ---")
    print(doc.get(level=ResolutionLevel.L0_EXISTENCE))
    print(f"Tokens: {doc.token_counts['L0']}")

    print("\n--- L1 (Summary) ---")
    print(doc.get(level=ResolutionLevel.L1_SUMMARY))
    print(f"Tokens: {doc.token_counts['L1']}")

    print("\n--- L2 (Key Facts) ---")
    import json
    print(json.dumps(doc.get(level=ResolutionLevel.L2_KEY_FACTS), indent=2))
    print(f"Tokens: {doc.token_counts['L2']}")

    print("\n--- L3 (Full Detail) ---")
    print(f"[Full data - {doc.token_counts['L3']} tokens]")

    # Token budget example
    print("\n" + "=" * 60)
    print("Token Budget Example")
    print("=" * 60)

    for budget in [5, 50, 200]:
        result = doc.get(token_budget=budget)
        print(f"\nBudget: {budget} tokens")
        print(f"Result type: {type(result).__name__}")
        if isinstance(result, str):
            print(f"Value: {result}")
        else:
            print(f"Keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")

    # ACP format output
    print("\n" + "=" * 60)
    print("ACP Format Output")
    print("=" * 60)
    print(doc.to_acp_format())

    # Custom key fields
    print("\n" + "=" * 60)
    print("Custom Key Fields Example")
    print("=" * 60)

    custom_doc = ACPDocument.from_dict(
        data=user_data,
        entity="user",
        id="user-12345",
        key_fields=["name", "email", "role"],
        summary_template="{name} <{email}> - {role}",
    )

    print(f"Custom L1: {custom_doc.l1}")
    print(f"Custom L2: {custom_doc.l2}")


if __name__ == "__main__":
    main()

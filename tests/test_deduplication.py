"""Unit tests for deduplication and content-hash algorithms."""

from gseim.database.deduplication import generate_composite_key, generate_content_hash

def test_composite_key_normalization():
    # Different tracking params & casing should produce the same composite key
    key1 = generate_composite_key(
        "Techstars",
        "2027 Accelerator Cohort",
        "https://www.techstars.com/accelerators?utm_source=twitter&utm_medium=social"
    )
    key2 = generate_composite_key(
        "techstars ",
        "2027 accelerator cohort",
        "https://www.techstars.com/accelerators/"
    )
    assert key1 == key2

def test_composite_key_distinct():
    key1 = generate_composite_key("Org A", "Program One", "https://example.com/one")
    key2 = generate_composite_key("Org B", "Program One", "https://example.com/one")
    assert key1 != key2

def test_content_hash_update_detection():
    # Initial state
    hash_v1 = generate_content_hash(
        "Seed funding up to $50k",
        "15-Oct-2026",
        "Early stage startups in UK"
    )

    # Identical state
    hash_v1_dup = generate_content_hash(
        "Seed funding up to $50k",
        "15-Oct-2026",
        "Early stage startups in UK"
    )
    assert hash_v1 == hash_v1_dup

    # Updated state (e.g. deadline extended or funding increased)
    hash_v2 = generate_content_hash(
        "Seed funding up to $100k",
        "30-Oct-2026",
        "Early stage startups in UK"
    )
    assert hash_v1 != hash_v2

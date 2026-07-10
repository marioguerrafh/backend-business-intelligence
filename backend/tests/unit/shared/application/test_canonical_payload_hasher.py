from app.shared.application.hashing.canonical_payload_hasher import CanonicalPayloadHasher


def test_hash_payload_is_deterministic_and_order_independent() -> None:
    hasher = CanonicalPayloadHasher()

    payload_a = {"b": 2, "a": 1, "nested": {"y": "2", "x": "1"}}
    payload_b = {"nested": {"x": "1", "y": "2"}, "a": 1, "b": 2}

    assert hasher.hash_payload(payload_a) == hasher.hash_payload(payload_b)


def test_hash_payload_changes_when_payload_changes() -> None:
    hasher = CanonicalPayloadHasher()

    payload_a = {"id": "A", "name": "Item"}
    payload_b = {"id": "A", "name": "Item 2"}

    assert hasher.hash_payload(payload_a) != hasher.hash_payload(payload_b)

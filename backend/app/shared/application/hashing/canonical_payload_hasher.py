import hashlib
import json
from collections.abc import Mapping
from typing import Any


class CanonicalPayloadHasher:
    def hash_payload(self, payload: Mapping[str, Any]) -> str:
        normalized = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

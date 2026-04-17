import hashlib
import json
from dataclasses import dataclass
from threading import Lock


@dataclass
class IdempotencyRecord:
    run_id: str
    payload_fingerprint: str


_STORE: dict[str, IdempotencyRecord] = {}
_LOCK = Lock()


def payload_fingerprint(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def get_record(key: str) -> IdempotencyRecord | None:
    with _LOCK:
        return _STORE.get(key)


def save_record(key: str, run_id: str, payload: dict) -> IdempotencyRecord:
    record = IdempotencyRecord(run_id=run_id, payload_fingerprint=payload_fingerprint(payload))
    with _LOCK:
        _STORE[key] = record
    return record

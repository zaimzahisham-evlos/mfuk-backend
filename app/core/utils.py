from datetime import datetime, UTC
from typing import Any

def utcnow() -> datetime:
    return datetime.now(UTC)

def set_attributes(obj: object, data: dict[str, Any]) -> None:
    for key, value in data.items():
        setattr(obj, key, value)

def trim_and_reject_blank(v: str) -> str:
    """prevents duplicate logical identities ('UC001' vs 'UC001 ')"""
    v = v.strip()
    if not v:
        raise ValueError("Value cannot be blank")
    return v
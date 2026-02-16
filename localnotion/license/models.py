"""License data models for LocalNotion."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Literal

PRODUCTS: frozenset[str] = frozenset({
    "LN",   # LocalNotion
    "CF",   # Course Factory (legacy)
    "QC",   # QuantCoder
    "WM",   # Windmar
    "UNI",  # Universal (all-product bundle)
})

TIERS: frozenset[str] = frozenset({"free", "standard", "pro", "enterprise"})

Tier = Literal["free", "standard", "pro", "enterprise"]


@dataclass(frozen=True, slots=True)
class LicensePayload:
    email: str
    product: str
    tier: Tier
    expiry: str
    max_machines: int = 1
    issued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if self.product not in PRODUCTS:
            raise ValueError(f"Unknown product {self.product!r}. Valid: {sorted(PRODUCTS)}")
        if self.tier not in TIERS:
            raise ValueError(f"Unknown tier {self.tier!r}. Valid: {sorted(TIERS)}")
        if self.max_machines < 0:
            raise ValueError("max_machines must be >= 0")
        datetime.fromisoformat(self.expiry)
        datetime.fromisoformat(self.issued_at)

    def to_json_bytes(self) -> bytes:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()

    @classmethod
    def from_json_bytes(cls, raw: bytes) -> LicensePayload:
        return cls(**json.loads(raw))

    @property
    def is_expired(self) -> bool:
        expiry_dt = datetime.fromisoformat(self.expiry)
        if expiry_dt.tzinfo is None:
            expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= expiry_dt

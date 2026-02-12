"""License data models for Course Factory.

Defines the canonical product codes, tier levels, and the immutable
``LicensePayload`` that travels inside every signed license key.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Literal

# ---------------------------------------------------------------------------
# Product codes  (append-only – never remove or rename a shipped code)
# ---------------------------------------------------------------------------
PRODUCTS: frozenset[str] = frozenset({
    "CF",   # Course Factory (core platform)
    "QC",   # QuantCoder
    "WM",   # Windmar
    "SK",   # Skillkit
    "ST",   # StrategyTester
    "CS",   # CaseStudy
    "CWF",  # CourseWare Forge
    "UNI",  # Universal (all-product bundle)
})

# ---------------------------------------------------------------------------
# Tier levels
# ---------------------------------------------------------------------------
TIERS: frozenset[str] = frozenset({"free", "pro", "enterprise"})

Tier = Literal["free", "pro", "enterprise"]

# ---------------------------------------------------------------------------
# Payload
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class LicensePayload:
    """Immutable description of a single license grant.

    Parameters
    ----------
    email : str
        Licensee e-mail address.
    product : str
        One of :data:`PRODUCTS`.
    tier : Tier
        One of ``"free"``, ``"pro"``, ``"enterprise"``.
    expiry : str
        ISO-8601 UTC date-time after which the license is no longer valid
        (e.g. ``"2027-01-01T00:00:00+00:00"``).
    max_machines : int
        Maximum number of distinct machine fingerprints that may activate
        this license concurrently.  ``0`` means unlimited.
    issued_at : str
        ISO-8601 UTC date-time when the license was generated.  Defaults
        to *now* if not supplied explicitly.
    """

    email: str
    product: str
    tier: Tier
    expiry: str
    max_machines: int = 1
    issued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # -- validation ----------------------------------------------------------

    def __post_init__(self) -> None:
        if self.product not in PRODUCTS:
            raise ValueError(
                f"Unknown product {self.product!r}. "
                f"Valid products: {sorted(PRODUCTS)}"
            )
        if self.tier not in TIERS:
            raise ValueError(
                f"Unknown tier {self.tier!r}. Valid tiers: {sorted(TIERS)}"
            )
        if self.max_machines < 0:
            raise ValueError("max_machines must be >= 0")

        # Validate ISO-8601 date strings are parseable
        try:
            datetime.fromisoformat(self.expiry)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid expiry date: {self.expiry!r}") from exc
        try:
            datetime.fromisoformat(self.issued_at)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid issued_at date: {self.issued_at!r}") from exc

    # -- serialisation -------------------------------------------------------

    def to_json_bytes(self) -> bytes:
        """Deterministic UTF-8 JSON encoding (sorted keys, no whitespace)."""
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()

    @classmethod
    def from_json_bytes(cls, raw: bytes) -> LicensePayload:
        """Deserialise from the canonical JSON byte representation."""
        data = json.loads(raw)
        return cls(**data)

    # -- convenience ---------------------------------------------------------

    @property
    def is_expired(self) -> bool:
        """Return ``True`` when the current UTC time is past *expiry*."""
        expiry_dt = datetime.fromisoformat(self.expiry)
        # Ensure timezone-aware comparison
        if expiry_dt.tzinfo is None:
            expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= expiry_dt

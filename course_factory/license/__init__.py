"""Course Factory license subsystem.

Provides Ed25519-based license key generation (developer-side) and
validation (client-side) for all Course Factory products.

Public API
----------
- ``LicensePayload``  – immutable data-class describing a single license.
- ``validate_key``    – verify a license key string and return its payload.
- ``PRODUCTS`` / ``TIERS`` – canonical product and tier enumerations.
"""

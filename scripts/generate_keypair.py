#!/usr/bin/env python3
"""Generate an Ed25519 signing / verification keypair for Course Factory.

Usage::

    python scripts/generate_keypair.py            # default -> keys/
    python scripts/generate_keypair.py --out /tmp  # custom directory

The script creates two files:

- ``<out>/cf.private``  -- 32-byte raw Ed25519 seed (signing key).
  **Keep this secret.**  Used only by ``keygen.py``.
- ``<out>/cf.public``   -- 32-byte raw Ed25519 verify key.
  Embedded (hex-encoded) in ``validator.py`` for client-side checks.

Both files are binary (exactly 32 bytes each).  The corresponding
hex-encoded representations are also printed to stdout for convenient
copy-paste into source code.
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

try:
    from nacl.signing import SigningKey
except ImportError:
    print(
        "ERROR: PyNaCl is not installed.\n"
        "Install it with:  pip install pynacl",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an Ed25519 keypair for Course Factory licensing.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "keys",
        help="Output directory for key files (default: keys/).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing key files without prompting.",
    )
    args = parser.parse_args()

    out_dir: Path = args.out.resolve()
    private_path = out_dir / "cf.private"
    public_path = out_dir / "cf.public"

    # -- Safety check --------------------------------------------------------
    if not args.force and (private_path.exists() or public_path.exists()):
        print(
            f"Key files already exist in {out_dir}/\n"
            f"  {private_path}\n"
            f"  {public_path}\n"
            f"\n"
            f"Re-run with --force to overwrite, or delete the files manually.",
            file=sys.stderr,
        )
        sys.exit(1)

    # -- Generate ------------------------------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)

    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key

    private_bytes: bytes = bytes(signing_key)  # 32-byte seed
    public_bytes: bytes = bytes(verify_key)    # 32-byte public key

    # -- Write private key (owner-only permissions) --------------------------
    private_path.write_bytes(private_bytes)
    os.chmod(private_path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600

    # -- Write public key ----------------------------------------------------
    public_path.write_bytes(public_bytes)

    # -- Report --------------------------------------------------------------
    private_hex = private_bytes.hex()
    public_hex = public_bytes.hex()

    print("=" * 68)
    print("  Course Factory -- Ed25519 Keypair Generated")
    print("=" * 68)
    print()
    print(f"  Private key : {private_path}")
    print(f"  Public key  : {public_path}")
    print()
    print(f"  Private hex : {private_hex}")
    print(f"  Public hex  : {public_hex}")
    print()
    print("  NEXT STEPS:")
    print()
    print("  1. Copy the public hex string above into:")
    print("     course_factory/license/validator.py -> _PUBLIC_KEY_HEX")
    print()
    print("  2. Keep cf.private SECRET. Do not commit it to version control.")
    print("     Add 'keys/*.private' to your .gitignore.")
    print()
    print("  3. Back up cf.private in a secure location (password manager,")
    print("     encrypted volume, etc.). If lost, all issued licenses")
    print("     become unverifiable.")
    print()
    print("=" * 68)


if __name__ == "__main__":
    main()

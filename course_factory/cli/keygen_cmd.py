"""License key generation and validation commands."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from course_factory.license.models import LicensePayload, PRODUCTS, TIERS

console = Console()
keygen_app = typer.Typer(name="keygen", help="License key management")

# Default directory for keypair storage (project root / keys)
_KEYS_DIR = Path(__file__).resolve().parents[2] / "keys"


def _keys_dir() -> Path:
    """Return the keys directory, creating it if needed."""
    _KEYS_DIR.mkdir(parents=True, exist_ok=True)
    return _KEYS_DIR


# -- commands ----------------------------------------------------------------


@keygen_app.command()
def init() -> None:
    """Generate a new Ed25519 keypair for license signing."""
    from nacl.signing import SigningKey

    keys_path = _keys_dir()
    private_path = keys_path / "private.key"
    public_path = keys_path / "public.key"

    if private_path.exists():
        console.print("[yellow]Keypair already exists. Overwrite?[/yellow]")
        overwrite = typer.confirm("Continue?", default=False)
        if not overwrite:
            raise typer.Exit()

    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key

    # Store raw 32-byte keys as base64
    private_path.write_text(base64.b64encode(bytes(signing_key)).decode(), encoding="utf-8")
    public_path.write_text(base64.b64encode(bytes(verify_key)).decode(), encoding="utf-8")

    # Restrict private key permissions
    private_path.chmod(0o600)

    console.print(Panel.fit(
        f"[green]Ed25519 keypair generated[/green]\n\n"
        f"  Private key: [bold]{private_path}[/bold]\n"
        f"  Public key:  [bold]{public_path}[/bold]\n\n"
        f"[dim]Keep private.key secret. Distribute public.key with your app.[/dim]",
        title="Keygen",
    ))


@keygen_app.command()
def generate(
    email: str = typer.Argument(..., help="Licensee email address"),
    product: str = typer.Argument(..., help=f"Product code: {sorted(PRODUCTS)}"),
    tier: str = typer.Option("pro", help=f"License tier: {sorted(TIERS)}"),
    days: int = typer.Option(365, help="Validity period in days"),
    max_machines: int = typer.Option(3, help="Max concurrent machine activations"),
) -> None:
    """Generate a signed license key."""
    from nacl.signing import SigningKey

    private_path = _keys_dir() / "private.key"
    if not private_path.exists():
        console.print("[red]Private key not found. Run 'cf keygen init' first.[/red]")
        raise typer.Exit(code=1)

    # Load private key
    try:
        raw_key = base64.b64decode(private_path.read_text(encoding="utf-8").strip())
        signing_key = SigningKey(raw_key)
    except Exception as exc:
        console.print(f"[red]Failed to load private key: {exc}[/red]")
        raise typer.Exit(code=1)

    # Build payload
    expiry = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    try:
        payload = LicensePayload(
            email=email,
            product=product.upper(),
            tier=tier.lower(),
            expiry=expiry,
            max_machines=max_machines,
        )
    except ValueError as exc:
        console.print(f"[red]Invalid payload: {exc}[/red]")
        raise typer.Exit(code=1)

    # Sign: signature + payload bytes, then base64url-encode the whole thing
    payload_bytes = payload.to_json_bytes()
    signed = signing_key.sign(payload_bytes)
    license_key = base64.urlsafe_b64encode(signed).decode()

    console.print(Panel.fit(
        f"[green]License key generated[/green]\n\n"
        f"  Email:        {email}\n"
        f"  Product:      {product.upper()}\n"
        f"  Tier:         {tier.lower()}\n"
        f"  Expires:      {expiry}\n"
        f"  Max machines: {max_machines}\n\n"
        f"[bold]License Key:[/bold]\n{license_key}",
        title="License",
    ))


@keygen_app.command()
def validate(
    key: str = typer.Argument(..., help="License key to validate"),
) -> None:
    """Validate a license key and display its payload."""
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError

    public_path = _keys_dir() / "public.key"
    if not public_path.exists():
        console.print("[red]Public key not found. Run 'cf keygen init' first.[/red]")
        raise typer.Exit(code=1)

    # Load public key
    try:
        raw_key = base64.b64decode(public_path.read_text(encoding="utf-8").strip())
        verify_key = VerifyKey(raw_key)
    except Exception as exc:
        console.print(f"[red]Failed to load public key: {exc}[/red]")
        raise typer.Exit(code=1)

    # Decode and verify
    try:
        signed_bytes = base64.urlsafe_b64decode(key)
        payload_bytes = verify_key.verify(signed_bytes)
        payload = LicensePayload.from_json_bytes(payload_bytes)
    except BadSignatureError:
        console.print("[red]INVALID: Signature verification failed.[/red]")
        raise typer.Exit(code=1)
    except Exception as exc:
        console.print(f"[red]INVALID: {exc}[/red]")
        raise typer.Exit(code=1)

    # Display result
    status = "[red]EXPIRED[/red]" if payload.is_expired else "[green]VALID[/green]"
    console.print(Panel.fit(
        f"Status:       {status}\n"
        f"Email:        {payload.email}\n"
        f"Product:      {payload.product}\n"
        f"Tier:         {payload.tier}\n"
        f"Expires:      {payload.expiry}\n"
        f"Max machines: {payload.max_machines}\n"
        f"Issued at:    {payload.issued_at}",
        title="License Validation",
    ))

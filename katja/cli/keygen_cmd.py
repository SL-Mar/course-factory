"""License key generation and validation commands."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from katja.license.models import LicensePayload, PRODUCTS, TIERS

console = Console()
keygen_app = typer.Typer(name="keygen", help="License key management")

_KEYS_DIR = Path(__file__).resolve().parents[2] / "keys"


def _keys_dir() -> Path:
    _KEYS_DIR.mkdir(parents=True, exist_ok=True)
    return _KEYS_DIR


@keygen_app.command()
def init() -> None:
    """Generate a new Ed25519 keypair for license signing."""
    from nacl.signing import SigningKey

    keys_path = _keys_dir()
    private_path = keys_path / "private.key"
    public_path = keys_path / "public.key"

    if private_path.exists():
        console.print("[yellow]Keypair already exists. Overwrite?[/yellow]")
        if not typer.confirm("Continue?", default=False):
            raise typer.Exit()

    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key

    private_path.write_text(base64.b64encode(bytes(signing_key)).decode(), encoding="utf-8")
    public_path.write_text(base64.b64encode(bytes(verify_key)).decode(), encoding="utf-8")
    private_path.chmod(0o600)

    console.print(Panel.fit(
        f"[green]Ed25519 keypair generated[/green]\n\n"
        f"  Private key: [bold]{private_path}[/bold]\n"
        f"  Public key:  [bold]{public_path}[/bold]",
        title="Keygen",
    ))


@keygen_app.command()
def generate(
    email: str = typer.Argument(...),
    product: str = typer.Argument(..., help=f"Product code: {sorted(PRODUCTS)}"),
    tier: str = typer.Option("pro", help=f"Tier: {sorted(TIERS)}"),
    days: int = typer.Option(365),
    max_machines: int = typer.Option(3),
) -> None:
    """Generate a signed license key."""
    from nacl.signing import SigningKey

    private_path = _keys_dir() / "private.key"
    if not private_path.exists():
        console.print("[red]Run 'katja keygen init' first.[/red]")
        raise typer.Exit(code=1)

    raw_key = base64.b64decode(private_path.read_text(encoding="utf-8").strip())
    signing_key = SigningKey(raw_key)

    expiry = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
    payload = LicensePayload(email=email, product=product.upper(), tier=tier.lower(), expiry=expiry, max_machines=max_machines)

    payload_bytes = payload.to_json_bytes()
    signed = signing_key.sign(payload_bytes)
    license_key = base64.urlsafe_b64encode(signed).decode()

    console.print(Panel.fit(
        f"[green]License key generated[/green]\n\n"
        f"  Email:   {email}\n  Product: {product.upper()}\n  Tier: {tier}\n  Expires: {expiry}\n\n"
        f"[bold]Key:[/bold]\n{license_key}",
        title="License",
    ))


@keygen_app.command()
def validate(key: str = typer.Argument(...)) -> None:
    """Validate a license key."""
    from nacl.signing import VerifyKey
    from nacl.exceptions import BadSignatureError

    public_path = _keys_dir() / "public.key"
    if not public_path.exists():
        console.print("[red]Run 'katja keygen init' first.[/red]")
        raise typer.Exit(code=1)

    raw_key = base64.b64decode(public_path.read_text(encoding="utf-8").strip())
    verify_key = VerifyKey(raw_key)

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

    status = "[red]EXPIRED[/red]" if payload.is_expired else "[green]VALID[/green]"
    console.print(Panel.fit(
        f"Status: {status}\nEmail: {payload.email}\nProduct: {payload.product}\nTier: {payload.tier}\nExpires: {payload.expiry}",
        title="License Validation",
    ))

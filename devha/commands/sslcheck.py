"""SSL/TLS Certificate Inspector."""

from __future__ import annotations

import datetime
import json
import socket
import ssl
from typing import Annotated

import typer

from devha.ui import console, make_table, info, warn, error, success


def sslcheck(
    host: Annotated[str, typer.Argument(help="Hostname (e.g. github.com).")],
    port: Annotated[int, typer.Option("--port", "-p")] = 443,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    SSL/TLS certificate inspector — expiry, issuer, SANs, protocol, ciphers.

    Example:
      devha sslcheck github.com
      devha sslcheck expired.badssl.com
    """
    host = host.replace("https://", "").replace("http://", "").split("/")[0]
    info(f"Checking SSL/TLS on [cyan]{host}:{port}[/cyan]...")

    cert = proto = cipher = None
    verified = True

    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                proto = ssock.version()
                cipher = ssock.cipher()
    except ssl.SSLCertVerificationError as e:
        verified = False
        warn(f"Certificate verification failed: {e}")
        ctx2 = ssl.create_default_context()
        ctx2.check_hostname = False
        ctx2.verify_mode = ssl.CERT_NONE
        try:
            with socket.create_connection((host, port), timeout=10) as sock:
                with ctx2.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    proto = ssock.version()
                    cipher = ssock.cipher()
        except Exception as e2:
            error(f"Cannot connect: {e2}")
            raise typer.Exit(1)
    except Exception as e:
        error(f"Cannot connect to {host}:{port} — {e}")
        raise typer.Exit(1)

    if not cert:
        error("No certificate returned.")
        raise typer.Exit(1)

    subject = dict(x[0] for x in cert.get("subject", []))
    issuer  = dict(x[0] for x in cert.get("issuer", []))
    not_after = cert.get("notAfter", "")
    not_before = cert.get("notBefore", "")
    sans = [v for t, v in cert.get("subjectAltName", []) if t == "DNS"]

    expiry = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
    days_left = (expiry - datetime.datetime.utcnow()).days

    if json_out:
        console.print_json(json.dumps({
            "host": host, "port": port, "verified": verified,
            "subject": subject, "issuer": issuer,
            "not_before": not_before, "not_after": not_after,
            "days_until_expiry": days_left, "sans": sans,
            "protocol": proto, "cipher": cipher[0] if cipher else None,
        }))
        return

    table = make_table("FIELD", "VALUE", title=f"🔒 SSL Certificate — {host}")
    table.add_row("[cyan]Common Name[/cyan]",  subject.get("commonName", "?"))
    table.add_row("[cyan]Organization[/cyan]", subject.get("organizationName", "?"))
    table.add_row("[cyan]Issuer[/cyan]",        issuer.get("organizationName", "?"))
    table.add_row("[cyan]Valid From[/cyan]",    not_before)

    exp_s = "bright_red" if days_left < 14 else "yellow" if days_left < 30 else "bright_green"
    table.add_row("[cyan]Expires[/cyan]", f"[{exp_s}]{not_after} ({days_left}d left)[/{exp_s}]")

    proto_s = "bright_green" if proto in ("TLSv1.3", "TLSv1.2") else "bright_red"
    table.add_row("[cyan]Protocol[/cyan]", f"[{proto_s}]{proto}[/{proto_s}]")
    table.add_row("[cyan]Cipher[/cyan]",   cipher[0] if cipher else "?")
    table.add_row("[cyan]SANs[/cyan]",     ", ".join(sans[:5]) + ("…" if len(sans) > 5 else ""))
    table.add_row("[cyan]Verified[/cyan]", "[bright_green]Yes[/bright_green]" if verified else "[bright_red]No — self-signed or invalid[/bright_red]")
    console.print(table)

    console.print("\n[bold]Security Verdict:[/bold]")
    if days_left < 0:
        console.print("  [bright_red]✘ EXPIRED![/bright_red]")
    elif days_left < 14:
        console.print(f"  [bright_red]⚠ Expiring in {days_left} days![/bright_red]")
    elif days_left < 30:
        console.print(f"  [yellow]⚠ Expiring soon ({days_left} days)[/yellow]")
    else:
        console.print(f"  [bright_green]✔ Valid — {days_left} days remaining[/bright_green]")

    if proto == "TLSv1.3":
        console.print("  [bright_green]✔ TLS 1.3 — best available[/bright_green]")
    elif proto == "TLSv1.2":
        console.print("  [bright_green]✔ TLS 1.2 — good[/bright_green]")
    else:
        console.print(f"  [bright_red]✘ {proto} — deprecated and vulnerable![/bright_red]")

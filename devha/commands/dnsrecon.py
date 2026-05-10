"""DNS Reconnaissance — query all record types, zone transfer, SPF/DMARC."""

from __future__ import annotations

import json
from typing import Annotated

import typer

from devha.ui import console, make_table, info, warn, error, success

app = typer.Typer(help="🔍 DNS Recon — query records, zone transfer, email security.")


def dnsrecon(
    domain: Annotated[str, typer.Argument(help="Domain to query (e.g. example.com).")],
    record_type: Annotated[str, typer.Option("--type", "-t", help="Record type: A,MX,NS,TXT,CNAME,SOA,AAAA or 'all'.")] = "all",
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    DNS Reconnaissance — queries A, MX, NS, TXT, CNAME, SOA records.
    Also tests zone transfer and analyses SPF/DMARC email security.

    Example:
      devha dnsrecon example.com
      devha dnsrecon example.com --type MX
    """
    try:
        import dns.resolver
        import dns.zone
        import dns.query
        import dns.exception
    except ImportError:
        error("dnspython not installed. Run: pip install dnspython")
        raise typer.Exit(1)

    info(f"DNS Recon on [cyan]{domain}[/cyan]...\n")

    results: dict[str, list[str]] = {}
    record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"] if record_type == "all" else [record_type.upper()]

    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(domain, rtype)
            results[rtype] = [r.to_text() for r in answers]
        except Exception:
            results[rtype] = []

    # Zone transfer attempt on each NS
    zone_results: dict[str, list[str] | None] = {}
    for ns in results.get("NS", [])[:3]:
        ns_clean = ns.rstrip(".")
        try:
            zone = dns.zone.from_xfr(dns.query.xfr(ns_clean, domain, timeout=5))
            zone_results[ns_clean] = [str(n) for n in zone.nodes.keys()][:20]
        except Exception:
            zone_results[ns_clean] = None

    # SPF / DMARC
    spf = next((r for r in results.get("TXT", []) if "v=spf1" in r.lower()), "")
    dmarc = ""
    try:
        import dns.resolver as _r
        dmarc_ans = _r.resolve(f"_dmarc.{domain}", "TXT")
        dmarc = " ".join(r.to_text() for r in dmarc_ans)
    except Exception:
        pass

    if json_out:
        console.print_json(json.dumps({"domain": domain, "records": results, "zone_transfer": zone_results, "spf": spf, "dmarc": dmarc}))
        return

    # Print records
    for rtype, records in results.items():
        if records:
            table = make_table("TYPE", "VALUE", title=f"DNS {rtype} — {domain}")
            style_map = {"A": "cyan", "AAAA": "cyan", "MX": "bright_green", "NS": "yellow", "TXT": "magenta", "CNAME": "blue", "SOA": "dim"}
            for r in records:
                s = style_map.get(rtype, "white")
                table.add_row(f"[{s}]{rtype}[/{s}]", r[:100])
            console.print(table)

    # Security analysis
    console.print("\n[bold cyan]── Email Security ──[/bold cyan]")
    if spf:
        console.print(f"  [bright_green]✔ SPF:[/bright_green]   {spf[:80]}")
    else:
        console.print("  [bright_red]✘ SPF:   Not configured — email spoofing possible![/bright_red]")

    if dmarc:
        console.print(f"  [bright_green]✔ DMARC:[/bright_green] {dmarc[:80]}")
    else:
        console.print("  [bright_red]✘ DMARC: Not configured — phishing risk![/bright_red]")

    # Zone transfer results
    console.print("\n[bold cyan]── Zone Transfer ──[/bold cyan]")
    for ns, names in zone_results.items():
        if names:
            warn(f"⚠️  ZONE TRANSFER SUCCEEDED on {ns}! Misconfiguration!")
            console.print(f"  Records: {', '.join(names[:8])}{'...' if len(names) > 8 else ''}")
        else:
            console.print(f"  [dim]Blocked on {ns} ✔[/dim]")

"""IP Intelligence — geolocation, ASN, ISP, proxy/VPN detection."""

from __future__ import annotations

import json
import socket
from typing import Annotated

import httpx
import typer

from devha.ui import console, make_table, info, error


def ipinfo(
    target: Annotated[str, typer.Argument(help="IP address or hostname.")],
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    IP / Domain Intelligence — location, ISP, ASN, proxy/VPN detection.

    Uses ip-api.com (free, no API key needed).

    Example:
      devha ipinfo 8.8.8.8
      devha ipinfo github.com
    """
    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        error(f"Cannot resolve: {target}")
        raise typer.Exit(1)

    if ip != target:
        info(f"Resolved [cyan]{target}[/cyan] → [cyan]{ip}[/cyan]")

    info(f"Looking up [cyan]{ip}[/cyan]...")

    try:
        resp = httpx.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,message,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as,proxy,hosting,query"},
            timeout=10,
        )
        data = resp.json()
    except Exception as e:
        error(f"API error: {e}")
        raise typer.Exit(1)

    if data.get("status") != "success":
        error(f"Lookup failed: {data.get('message', 'unknown')}")
        raise typer.Exit(1)

    if json_out:
        console.print_json(json.dumps(data))
        return

    code = data.get("countryCode", "")
    flag = (chr(0x1F1E6 + ord(code[0]) - 65) + chr(0x1F1E6 + ord(code[1]) - 65)) if len(code) == 2 else "🌐"

    table = make_table("FIELD", "VALUE", title=f"🌍 IP Intelligence — {data.get('query', ip)}")
    table.add_row("[cyan]IP Address[/cyan]",   data.get("query", ip))
    table.add_row("[cyan]Country[/cyan]",       f"{flag} {data.get('country','?')} ({code})")
    table.add_row("[cyan]Region[/cyan]",        data.get("regionName", "?"))
    table.add_row("[cyan]City[/cyan]",          data.get("city", "?"))
    table.add_row("[cyan]Coordinates[/cyan]",   f"{data.get('lat','?')}, {data.get('lon','?')}")
    table.add_row("[cyan]Timezone[/cyan]",      data.get("timezone", "?"))
    table.add_row("[cyan]ISP[/cyan]",           data.get("isp", "?"))
    table.add_row("[cyan]Organization[/cyan]",  data.get("org", "?"))
    table.add_row("[cyan]ASN[/cyan]",           data.get("as", "?"))

    proxy   = data.get("proxy", False)
    hosting = data.get("hosting", False)
    table.add_row("[cyan]Proxy / VPN[/cyan]",  f"[bright_red]YES — anonymizer[/bright_red]" if proxy else "[bright_green]No[/bright_green]")
    table.add_row("[cyan]Datacenter[/cyan]",   f"[yellow]YES — hosting/DC IP[/yellow]" if hosting else "[bright_green]No[/bright_green]")
    console.print(table)

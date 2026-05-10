"""Ping command — ICMP ping using system ping."""

from __future__ import annotations

import json
import platform
import subprocess
import re
from typing import Annotated

import typer

from devha.ui import console, print_panel, error, info


def ping(
    host: Annotated[str, typer.Argument(help="Target hostname or IP.")],
    count: Annotated[int, typer.Option("--count", "-c", help="Number of pings.")] = 4,
    timeout: Annotated[float, typer.Option("--timeout", help="Timeout per ping in seconds.")] = 2.0,
    json_out: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
) -> None:
    """
    Ping a host — shows RTT, TTL, packet loss.

    Examples:
      devha ping 8.8.8.8
      devha ping example.com --count 8
    """
    info(f"Pinging [cyan]{host}[/cyan] ({count} packets)...\n")

    system = platform.system()
    if system == "Windows":
        cmd = ["ping", "-n", str(count), host]
    elif system == "Darwin":
        cmd = ["ping", "-c", str(count), "-W", str(int(timeout * 1000)), host]
    else:
        cmd = ["ping", "-c", str(count), "-W", str(int(timeout)), host]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout + result.stderr
    except FileNotFoundError:
        error("ping command not found on this system.")
        raise typer.Exit(1)

    results = []
    for line in output.splitlines():
        line_s = line.strip()
        m = re.search(r"icmp_seq=?(\d+).*?ttl=(\d+).*?time=([\d.]+)\s*ms", line_s, re.IGNORECASE)
        if m:
            seq, ttl, rtt = m.group(1), m.group(2), m.group(3)
            results.append({"seq": int(seq), "status": "reply", "rtt_ms": float(rtt), "ttl": int(ttl)})
            console.print(f"  [{seq}] [bright_green]Reply[/bright_green]  ttl={ttl}  rtt=[cyan]{rtt}ms[/cyan]")
        elif "timeout" in line_s.lower() or "request timeout" in line_s.lower():
            results.append({"seq": len(results) + 1, "status": "timeout", "rtt_ms": None, "ttl": None})
            console.print(f"  [yellow]Request timeout[/yellow]")

    console.print()
    for line in output.splitlines():
        ls = line.strip()
        if "packet loss" in ls.lower() or "packets transmitted" in ls.lower():
            console.print(f"  [dim]{ls}[/dim]")
        elif "round-trip" in ls.lower() or "rtt" in ls.lower():
            console.print(f"  [dim]{ls}[/dim]")

    if json_out:
        console.print_json(json.dumps({"host": host, "results": results}))

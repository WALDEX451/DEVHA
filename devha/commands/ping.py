"""Ping command — uses system ping, no root required."""

from __future__ import annotations

import json
import platform
import re
import subprocess
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
    ICMP ping — shows RTT, TTL, and packet loss.

    Examples:
      devha ping 8.8.8.8
      devha ping example.com --count 10
    """
    info(f"Pinging [cyan]{host}[/cyan] ({count} packets)...\n")

    system = platform.system()
    if system == "Darwin":
        cmd = ["ping", "-c", str(count), "-W", str(int(timeout * 1000)), host]
    elif system == "Windows":
        cmd = ["ping", "-n", str(count), "-w", str(int(timeout * 1000)), host]
    else:
        cmd = ["ping", "-c", str(count), "-W", str(int(timeout)), host]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout + result.stderr
    except FileNotFoundError:
        error("'ping' command not found on this system.")
        raise typer.Exit(1)

    # Parse individual replies
    pattern = re.compile(r"icmp_seq=?(\d+).*?ttl=(\d+).*?time=([\d.]+)\s*ms", re.IGNORECASE)
    results = []
    rtts = []

    for line in output.splitlines():
        m = pattern.search(line)
        if m:
            seq = int(m.group(1))
            ttl = int(m.group(2))
            rtt = float(m.group(3))
            rtts.append(rtt)
            results.append({"seq": seq, "status": "reply", "rtt_ms": rtt, "ttl": ttl})
            console.print(
                f"  [{seq}] [bright_green]Reply[/bright_green]  "
                f"ttl={ttl}  rtt=[cyan]{rtt:.2f}ms[/cyan]"
            )
        elif re.search(r"(request timeout|no route|unreachable|timed out)", line, re.IGNORECASE):
            seq = len(results) + 1
            results.append({"seq": seq, "status": "timeout", "rtt_ms": None, "ttl": None})
            console.print(f"  [{seq}] [yellow]Request timeout[/yellow]")

    if not results:
        console.print(output)

    if json_out:
        console.print_json(json.dumps({"host": host, "results": results}))
        return

    sent = count
    received = len(rtts)
    loss = round((sent - received) / sent * 100) if sent else 0
    avg_rtt = round(sum(rtts) / len(rtts), 2) if rtts else 0
    min_rtt = round(min(rtts), 2) if rtts else 0
    max_rtt = round(max(rtts), 2) if rtts else 0

    summary = (
        f"[bold]Sent:[/bold] {sent}  "
        f"[bold]Received:[/bold] [bright_green]{received}[/bright_green]  "
        f"[bold]Loss:[/bold] [{'bright_red' if loss > 0 else 'bright_green'}]{loss}%[/{'bright_red' if loss > 0 else 'bright_green'}]  "
        f"[bold]RTT:[/bold] min={min_rtt}ms avg={avg_rtt}ms max={max_rtt}ms"
    )
    print_panel(summary, title=f"Ping Summary — {host}")

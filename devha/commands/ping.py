"""Ping command — ICMP ping using scapy (educational packet-level view)."""

from __future__ import annotations

import json
import os
import time
from typing import Annotated

import typer

from devha.ui import console, make_table, print_panel, error, warn, info


def ping(
    host: Annotated[str, typer.Argument(help="Target hostname or IP.")],
    count: Annotated[int, typer.Option("--count", "-c", help="Number of pings.")] = 4,
    show_packet: Annotated[bool, typer.Option("--show-packet", help="Show raw packet detail (educational).")] = False,
    timeout: Annotated[float, typer.Option("--timeout", help="Timeout per ping in seconds.")] = 2.0,
    json_out: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
) -> None:
    """
    ICMP ping using Scapy — shows packet-level detail.

    Examples:
      devha ping 8.8.8.8
      devha ping example.com --count 4 --show-packet
    """
    try:
        from scapy.all import IP, ICMP, sr1  # type: ignore[import]
        from scapy.all import conf as scapy_conf  # type: ignore[import]
        scapy_conf.verb = 0
    except ImportError:
        error("Scapy is not installed. Run: pip install scapy")
        raise typer.Exit(1)

    if os.geteuid() != 0:
        error("Ping requires root/admin privileges. Try: sudo devha ping ...")
        raise typer.Exit(1)

    info(f"Pinging [cyan]{host}[/cyan] with {count} ICMP packets...\n")

    results = []
    rtts = []

    for seq in range(1, count + 1):
        pkt = IP(dst=host) / ICMP(seq=seq)
        t_start = time.time()
        try:
            reply = sr1(pkt, timeout=timeout)
            rtt = (time.time() - t_start) * 1000
        except Exception as exc:
            error(f"Send error: {exc}")
            results.append({"seq": seq, "status": "error", "rtt_ms": None, "ttl": None})
            continue

        if reply is None:
            results.append({"seq": seq, "status": "timeout", "rtt_ms": None, "ttl": None})
            console.print(f"  [{seq}] [yellow]Request timeout[/yellow]")
        else:
            ttl = reply.ttl
            size = len(reply)
            rtts.append(rtt)
            results.append({"seq": seq, "status": "reply", "rtt_ms": round(rtt, 2), "ttl": ttl, "size": size})
            console.print(
                f"  [{seq}] [bright_green]Reply[/bright_green]  "
                f"ttl={ttl}  size={size}B  rtt=[cyan]{rtt:.2f}ms[/cyan]"
            )

            if show_packet:
                console.print(f"       [dim]{reply.summary()}[/dim]")

    if json_out:
        console.print_json(json.dumps({"host": host, "results": results}))
        return

    # Summary
    sent = count
    received = sum(1 for r in results if r["status"] == "reply")
    loss = round((sent - received) / sent * 100)
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

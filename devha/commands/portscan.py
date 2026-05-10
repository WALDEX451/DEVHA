"""Portscan command — mini nmap using sockets and threading."""

from __future__ import annotations

import json
import socket
import concurrent.futures
from typing import Annotated

import typer
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

from devha.ui import console, make_table, error
from devha.ethics import ethics_check


def _parse_port_range(ports: str) -> list[int]:
    result: list[int] = []
    for part in ports.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            result.extend(range(int(lo), int(hi) + 1))
        else:
            result.append(int(part))
    return result


def _get_service(port: int) -> str:
    try:
        return socket.getservbyport(port)
    except OSError:
        return "unknown"


def _scan_port(host: str, port: int, timeout: float) -> dict | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            if result == 0:
                return {"port": port, "status": "open", "service": _get_service(port)}
    except (socket.gaierror, OSError):
        pass
    return None


def portscan(
    target: Annotated[str, typer.Argument(help="Target IP address or hostname.")],
    ports: Annotated[str, typer.Option("--ports", "-p", help="Port range, e.g. 1-1024 or 22,80,443.")] = "1-1024",
    threads: Annotated[int, typer.Option("--threads", help="Number of concurrent threads.")] = 100,
    timeout: Annotated[float, typer.Option("--timeout", help="Socket timeout in seconds.")] = 1.0,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip ethics confirmation.")] = False,
    json_out: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
) -> None:
    """
    Scan open ports on a host.

    Examples:
      devha portscan 192.168.1.1
      devha portscan scanme.nmap.org --ports 1-1000 --threads 200
      devha portscan 10.0.0.1 --ports 22,80,443,8080 --yes
    """
    ethics_check(target, yes=yes)

    try:
        resolved = socket.gethostbyname(target)
    except socket.gaierror:
        error(f"Cannot resolve host: {target}")
        raise typer.Exit(1)

    port_list = _parse_port_range(ports)
    open_ports: list[dict] = []

    console.print(f"[blue]Scanning[/blue] [cyan]{target}[/cyan] ({resolved})  "
                  f"[blue]ports[/blue] [cyan]{ports}[/cyan]  "
                  f"[blue]threads[/blue] [cyan]{threads}[/cyan]\n")

    with Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Scanning...", total=len(port_list))

        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(_scan_port, resolved, p, timeout): p for p in port_list}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    open_ports.append(result)
                progress.advance(task)

    open_ports.sort(key=lambda x: x["port"])

    if json_out:
        console.print_json(json.dumps({"target": target, "resolved": resolved, "open_ports": open_ports}))
        return

    if not open_ports:
        console.print(f"\n[yellow]No open ports found on {target} in range {ports}.[/yellow]")
        return

    table = make_table("PORT", "STATUS", "SERVICE", title=f"Open ports on {target}")
    for p in open_ports:
        table.add_row(
            f"[cyan]{p['port']}[/cyan]",
            "[bright_green]OPEN[/bright_green]",
            p["service"],
        )
    console.print(table)
    console.print(f"\n[bright_green]Found {len(open_ports)} open port(s).[/bright_green]")

"""Device Scanner — advanced port scan with OS detection and CVE lookup."""

from __future__ import annotations

import asyncio
import json
import socket
import concurrent.futures
from typing import Annotated

import httpx
import typer
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

from devha.ui import console, make_table, print_panel, info, warn, error, success
from devha.ethics import ethics_check

# Common service banners / signatures
_SERVICE_PROBES = {
    21: b"",
    22: b"",
    25: b"",
    80: b"HEAD / HTTP/1.0\r\n\r\n",
    443: b"",
    3306: b"",
    5432: b"",
    6379: b"PING\r\n",
    27017: b"",
}

_OS_TTLS = {
    (60, 70): "Linux",
    (120, 135): "Windows",
    (250, 260): "macOS / BSD",
    (50, 60): "Linux (low TTL)",
}

_CVE_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def _detect_os_by_ttl(ttl: int) -> str:
    for (lo, hi), os_name in _OS_TTLS.items():
        if lo <= ttl <= hi:
            return os_name
    return "Unknown"


def _grab_banner(host: str, port: int, timeout: float = 2.0) -> str:
    try:
        probe = _SERVICE_PROBES.get(port, b"")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            if probe:
                s.sendall(probe)
            banner = s.recv(1024)
            return banner.decode("utf-8", errors="ignore").strip()[:120]
    except Exception:
        return ""


def _scan_port(host: str, port: int, timeout: float) -> dict | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            if s.connect_ex((host, port)) == 0:
                try:
                    service = socket.getservbyport(port)
                except OSError:
                    service = "unknown"
                banner = _grab_banner(host, port, timeout)
                return {"port": port, "service": service, "banner": banner}
    except (socket.gaierror, OSError):
        pass
    return None


def _parse_port_range(ports: str) -> list[int]:
    result = []
    for part in ports.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            result.extend(range(int(lo), int(hi) + 1))
        else:
            result.append(int(part))
    return result


async def _fetch_cves(keyword: str) -> list[dict]:
    """Fetch CVEs from NVD NIST for a service keyword."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(_CVE_API, params={"keywordSearch": keyword, "resultsPerPage": 5})
            if resp.status_code == 200:
                data = resp.json()
                cves = []
                for item in data.get("vulnerabilities", []):
                    cve = item.get("cve", {})
                    cve_id = cve.get("id", "?")
                    descs = cve.get("descriptions", [])
                    desc = next((d["value"] for d in descs if d["lang"] == "en"), "")[:100]
                    score = "?"
                    metrics = cve.get("metrics", {})
                    for v in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                        if v in metrics and metrics[v]:
                            score = metrics[v][0].get("cvssData", {}).get("baseScore", "?")
                            break
                    cves.append({"id": cve_id, "score": score, "desc": desc})
                return cves
    except Exception:
        pass
    return []


def devscanner(
    target: Annotated[str, typer.Argument(help="Target IP or hostname.")],
    ports: Annotated[str, typer.Option("--ports", "-p", help="Port range, e.g. 1-1024 or 22,80,443.")] = "1-1024",
    threads: Annotated[int, typer.Option("--threads", help="Concurrent threads.")] = 150,
    timeout: Annotated[float, typer.Option("--timeout", help="Socket timeout.")] = 0.8,
    cve_lookup: Annotated[bool, typer.Option("--cve", help="Lookup CVEs for found services (requires internet).")] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip ethics confirmation.")] = False,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    Advanced port scanner with banner grabbing, OS detection, and CVE lookup.

    Example:
      devha devscanner 192.168.1.1
      devha devscanner scanme.nmap.org --cve
      devha devscanner 10.0.0.1 --ports 1-65535 --threads 300
    """
    ethics_check(target, yes=yes)

    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        error(f"Cannot resolve: {target}")
        raise typer.Exit(1)

    port_list = _parse_port_range(ports)
    open_ports: list[dict] = []

    info(f"Scanning [cyan]{target}[/cyan] ({ip})  ports=[cyan]{ports}[/cyan]  threads=[cyan]{threads}[/cyan]\n")

    with Progress(SpinnerColumn(), "[cyan]Scanning...", BarColumn(), TaskProgressColumn(), TimeElapsedColumn(), console=console) as prog:
        task = prog.add_task("scan", total=len(port_list))
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as ex:
            futures = {ex.submit(_scan_port, ip, p, timeout): p for p in port_list}
            for fut in concurrent.futures.as_completed(futures):
                result = fut.result()
                if result:
                    open_ports.append(result)
                prog.advance(task)

    open_ports.sort(key=lambda x: x["port"])

    # OS detection via ICMP TTL
    os_guess = "Unknown"
    try:
        import os as _os
        if _os.geteuid() == 0:
            from scapy.all import IP, ICMP, sr1, conf as sc  # type: ignore[import]
            sc.verb = 0
            r = sr1(IP(dst=ip) / ICMP(), timeout=2)
            if r:
                os_guess = _detect_os_by_ttl(r.ttl)
    except Exception:
        pass

    # CVE lookup
    cve_data: dict[str, list] = {}
    if cve_lookup and open_ports:
        info("Looking up CVEs for found services...")
        services = list({p["service"] for p in open_ports if p["service"] != "unknown"})
        cve_data = {svc: asyncio.run(_fetch_cves(svc)) for svc in services[:5]}

    if json_out:
        console.print_json(json.dumps({"target": target, "ip": ip, "os_guess": os_guess, "open_ports": open_ports, "cves": cve_data}))
        return

    # Main results table
    table = make_table("PORT", "SERVICE", "BANNER", title=f"🔌 Open ports on {target} ({ip})")
    for p in open_ports:
        banner_short = p["banner"][:60] + "…" if len(p["banner"]) > 60 else p["banner"]
        table.add_row(
            f"[cyan]{p['port']}[/cyan]",
            f"[bright_green]{p['service']}[/bright_green]",
            f"[dim]{banner_short}[/dim]",
        )
    console.print(table)

    if os_guess != "Unknown":
        console.print(f"\n[blue]OS guess:[/blue] [cyan]{os_guess}[/cyan] (based on TTL)")

    console.print(f"[bright_green]Found {len(open_ports)} open port(s).[/bright_green]  [dim]⚡ Stay ethical[/dim]\n")

    # CVE results
    if cve_data:
        for svc, cves in cve_data.items():
            if cves:
                cve_table = make_table("CVE ID", "SCORE", "DESCRIPTION", title=f"🔴 CVEs for {svc}")
                for cve in cves:
                    score = float(cve["score"]) if str(cve["score"]).replace(".", "").isdigit() else 0
                    score_style = "bright_red" if score >= 7 else "yellow" if score >= 4 else "bright_green"
                    cve_table.add_row(
                        f"[cyan]{cve['id']}[/cyan]",
                        f"[{score_style}]{cve['score']}[/{score_style}]",
                        cve["desc"],
                    )
                console.print(cve_table)

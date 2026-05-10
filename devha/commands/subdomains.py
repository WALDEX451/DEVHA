"""Subdomains command — find subdomains via wordlist, crt.sh, and HackerTarget."""

from __future__ import annotations

import asyncio
import json
import socket
from importlib.resources import files
from typing import Annotated

import httpx
import typer

from devha.ui import console, make_table, info, warn, error

_HACKERTARGET = "https://api.hackertarget.com/hostsearch/?q={}"
_CRTSH = "https://crt.sh/?q=%25.{}&output=json"


def _dns_resolve(hostname: str) -> str | None:
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None


async def _wordlist_scan(domain: str, client: httpx.AsyncClient) -> list[dict]:
    wordlist_data = files("devha.data").joinpath("subdomains.txt").read_text(encoding="utf-8")
    words = [w.strip() for w in wordlist_data.splitlines() if w.strip()]
    results = []

    async def check(word: str) -> dict | None:
        hostname = f"{word}.{domain}"
        ip = await asyncio.get_event_loop().run_in_executor(None, _dns_resolve, hostname)
        if ip:
            return {"subdomain": hostname, "ip": ip, "method": "wordlist"}
        return None

    tasks = [check(w) for w in words]
    found = await asyncio.gather(*tasks)
    results.extend(r for r in found if r)
    return results


async def _crtsh_scan(domain: str, client: httpx.AsyncClient) -> list[dict]:
    results = []
    try:
        resp = await client.get(_CRTSH.format(domain), timeout=15.0)
        if resp.status_code == 200:
            entries = resp.json()
            seen: set[str] = set()
            for entry in entries:
                name = entry.get("name_value", "")
                for sub in name.splitlines():
                    sub = sub.strip().lstrip("*.")
                    if sub.endswith(domain) and sub not in seen:
                        seen.add(sub)
                        ip = await asyncio.get_event_loop().run_in_executor(None, _dns_resolve, sub)
                        results.append({"subdomain": sub, "ip": ip or "N/A", "method": "crt.sh"})
    except (httpx.RequestError, ValueError):
        warn("crt.sh request failed — skipping.")
    return results


async def _hackertarget_scan(domain: str, client: httpx.AsyncClient) -> list[dict]:
    results = []
    try:
        resp = await client.get(_HACKERTARGET.format(domain), timeout=15.0)
        if resp.status_code == 200 and "error" not in resp.text.lower()[:20]:
            for line in resp.text.strip().splitlines():
                if "," in line:
                    sub, ip = line.split(",", 1)
                    results.append({"subdomain": sub.strip(), "ip": ip.strip(), "method": "hackertarget"})
    except httpx.RequestError:
        warn("HackerTarget request failed — skipping.")
    return results


async def _run_all(domain: str, method: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        tasks = []
        if method in ("all", "wordlist"):
            tasks.append(_wordlist_scan(domain, client))
        if method in ("all", "crt"):
            tasks.append(_crtsh_scan(domain, client))
        if method in ("all", "hackertarget"):
            tasks.append(_hackertarget_scan(domain, client))

        all_results: list[dict] = []
        for coro_results in await asyncio.gather(*tasks):
            all_results.extend(coro_results)

    # Deduplicate by subdomain
    seen: set[str] = set()
    deduped = []
    for r in all_results:
        if r["subdomain"] not in seen:
            seen.add(r["subdomain"])
            deduped.append(r)
    return sorted(deduped, key=lambda x: x["subdomain"])


def subdomains(
    domain: Annotated[str, typer.Argument(help="Target domain (e.g. example.com).")],
    method: Annotated[str, typer.Option("--method", "-m", help="[wordlist|crt|hackertarget|all]")] = "all",
    json_out: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
) -> None:
    """
    Discover subdomains via wordlist brute-force, crt.sh, and HackerTarget.

    Examples:
      devha subdomains example.com
      devha subdomains example.com --method crt
      devha subdomains tesla.com --method wordlist
    """
    valid_methods = {"all", "wordlist", "crt", "hackertarget"}
    if method not in valid_methods:
        error(f"Unknown method '{method}'. Choose: {', '.join(valid_methods)}")
        raise typer.Exit(1)

    info(f"Scanning subdomains for [cyan]{domain}[/cyan] using method=[cyan]{method}[/cyan]...")

    results = asyncio.run(_run_all(domain, method))

    if json_out:
        console.print_json(json.dumps({"domain": domain, "results": results}))
        return

    if not results:
        console.print(f"[yellow]No subdomains found for {domain}.[/yellow]")
        return

    table = make_table("SUBDOMAIN", "IP", "METHOD", title=f"Subdomains of {domain}")
    for r in results:
        method_color = {"wordlist": "cyan", "crt.sh": "blue", "hackertarget": "magenta"}.get(r["method"], "white")
        table.add_row(
            f"[bright_green]{r['subdomain']}[/bright_green]",
            r["ip"],
            f"[{method_color}]{r['method']}[/{method_color}]",
        )
    console.print(table)
    console.print(f"\n[bright_green]Found {len(results)} subdomain(s).[/bright_green]")

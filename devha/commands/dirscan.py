"""Dirscan command — directory/path brute-force scanner."""

from __future__ import annotations

import asyncio
import json
import time
from importlib.resources import files
from typing import Annotated
from urllib.parse import urljoin

import httpx
import typer
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

from devha.ui import console, make_table, error, warn, info
from devha.ethics import ethics_check

_INTERESTING_CODES = {200, 201, 204, 301, 302, 307, 308, 401, 403, 405}


async def _check_path(
    client: httpx.AsyncClient,
    base_url: str,
    path: str,
    semaphore: asyncio.Semaphore,
    rate_limiter: list[float],
    rate: float,
) -> dict | None:
    async with semaphore:
        # Simple rate limiting
        now = time.time()
        if rate_limiter and (now - rate_limiter[-1]) < (1.0 / rate):
            await asyncio.sleep((1.0 / rate) - (now - rate_limiter[-1]))
        rate_limiter.append(time.time())

        url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
        try:
            resp = await client.head(url, timeout=5.0, follow_redirects=False)
            if resp.status_code in _INTERESTING_CODES:
                content_length = resp.headers.get("content-length", "-")
                return {
                    "status": resp.status_code,
                    "size": content_length,
                    "path": "/" + path.lstrip("/"),
                    "url": url,
                }
        except httpx.RequestError:
            pass
    return None


async def _run_scan(
    base_url: str,
    paths: list[str],
    threads: int,
    rate: float,
    user_agent: str,
) -> list[dict]:
    semaphore = asyncio.Semaphore(threads)
    rate_limiter: list[float] = []
    headers = {"User-Agent": user_agent}

    async with httpx.AsyncClient(headers=headers, follow_redirects=False) as client:
        tasks = [_check_path(client, base_url, p, semaphore, rate_limiter, rate) for p in paths]
        results = await asyncio.gather(*tasks)

    return [r for r in results if r is not None]


def dirscan(
    url: Annotated[str, typer.Argument(help="Target URL (e.g. https://example.com).")],
    threads: Annotated[int, typer.Option("--threads", help="Concurrent threads.")] = 50,
    extensions: Annotated[str, typer.Option("--extensions", "-e", help="Extra extensions to append (e.g. php,html,txt).")] = "",
    user_agent: Annotated[str, typer.Option("--user-agent", "-A", help="Custom User-Agent.")] = "devha/0.1 dirscan",
    rate: Annotated[float, typer.Option("--rate", "-r", help="Max requests per second.")] = 10.0,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip ethics confirmation.")] = False,
    json_out: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
) -> None:
    """
    Brute-force common paths on a web server.

    Examples:
      devha dirscan https://example.com
      devha dirscan https://target.local --extensions php,html --threads 20
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    from urllib.parse import urlparse
    host = urlparse(url).netloc
    ethics_check(host, yes=yes)

    # Load paths
    paths_data = files("devha.data").joinpath("common_paths.txt").read_text(encoding="utf-8")
    base_paths = [p.strip() for p in paths_data.splitlines() if p.strip()]

    # Expand with extensions
    all_paths = list(base_paths)
    if extensions:
        exts = [e.strip().lstrip(".") for e in extensions.split(",") if e.strip()]
        for path in base_paths:
            if "." not in path.split("/")[-1]:
                for ext in exts:
                    all_paths.append(f"{path}.{ext}")

    info(f"Scanning [cyan]{url}[/cyan] with {len(all_paths)} paths  "
         f"[blue]threads[/blue]=[cyan]{threads}[/cyan]  "
         f"[blue]rate[/blue]=[cyan]{rate}/s[/cyan]\n")

    results = asyncio.run(_run_scan(url, all_paths, threads, rate, user_agent))
    results.sort(key=lambda x: x["status"])

    if json_out:
        console.print_json(json.dumps({"url": url, "results": results}))
        return

    if not results:
        console.print(f"[yellow]Nothing interesting found at {url}.[/yellow]")
        return

    table = make_table("STATUS", "SIZE", "PATH", title=f"Dirscan results — {url}")
    for r in results:
        code = r["status"]
        if code == 200:
            code_style = "bright_green"
        elif code in (301, 302, 307, 308):
            code_style = "cyan"
        elif code in (401, 403):
            code_style = "yellow"
        else:
            code_style = "white"
        table.add_row(
            f"[{code_style}]{code}[/{code_style}]",
            str(r["size"]),
            f"[{code_style}]{r['path']}[/{code_style}]",
        )
    console.print(table)
    console.print(f"\n[bright_green]Found {len(results)} interesting path(s).[/bright_green]")

"""Username command — check username existence on 50+ platforms."""

from __future__ import annotations

import asyncio
import json
from importlib.resources import files
from typing import Annotated

import httpx
import typer

from devha.ui import console, make_table, info


def _load_sites() -> dict:
    data = files("devha.data").joinpath("sites.json").read_text(encoding="utf-8")
    return json.loads(data)


async def _check_site(
    client: httpx.AsyncClient,
    site_name: str,
    template: dict,
    username: str,
    timeout: float,
) -> dict:
    url = template["url"].replace("{}", username)
    error_code = template.get("error_code", 404)
    try:
        resp = await client.get(url, timeout=timeout, follow_redirects=True)
        if resp.status_code == error_code:
            status = "not_found"
        elif resp.status_code < 400:
            status = "found"
        else:
            status = f"error_{resp.status_code}"
    except httpx.TimeoutException:
        status = "timeout"
    except httpx.RequestError:
        status = "error"
    return {"site": site_name, "status": status, "url": url}


async def _run_checks(username: str, sites: dict, site_filter: list[str], timeout: float) -> list[dict]:
    if site_filter:
        sites = {k: v for k, v in sites.items() if k.lower() in [s.lower() for s in site_filter]}

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0"
    }
    async with httpx.AsyncClient(headers=headers) as client:
        tasks = [_check_site(client, name, tmpl, username, timeout) for name, tmpl in sites.items()]
        return await asyncio.gather(*tasks)


def username(
    name: Annotated[str, typer.Argument(help="Username to search for.")],
    sites: Annotated[str, typer.Option("--sites", "-s", help="Comma-separated site names (default: all).")] = "",
    timeout: Annotated[float, typer.Option("--timeout", help="Request timeout in seconds.")] = 5.0,
    found_only: Annotated[bool, typer.Option("--found", help="Show only found accounts.")] = False,
    json_out: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
) -> None:
    """
    Check if a username exists on 50+ platforms.

    Examples:
      devha username torvalds
      devha username coolkid42 --sites github,reddit,twitter
      devha username hacker --found
    """
    all_sites = _load_sites()
    site_filter = [s.strip() for s in sites.split(",") if s.strip()] if sites else []

    info(f"Checking username [cyan]{name}[/cyan] across {len(site_filter) or len(all_sites)} sites...")

    results = asyncio.run(_run_checks(name, all_sites, site_filter, timeout))
    results.sort(key=lambda x: (x["status"] != "found", x["site"].lower()))

    if found_only:
        results = [r for r in results if r["status"] == "found"]

    if json_out:
        console.print_json(json.dumps({"username": name, "results": results}))
        return

    table = make_table("SITE", "STATUS", "URL", title=f"Username: {name}")
    for r in results:
        st = r["status"]
        if st == "found":
            status_str = "[bright_green]✔  FOUND[/bright_green]"
        elif st == "not_found":
            status_str = "[red]✘  NOT FOUND[/red]"
        elif st == "timeout":
            status_str = "[yellow]⚠  TIMEOUT[/yellow]"
        else:
            status_str = f"[yellow]⚠  {st.upper()}[/yellow]"

        url_str = f"[cyan]{r['url']}[/cyan]" if st == "found" else r["url"]
        table.add_row(r["site"], status_str, url_str)

    console.print(table)
    found_count = sum(1 for r in results if r["status"] == "found")
    console.print(f"\n[bright_green]Found on {found_count}[/bright_green] / {len(results)} platform(s).")

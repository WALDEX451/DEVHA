"""Harvest command — gather public info about a domain (mini-theHarvester)."""

from __future__ import annotations

import json
import re
from typing import Annotated
from urllib.parse import quote_plus

import httpx
import typer
from bs4 import BeautifulSoup
from rich.text import Text

from devha.ui import console, print_panel, warn, info, error

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_CRTSH = "https://crt.sh/?q=%25.{}&output=json"
_DDG_URL = "https://html.duckduckgo.com/html/?q={}"


def _ddg_search(query: str, client: httpx.Client) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept": "text/html",
    }
    try:
        resp = client.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers=headers,
            timeout=15.0,
        )
        return resp.text
    except httpx.RequestError:
        return ""


def _harvest_emails(domain: str, client: httpx.Client) -> set[str]:
    emails: set[str] = set()
    html = _ddg_search(f'site:{domain} "@{domain}"', client)
    if html:
        emails.update(e for e in _EMAIL_RE.findall(html) if e.endswith(f"@{domain}"))
    html2 = _ddg_search(f'"{domain}" email OR contact', client)
    if html2:
        emails.update(e for e in _EMAIL_RE.findall(html2) if domain in e)
    return emails


def _harvest_subdomains_crt(domain: str, client: httpx.Client) -> set[str]:
    subs: set[str] = set()
    try:
        resp = client.get(_CRTSH.format(domain), timeout=15.0)
        if resp.status_code == 200:
            for entry in resp.json():
                for name in entry.get("name_value", "").splitlines():
                    name = name.strip().lstrip("*.")
                    if name.endswith(domain):
                        subs.add(name)
    except (httpx.RequestError, ValueError):
        pass
    return subs


def _harvest_names(domain: str, client: httpx.Client) -> set[str]:
    names: set[str] = set()
    html = _ddg_search(f'site:linkedin.com "{domain}"', client)
    if not html:
        return names
    soup = BeautifulSoup(html, "html.parser")
    for result in soup.find_all("a", class_="result__a"):
        text = result.get_text(strip=True)
        # LinkedIn results often: "Name | Title | Company"
        if "|" in text:
            name_part = text.split("|")[0].strip()
            if 3 < len(name_part) < 50 and " " in name_part:
                names.add(name_part)
    return names


def harvest(
    domain: Annotated[str, typer.Argument(help="Target domain (e.g. example.com).")],
    json_out: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
    timeout: Annotated[float, typer.Option("--timeout", help="Request timeout in seconds.")] = 15.0,
) -> None:
    """
    Collect publicly available info about a domain.

    Gathers emails, subdomains, and employee names from public sources only.
    This tool only uses public information — use responsibly.

    Examples:
      devha harvest example.com
      devha harvest github.com --json
    """
    warn("This tool only collects [bold]publicly available[/bold] information. Use responsibly.")
    info(f"Harvesting public info for [cyan]{domain}[/cyan]...\n")

    with httpx.Client(follow_redirects=True) as client:
        emails = _harvest_emails(domain, client)
        subs = _harvest_subdomains_crt(domain, client)
        names = _harvest_names(domain, client)

    if json_out:
        console.print_json(json.dumps({
            "domain": domain,
            "emails": sorted(emails),
            "subdomains": sorted(subs),
            "names": sorted(names),
        }))
        return

    def _panel(title: str, items: set[str], style: str = "cyan") -> None:
        if not items:
            console.print(f"[dim]{title}: nothing found[/dim]")
            return
        content = Text()
        for item in sorted(items)[:100]:
            content.append(f"  • {item}\n")
        print_panel(content, title=f"{title} ({len(items)})", style=style)

    _panel("Emails", emails, "bright_green")
    _panel("Subdomains", subs, "blue")
    _panel("Employee Names (LinkedIn snippets)", names, "magenta")

    console.print(
        "\n[dim]⚠  All data sourced from public internet (DuckDuckGo, crt.sh). "
        "No credentials or private systems accessed.[/dim]"
    )

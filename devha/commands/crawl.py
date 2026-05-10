"""Crawl command — website crawler that extracts emails, links, and potential secrets."""

from __future__ import annotations

import json
import re
import urllib.robotparser
from collections import defaultdict
from typing import Annotated
from urllib.parse import urljoin, urlparse

import httpx
import typer
from bs4 import BeautifulSoup
from rich.text import Text

from devha.ui import console, print_panel, warn, info, error
from devha.ethics import ethics_check

# Patterns
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?\d[\d\s\-().]{7,}\d)")
_API_KEY_RE = re.compile(r"['\"]([A-Za-z0-9_\-]{32,64})['\"]")
_SOCIAL_DOMAINS = {"twitter.com", "x.com", "linkedin.com", "facebook.com", "instagram.com",
                   "github.com", "youtube.com", "tiktok.com"}


def _same_origin(base: str, href: str) -> bool:
    b = urlparse(base)
    h = urlparse(href)
    return h.netloc == "" or h.netloc == b.netloc


def _can_fetch(rp: urllib.robotparser.RobotFileParser, url: str) -> bool:
    return rp.can_fetch("*", url)


def _load_robots(base_url: str, client: httpx.Client) -> urllib.robotparser.RobotFileParser:
    rp = urllib.robotparser.RobotFileParser()
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        resp = client.get(robots_url, timeout=5.0)
        rp.parse(resp.text.splitlines())
    except httpx.RequestError:
        pass
    return rp


def crawl(
    url: Annotated[str, typer.Argument(help="Target URL to crawl.")],
    depth: Annotated[int, typer.Option("--depth", "-d", help="Maximum crawl depth.")] = 2,
    ignore_robots: Annotated[bool, typer.Option("--ignore-robots", help="Ignore robots.txt (use responsibly!).")] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip ethics confirmation.")] = False,
    json_out: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
    timeout: Annotated[float, typer.Option("--timeout", help="Request timeout in seconds.")] = 10.0,
) -> None:
    """
    Crawl a website and extract emails, links, phone numbers, and API key patterns.

    Examples:
      devha crawl https://example.com
      devha crawl https://target.local --depth 3
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    host = urlparse(url).netloc
    ethics_check(host, yes=yes)

    if ignore_robots:
        warn("--ignore-robots active. Ensure you have permission to crawl this site.")

    info(f"Crawling [cyan]{url}[/cyan]  depth=[cyan]{depth}[/cyan]")

    found: dict[str, set[str]] = defaultdict(set)
    visited: set[str] = set()
    queue = [(url, 0)]

    headers = {"User-Agent": "devha/0.1 crawler (educational)"}

    with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as client:
        rp = _load_robots(url, client) if not ignore_robots else None

        while queue:
            current_url, current_depth = queue.pop(0)
            if current_url in visited or current_depth > depth:
                continue
            visited.add(current_url)

            if rp and not _can_fetch(rp, current_url):
                warn(f"robots.txt blocks: {current_url}")
                continue

            try:
                resp = client.get(current_url)
                content_type = resp.headers.get("content-type", "")
            except httpx.RequestError:
                continue

            if "text/html" in content_type:
                soup = BeautifulSoup(resp.text, "html.parser")
                text = resp.text

                # Extract emails
                for email in _EMAIL_RE.findall(text):
                    found["emails"].add(email)

                # Extract phone numbers (basic)
                for phone in _PHONE_RE.findall(text):
                    cleaned = phone.strip()
                    if len(cleaned) >= 9:
                        found["phones"].add(cleaned)

                # Extract links
                for tag in soup.find_all("a", href=True):
                    href = urljoin(current_url, tag["href"])
                    if href.startswith("http"):
                        parsed = urlparse(href)
                        if parsed.netloc in _SOCIAL_DOMAINS:
                            found["social"].add(href)
                        elif not _same_origin(url, href):
                            found["external_links"].add(href)
                        elif current_depth < depth:
                            queue.append((href, current_depth + 1))

            elif "javascript" in content_type or current_url.endswith(".js"):
                text = resp.text
                for key in _API_KEY_RE.findall(text):
                    found["potential_keys"].add(key)

    # Convert sets to sorted lists for output
    result_dict = {k: sorted(v) for k, v in found.items()}

    if json_out:
        console.print_json(json.dumps({"url": url, "pages_crawled": len(visited), "results": result_dict}))
        return

    console.print(f"\n[blue]Crawled[/blue] [cyan]{len(visited)}[/cyan] page(s)\n")

    def _render_panel(title: str, items: list[str], style: str = "cyan") -> None:
        if not items:
            return
        content = Text()
        for item in items[:50]:
            content.append(f"  • {item}\n")
        if len(items) > 50:
            content.append(f"  … and {len(items) - 50} more\n", style="dim")
        print_panel(content, title=f"{title} ({len(items)})", style=style)

    _render_panel("Emails", result_dict.get("emails", []), "bright_green")
    _render_panel("Phone Numbers", result_dict.get("phones", []), "blue")
    _render_panel("Social Links", result_dict.get("social", []), "magenta")
    _render_panel("External Links", result_dict.get("external_links", []), "cyan")

    keys = result_dict.get("potential_keys", [])
    if keys:
        warn("Potential API key patterns found (may be false positives):")
        _render_panel("Potential API Keys", keys, "yellow")

    if not any(result_dict.values()):
        console.print("[yellow]Nothing extracted.[/yellow]")

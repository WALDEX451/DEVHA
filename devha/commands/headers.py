"""Headers command — HTTP header inspector and security audit."""

from __future__ import annotations

import json
from typing import Annotated

import httpx
import typer
from rich.text import Text

from devha.ui import console, make_table, print_panel, error, info

_SECURITY_HEADERS = [
    "content-security-policy",
    "strict-transport-security",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
]

_HEADER_DESCRIPTIONS = {
    "content-security-policy": "Prevents XSS and data injection attacks",
    "strict-transport-security": "Forces HTTPS connections (HSTS)",
    "x-content-type-options": "Prevents MIME-type sniffing",
    "x-frame-options": "Prevents clickjacking attacks",
    "referrer-policy": "Controls referrer information leakage",
    "permissions-policy": "Controls browser feature access",
}


def headers(
    url: Annotated[str, typer.Argument(help="Target URL (include https://).")],
    json_out: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
    timeout: Annotated[float, typer.Option("--timeout", help="Request timeout in seconds.")] = 10.0,
) -> None:
    """
    Inspect HTTP headers and audit security headers.

    Examples:
      devha headers https://example.com
      devha headers https://github.com --json
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    info(f"Fetching headers from [cyan]{url}[/cyan]...")

    try:
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            resp = client.get(url)
    except httpx.RequestError as exc:
        error(f"Request failed: {exc}")
        raise typer.Exit(1)

    all_headers = dict(resp.headers)
    lower_headers = {k.lower(): v for k, v in all_headers.items()}

    present = [h for h in _SECURITY_HEADERS if h in lower_headers]
    missing = [h for h in _SECURITY_HEADERS if h not in lower_headers]
    score = len(present)
    total = len(_SECURITY_HEADERS)

    if json_out:
        console.print_json(json.dumps({
            "url": url,
            "status_code": resp.status_code,
            "headers": all_headers,
            "security_score": f"{score}/{total}",
            "present": present,
            "missing": missing,
        }))
        return

    # All headers table
    hdr_table = make_table("HEADER", "VALUE", title=f"Response Headers — {url}")
    for k, v in all_headers.items():
        display_val = v if len(v) <= 80 else v[:77] + "..."
        style = "bright_green" if k.lower() in _SECURITY_HEADERS else "white"
        hdr_table.add_row(f"[{style}]{k}[/{style}]", display_val)
    console.print(hdr_table)

    # Security audit panel
    score_color = "bright_green" if score >= 5 else "yellow" if score >= 3 else "bright_red"
    score_text = Text()
    score_text.append(f"Security Score: {score}/{total}  ", style="bold")
    score_text.append("★" * score + "☆" * (total - score), style=score_color)
    score_text.append("\n")

    if present:
        score_text.append("\n✔  Present:\n", style="bright_green bold")
        for h in present:
            score_text.append(f"   • {h}\n", style="bright_green")

    if missing:
        score_text.append("\n✘  Missing:\n", style="bright_red bold")
        for h in missing:
            desc = _HEADER_DESCRIPTIONS.get(h, "")
            score_text.append(f"   • {h}", style="bright_red")
            score_text.append(f"  — {desc}\n", style="dim")

    print_panel(score_text, title="Security Audit", style=score_color)

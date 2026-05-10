"""Web Vulnerability Scanner — exposed files, misconfigs, security headers."""

from __future__ import annotations

import asyncio
import json
from typing import Annotated
from urllib.parse import urljoin, urlparse

import httpx
import typer

from devha.ui import console, make_table, info, warn, error, success


def webvuln(
    url: Annotated[str, typer.Argument(help="Target URL (only scan sites you own).")],
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    Web vulnerability scanner — exposed files, CORS, headers, info leaks.

    Checks: .env, .git, phpinfo, backup files, security headers,
    server version disclosure, CORS wildcard, directory listing.

    ⚠ Only scan sites you own or have explicit permission to test!

    Example:
      devha webvuln https://example.com
    """
    if not url.startswith("http"):
        url = "https://" + url

    info(f"Scanning [cyan]{url}[/cyan]...")
    warn("⚡ Only scan sites you own or have explicit permission to test!")
    console.print()

    findings = asyncio.run(_run_checks(url))

    if json_out:
        console.print_json(json.dumps({"url": url, "findings": findings}))
        return

    if not findings:
        success("No issues found.")
        return

    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    findings.sort(key=lambda f: order.get(f["severity"], 9))

    table = make_table("SEVERITY", "FINDING", "DETAIL", title=f"🕸️  Web Vuln Scan — {url}")
    styles = {"HIGH": "bright_red bold", "MEDIUM": "yellow", "LOW": "cyan", "INFO": "dim"}
    for f in findings:
        s = styles.get(f["severity"], "white")
        table.add_row(f"[{s}]{f['severity']}[/{s}]", f["name"], f["detail"][:80])
    console.print(table)

    counts = {k: sum(1 for f in findings if f["severity"] == k) for k in ("HIGH", "MEDIUM", "LOW", "INFO")}
    console.print(
        f"\n[bright_red bold]HIGH: {counts['HIGH']}[/bright_red bold]  "
        f"[yellow]MEDIUM: {counts['MEDIUM']}[/yellow]  "
        f"[cyan]LOW: {counts['LOW']}[/cyan]  "
        f"[dim]INFO: {counts['INFO']}[/dim]"
    )


async def _run_checks(url: str) -> list[dict]:
    findings: list[dict] = []

    async with httpx.AsyncClient(
        timeout=10,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (devha security scanner — authorized use only)"},
    ) as client:
        try:
            resp = await client.get(url)
        except Exception as e:
            error(f"Cannot reach {url}: {e}")
            return []

        headers = {k.lower(): v for k, v in resp.headers.items()}
        body = resp.text.lower()

        # Security headers
        missing_headers = [
            ("strict-transport-security", "MEDIUM", "Missing HSTS — HTTPS not enforced"),
            ("content-security-policy",   "MEDIUM", "Missing CSP — XSS protection absent"),
            ("x-frame-options",           "MEDIUM", "Missing X-Frame-Options — clickjacking risk"),
            ("x-content-type-options",    "LOW",    "Missing X-Content-Type-Options"),
            ("referrer-policy",           "LOW",    "Missing Referrer-Policy"),
            ("permissions-policy",        "LOW",    "Missing Permissions-Policy"),
        ]
        for h, sev, desc in missing_headers:
            if h not in headers:
                findings.append({"severity": sev, "name": f"Missing: {h}", "detail": desc})

        # Server version disclosure
        server = headers.get("server", "")
        if server and any(v in server.lower() for v in ["apache/", "nginx/", "iis/", "lighttpd/"]):
            findings.append({"severity": "LOW", "name": "Server Version Exposed", "detail": f"Server: {server}"})

        if headers.get("x-powered-by"):
            findings.append({"severity": "LOW", "name": "X-Powered-By Exposed", "detail": headers["x-powered-by"]})

        # CORS
        cors = headers.get("access-control-allow-origin", "")
        if cors == "*":
            findings.append({"severity": "MEDIUM", "name": "Wildcard CORS", "detail": "Any origin can read responses — possible data theft"})

        # Directory listing
        if "<title>index of" in body or "directory listing for" in body:
            findings.append({"severity": "HIGH", "name": "Directory Listing Enabled", "detail": "Server exposes file/directory listings"})

        # Error disclosure
        for pattern in ["stack trace", "sql syntax", "mysql_query", "pg_query", "ora-0", "exception in thread", "traceback (most recent"]:
            if pattern in body:
                findings.append({"severity": "MEDIUM", "name": "Error Info Disclosure", "detail": f"Pattern '{pattern}' found in response"})
                break

        # robots.txt info
        base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        try:
            r = await client.get(f"{base}/robots.txt")
            if r.status_code == 200:
                disallowed = [l.split(":",1)[1].strip() for l in r.text.splitlines() if l.lower().startswith("disallow:") and l.split(":",1)[1].strip() not in ("/", "")]
                if disallowed:
                    findings.append({"severity": "INFO", "name": "robots.txt reveals paths", "detail": f"Disallowed: {', '.join(disallowed[:5])}"})
        except Exception:
            pass

        # Sensitive files
        sensitive = [
            (".env",               "HIGH",   "Environment file — may contain passwords/API keys"),
            (".git/config",        "HIGH",   "Git repo exposed — source code accessible"),
            (".git/HEAD",          "HIGH",   "Git repo exposed — source code accessible"),
            ("wp-config.php.bak",  "HIGH",   "WordPress config backup"),
            ("config.php.bak",     "HIGH",   "PHP config backup"),
            ("backup.zip",         "HIGH",   "Backup archive accessible"),
            ("backup.tar.gz",      "HIGH",   "Backup archive accessible"),
            ("database.sql",       "HIGH",   "SQL dump accessible"),
            ("phpinfo.php",        "MEDIUM", "PHP info page — server config exposed"),
            (".htaccess",          "MEDIUM", "htaccess file readable"),
            ("server-status",      "MEDIUM", "Apache server-status exposed"),
            ("admin/",             "INFO",   "Admin panel path accessible"),
            ("administrator/",     "INFO",   "Admin panel path accessible"),
            ("phpmyadmin/",        "MEDIUM", "phpMyAdmin exposed"),
            ("test.php",           "LOW",    "Test file accessible"),
            ("readme.txt",         "LOW",    "README exposed — version info"),
            ("README.md",          "LOW",    "README exposed — version info"),
            ("CHANGELOG.md",       "LOW",    "CHANGELOG — version info"),
            ("composer.json",      "LOW",    "composer.json — dependency info"),
            ("package.json",       "LOW",    "package.json — dependency info"),
            (".DS_Store",          "LOW",    ".DS_Store — macOS metadata, dir structure leak"),
        ]

        tasks = [_probe(client, base, path, sev, desc) for path, sev, desc in sensitive]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        findings.extend(r for r in results if isinstance(r, dict))

    return findings


async def _probe(client: httpx.AsyncClient, base: str, path: str, severity: str, desc: str) -> dict | None:
    try:
        r = await client.get(urljoin(base + "/", path))
        if r.status_code == 200 and len(r.content) > 10:
            return {"severity": severity, "name": f"Exposed: /{path}", "detail": desc}
    except Exception:
        pass
    return None

"""WHOIS / RDAP lookup — domain registration info."""

from __future__ import annotations

import json
import subprocess
from typing import Annotated

import httpx
import typer

from devha.ui import console, make_table, info, warn, error


def whois_lookup(
    target: Annotated[str, typer.Argument(help="Domain or IP (e.g. example.com, 8.8.8.8).")],
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    WHOIS / RDAP lookup — registrar, creation date, expiry, nameservers.

    Example:
      devha whois google.com
      devha whois 8.8.8.8
    """
    target = target.lstrip("www.").strip()
    info(f"WHOIS lookup for [cyan]{target}[/cyan]...")

    data = _rdap_lookup(target)

    if data:
        if json_out:
            console.print_json(json.dumps(data))
            return
        table = make_table("FIELD", "VALUE", title=f"🔎 WHOIS — {target}")
        for k, v in data.items():
            if v:
                table.add_row(f"[cyan]{k}[/cyan]", str(v)[:120])
        console.print(table)
    else:
        _system_whois(target)


def _rdap_lookup(domain: str) -> dict | None:
    try:
        resp = httpx.get(f"https://rdap.org/domain/{domain}", timeout=10, follow_redirects=True)
        if resp.status_code != 200:
            return None
        raw = resp.json()
    except Exception:
        return None

    data: dict[str, str] = {}
    data["Domain"] = raw.get("ldhName", domain).upper()
    data["Status"] = ", ".join(raw.get("status", []))

    for event in raw.get("events", []):
        action = event.get("eventAction", "")
        date   = event.get("eventDate", "")[:10]
        if action == "registration":
            data["Created"] = date
        elif action == "expiration":
            data["Expires"] = date
        elif action == "last changed":
            data["Updated"] = date

    for entity in raw.get("entities", []):
        roles = entity.get("roles", [])
        vcard = entity.get("vcardArray", [])
        name = ""
        if isinstance(vcard, list) and len(vcard) > 1:
            for field in vcard[1]:
                if isinstance(field, list) and len(field) >= 4 and field[0] == "fn":
                    name = str(field[3])
        if "registrar" in roles and name:
            data["Registrar"] = name
        elif "registrant" in roles and name:
            data["Registrant"] = name

    ns_list = [n.get("ldhName", "") for n in raw.get("nameservers", [])]
    data["Nameservers"] = ", ".join(ns_list[:6])

    return {k: v for k, v in data.items() if v}


def _system_whois(target: str) -> None:
    try:
        result = subprocess.run(["whois", target], capture_output=True, text=True, timeout=15)
        output = result.stdout or result.stderr
        if not output:
            error("No whois output returned.")
            return
        keep_keys = ["domain", "registrar", "created", "creat", "expir", "updated", "nameserver", "status", "registrant", "dnssec", "org", "netrange", "cidr", "country"]
        useful = []
        for line in output.splitlines():
            ls = line.strip()
            if not ls or ls.startswith("%") or ls.startswith("#") or ls.startswith(">>>"):
                continue
            if any(k in ls.lower() for k in keep_keys):
                useful.append(ls)
        console.print("\n".join(useful[:35]) if useful else output[:1500])
    except FileNotFoundError:
        error("'whois' command not available. Install: brew install whois")
    except Exception as e:
        error(f"whois error: {e}")

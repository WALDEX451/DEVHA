"""Wifi command — list nearby Wi-Fi networks (read-only)."""

from __future__ import annotations

import json
import platform
import re
import subprocess
from typing import Annotated

import typer

from devha.ui import console, make_table, error, warn, info


def _run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def _parse_linux() -> list[dict]:
    """Try nmcli first, fall back to iwlist."""
    networks = []

    # nmcli approach
    out = _run(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,CHAN,BSSID", "device", "wifi", "list"])
    if out.strip():
        for line in out.strip().splitlines():
            parts = line.split(":")
            if len(parts) >= 4:
                networks.append({
                    "ssid": parts[0] or "<hidden>",
                    "signal": parts[1],
                    "security": parts[2] or "Open",
                    "channel": parts[3] if len(parts) > 3 else "?",
                })
        return networks

    # iwlist fallback
    out = _run(["iwlist", "scan"])
    if not out:
        return []

    cells = re.split(r"Cell \d+", out)
    for cell in cells[1:]:
        ssid_m = re.search(r'ESSID:"([^"]*)"', cell)
        signal_m = re.search(r"Signal level[=:](-?\d+)", cell)
        enc_m = re.search(r"Encryption key:(on|off)", cell, re.IGNORECASE)
        chan_m = re.search(r"Channel[:\s]+(\d+)", cell)
        networks.append({
            "ssid": ssid_m.group(1) if ssid_m else "<hidden>",
            "signal": signal_m.group(1) if signal_m else "?",
            "security": "WPA/WEP" if enc_m and enc_m.group(1).lower() == "on" else "Open",
            "channel": chan_m.group(1) if chan_m else "?",
        })
    return networks


def _parse_macos() -> list[dict]:
    airport = (
        "/System/Library/PrivateFrameworks/Apple80211.framework"
        "/Versions/Current/Resources/airport"
    )
    out = _run([airport, "-s"])
    if not out:
        return []

    networks = []
    for line in out.strip().splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 5:
            networks.append({
                "ssid": parts[0],
                "signal": parts[2],
                "security": parts[-1] if len(parts) > 4 else "?",
                "channel": parts[3] if len(parts) > 3 else "?",
            })
    return networks


def _parse_windows() -> list[dict]:
    out = _run(["netsh", "wlan", "show", "networks", "mode=Bssid"])
    if not out:
        return []

    networks = []
    current: dict = {}
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("SSID") and "BSSID" not in line:
            if current:
                networks.append(current)
            current = {"ssid": line.split(":", 1)[-1].strip(), "signal": "?", "security": "?", "channel": "?"}
        elif "Signal" in line and current:
            current["signal"] = line.split(":", 1)[-1].strip()
        elif "Authentication" in line and current:
            current["security"] = line.split(":", 1)[-1].strip()
        elif "Channel" in line and current:
            current["channel"] = line.split(":", 1)[-1].strip()
    if current:
        networks.append(current)
    return networks


def _signal_sort_key(net: dict) -> int:
    try:
        return -int(net["signal"].replace("%", "").strip())
    except (ValueError, AttributeError):
        return 0


def wifi(
    json_out: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
) -> None:
    """
    List nearby Wi-Fi networks (read-only — does not connect or crack).

    Examples:
      devha wifi
      devha wifi --json
    """
    os_name = platform.system()
    info(f"Scanning Wi-Fi networks on [cyan]{os_name}[/cyan]...")

    if os_name == "Linux":
        networks = _parse_linux()
    elif os_name == "Darwin":
        networks = _parse_macos()
    elif os_name == "Windows":
        networks = _parse_windows()
    else:
        error(f"Unsupported OS: {os_name}")
        raise typer.Exit(1)

    if not networks:
        warn("No networks found. Are Wi-Fi adapters available and enabled?")
        warn("Linux users: try running with sudo, or check 'nmcli' / 'iwlist' availability.")
        raise typer.Exit(0)

    networks.sort(key=_signal_sort_key)

    if json_out:
        console.print_json(json.dumps({"os": os_name, "networks": networks}))
        return

    table = make_table("SSID", "SIGNAL", "SECURITY", "CHANNEL", title="Nearby Wi-Fi Networks")
    for net in networks:
        ssid = net["ssid"] or "[dim]<hidden>[/dim]"
        security = net["security"]
        sec_style = "bright_green" if security == "Open" else "yellow"
        table.add_row(
            f"[cyan]{ssid}[/cyan]",
            str(net["signal"]),
            f"[{sec_style}]{security}[/{sec_style}]",
            str(net["channel"]),
        )
    console.print(table)
    console.print(f"\n[dim]Read-only scan — {len(networks)} network(s) found. "
                  "devha does not connect or crack networks.[/dim]")

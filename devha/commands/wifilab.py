"""WiFi Lab — scan, map devices, test own network security."""

from __future__ import annotations

import json
import os
import platform
import re
import socket
import subprocess
import time
from typing import Annotated

import typer
from rich.progress import Progress, SpinnerColumn, BarColumn, TimeElapsedColumn
from rich.text import Text

from devha.ui import console, make_table, print_panel, info, warn, error, success

app = typer.Typer(help="📡 WiFi Lab — scan networks, map devices, test your own AP security.")


# ─── Helpers ───────────────────────────────────────────────────────────────

def _run(cmd: list[str], timeout: int = 15) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout + r.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def _vendor_from_mac(mac: str) -> str:
    oui_map = {
        "00:50:56": "VMware", "00:0c:29": "VMware", "08:00:27": "VirtualBox",
        "b8:27:eb": "Raspberry Pi", "dc:a6:32": "Raspberry Pi", "e4:5f:01": "Raspberry Pi",
        "fc:fb:fb": "Cisco", "00:1a:2b": "Cisco",
        "ac:37:43": "Apple", "f8:ff:c2": "Apple", "3c:15:c2": "Apple",
        "28:d2:44": "Samsung", "98:01:a7": "Apple",
    }
    prefix = mac[:8].lower().replace("-", ":")
    return oui_map.get(prefix, "Unknown")


# ─── Commands ───────────────────────────────────────────────────────────────

@app.command("scan")
def scan_networks(
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Scan nearby WiFi networks and show signal strength."""
    info("Scanning WiFi networks...")

    os_name = platform.system()
    networks = []

    if os_name == "Linux":
        out = _run(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,CHAN,BSSID", "device", "wifi", "list"])
        for line in out.strip().splitlines():
            parts = line.split(":")
            if len(parts) >= 3:
                networks.append({
                    "ssid": parts[0] or "<hidden>",
                    "signal": parts[1],
                    "security": parts[2] or "Open",
                    "channel": parts[3] if len(parts) > 3 else "?",
                    "bssid": parts[4] if len(parts) > 4 else "?",
                })
    elif os_name == "Darwin":
        # Try airport binary
        airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        out = _run([airport, "-s"])
        if not out.strip():
            # Fallback: system_profiler
            out2 = _run(["system_profiler", "SPAirPortDataType"])
            if out2:
                console.print("[dim]Using system_profiler (airport binary unavailable)...[/dim]")
                for line in out2.splitlines():
                    line = line.strip()
                    if line.startswith("Other Local Wi-Fi Networks:") or ("Network Name" in line):
                        pass
                    m = re.match(r"^([^:]+):$", line)
                    if m and len(m.group(1)) < 40:
                        networks.append({"ssid": m.group(1), "signal": "?", "security": "?", "channel": "?", "bssid": "?"})
        else:
            for line in out.strip().splitlines()[1:]:
                p = line.split()
                if len(p) >= 5:
                    networks.append({"ssid": p[0], "signal": p[2], "security": p[-1], "channel": p[3], "bssid": p[1]})
    elif os_name == "Windows":
        out = _run(["netsh", "wlan", "show", "networks", "mode=Bssid"])
        current: dict = {}
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("SSID") and "BSSID" not in line:
                if current:
                    networks.append(current)
                current = {"ssid": line.split(":", 1)[-1].strip(), "signal": "?", "security": "?", "channel": "?", "bssid": "?"}
            elif "Signal" in line and current:
                current["signal"] = line.split(":", 1)[-1].strip()
            elif "Authentication" in line and current:
                current["security"] = line.split(":", 1)[-1].strip()
            elif "BSSID" in line and current:
                current["bssid"] = line.split(":", 1)[-1].strip()
        if current:
            networks.append(current)

    if not networks:
        warn("No networks found. On macOS, WiFi scanning may require location permissions or sudo.")
        console.print("[dim]Try: sudo devha wifilab scan[/dim]")
        return

    networks.sort(key=lambda x: -int(x["signal"].replace("%", "").strip()) if x["signal"].replace("%", "").strip().lstrip("-").isdigit() else 0)

    if json_out:
        console.print_json(json.dumps(networks))
        return

    table = make_table("SSID", "SIGNAL", "SECURITY", "CHANNEL", "BSSID", title="📡 WiFi Networks")
    for n in networks:
        sig = n["signal"]
        sec = n["security"]
        sec_style = "bright_red bold" if sec == "Open" else "bright_green" if "WPA3" in sec else "yellow"
        bar = _signal_bar(sig)
        table.add_row(
            f"[cyan]{n['ssid']}[/cyan]",
            f"[dim]{bar}[/dim] {sig}",
            f"[{sec_style}]{sec}[/{sec_style}]",
            n["channel"],
            f"[dim]{n['bssid']}[/dim]",
        )
    console.print(table)
    console.print(f"\n[dim]⚡ {len(networks)} networks found — read-only scan[/dim]")


def _signal_bar(sig: str) -> str:
    try:
        val = int(sig.replace("%", "").strip())
        val = val if val > 0 else 100 + val
        blocks = int(val / 20)
        return "█" * blocks + "░" * (5 - blocks)
    except Exception:
        return "░░░░░"


@app.command("devices")
def scan_devices(
    subnet: Annotated[str, typer.Option("--subnet", "-s", help="Subnet to scan, e.g. 192.168.1.0/24")] = "",
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    Discover all devices on your local network using ARP.

    Requires root. Run: sudo devha wifilab devices
    """
    if os.geteuid() != 0:
        error("Device scan requires root. Run: [bold]sudo devha wifilab devices[/bold]")
        raise typer.Exit(1)

    try:
        from scapy.all import ARP, Ether, srp, conf as scapy_conf  # type: ignore[import]
        scapy_conf.verb = 0
    except ImportError:
        error("Scapy not installed.")
        raise typer.Exit(1)

    if not subnet:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        subnet = ".".join(local_ip.split(".")[:3]) + ".0/24"

    info(f"ARP scanning [cyan]{subnet}[/cyan]...")

    arp = ARP(pdst=subnet)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether / arp

    with Progress(SpinnerColumn(), "[cyan]Scanning...", TimeElapsedColumn(), console=console) as p:
        p.add_task("scan", total=None)
        answered, _ = srp(packet, timeout=3, retry=1)

    devices = []
    for _, recv in answered:
        mac = recv.hwsrc
        ip = recv.psrc
        vendor = _vendor_from_mac(mac)
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except socket.herror:
            hostname = "?"
        devices.append({"ip": ip, "mac": mac, "vendor": vendor, "hostname": hostname})

    devices.sort(key=lambda x: [int(p) for p in x["ip"].split(".")])

    if json_out:
        console.print_json(json.dumps({"subnet": subnet, "devices": devices}))
        return

    table = make_table("IP", "MAC", "VENDOR", "HOSTNAME", title=f"🖥️  Devices on {subnet}")
    for d in devices:
        table.add_row(
            f"[cyan]{d['ip']}[/cyan]",
            f"[dim]{d['mac']}[/dim]",
            f"[yellow]{d['vendor']}[/yellow]",
            d["hostname"],
        )
    console.print(table)
    console.print(f"\n[bright_green]Found {len(devices)} device(s) on {subnet}.[/bright_green]")


@app.command("security")
def security_check(
    target: Annotated[str, typer.Argument(help="Router IP, e.g. 192.168.1.1")] = "192.168.1.1",
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    Check your router/AP for common security weaknesses.

    Example:
      devha wifilab security 192.168.1.1
    """
    import socket as _socket
    info(f"Security checking [cyan]{target}[/cyan]...")

    checks = []

    dangerous_ports = {
        23: ("Telnet", "HIGH — unencrypted admin access"),
        80: ("HTTP admin", "MEDIUM — check if default password is set"),
        443: ("HTTPS admin", "LOW — encrypted, but change default password"),
        8080: ("HTTP alt", "MEDIUM — alternative HTTP admin panel"),
        8443: ("HTTPS alt", "LOW"),
        21: ("FTP", "HIGH — unencrypted file access"),
        22: ("SSH", "LOW — encrypted, ensure strong password"),
    }

    for port, (svc, risk) in dangerous_ports.items():
        try:
            with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as s:
                s.settimeout(1.0)
                open_ = s.connect_ex((target, port)) == 0
        except OSError:
            open_ = False
        if open_:
            checks.append({"port": port, "service": svc, "risk": risk, "status": "OPEN"})

    try:
        import httpx
        r = httpx.get(f"http://{target}", timeout=3, follow_redirects=True)
        body = r.text.lower()
        if any(w in body for w in ["password", "username", "login", "admin"]):
            checks.append({"port": 80, "service": "HTTP Login Page", "risk": "MEDIUM — check default credentials", "status": "DETECTED"})
    except Exception:
        pass

    if json_out:
        console.print_json(json.dumps({"target": target, "findings": checks}))
        return

    if not checks:
        success(f"No common vulnerabilities found on {target}")
        return

    table = make_table("PORT", "SERVICE", "STATUS", "RISK", title=f"🛡️  Security Check — {target}")
    for c in checks:
        risk = c["risk"]
        risk_style = "bright_red" if "HIGH" in risk else "yellow" if "MEDIUM" in risk else "dim"
        table.add_row(
            f"[cyan]{c['port']}[/cyan]",
            c["service"],
            f"[bright_red]{c['status']}[/bright_red]",
            f"[{risk_style}]{risk}[/{risk_style}]",
        )
    console.print(table)
    console.print("\n[dim]⚡ Tested against your own router only — change defaults immediately[/dim]")


@app.command("deauth-test")
def deauth_test(
    bssid: Annotated[str, typer.Argument(help="Your own AP BSSID (MAC address), e.g. AA:BB:CC:DD:EE:FF")],
    client: Annotated[str, typer.Option("--client", "-c", help="Client MAC (default: broadcast)")] = "ff:ff:ff:ff:ff:ff",
    count: Annotated[int, typer.Option("--count", "-n", help="Number of deauth frames.")] = 5,
    iface: Annotated[str, typer.Option("--iface", "-i", help="Wireless interface in monitor mode.")] = "wlan0mon",
) -> None:
    """
    Send deauth frames to YOUR OWN access point to test its resilience.

    Requires monitor mode + root.
    Setup: sudo airmon-ng start wlan0

    Example:
      sudo devha wifilab deauth-test AA:BB:CC:DD:EE:FF --iface wlan0mon
    """
    if os.geteuid() != 0:
        error("Deauth test requires root: sudo devha wifilab deauth-test ...")
        raise typer.Exit(1)

    warn("⚡ Deauth test — YOUR OWN AP only. Illegal on others' networks.")

    try:
        from scapy.all import RadioTap, Dot11, Dot11Deauth, sendp, conf as scapy_conf  # type: ignore[import]
        scapy_conf.verb = 0
    except ImportError:
        error("Scapy not installed.")
        raise typer.Exit(1)

    info(f"Sending {count} deauth frames to [cyan]{bssid}[/cyan] via [cyan]{iface}[/cyan]...")

    pkt = (
        RadioTap()
        / Dot11(addr1=client, addr2=bssid, addr3=bssid)
        / Dot11Deauth(reason=7)
    )

    with Progress(SpinnerColumn(), "[cyan]Sending deauth frames...", BarColumn(), TimeElapsedColumn(), console=console) as p:
        task = p.add_task("send", total=count)
        for i in range(count):
            sendp(pkt, iface=iface, count=1, inter=0.1)
            p.advance(task)

    success(f"Sent {count} deauth frames to {bssid}.")
    console.print("[dim]If your own devices disconnected — your AP responded correctly to deauth.[/dim]")
    console.print("[dim]Enable 802.11w (Management Frame Protection) on your router to block this.[/dim]")

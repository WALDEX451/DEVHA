"""Packet Lab — live capture, ARP scan, TCP builder (your network only)."""

from __future__ import annotations

import json
import os
import socket
import time
from collections import defaultdict
from typing import Annotated

import typer
from rich.live import Live
from rich.table import Table
from rich import box

from devha.ui import console, make_table, print_panel, info, warn, error, success

app = typer.Typer(help="📦 Packet Lab — capture, ARP scan, and build packets on your own network.")


def _need_root() -> None:
    if os.geteuid() != 0:
        error("Packet Lab requires root. Run: sudo devha packetlab <command>")
        raise typer.Exit(1)


def _get_scapy():
    try:
        from scapy.all import (  # type: ignore[import]
            sniff, ARP, IP, TCP, UDP, ICMP, Ether, Raw,
            get_if_list, conf as scapy_conf,
        )
        scapy_conf.verb = 0
        return sniff, ARP, IP, TCP, UDP, ICMP, Ether, Raw, get_if_list
    except ImportError:
        error("Scapy not installed.")
        raise typer.Exit(1)


# ─── Commands ──────────────────────────────────────────────────────────────────

@app.command("capture")
def capture(
    iface: Annotated[str, typer.Option("--iface", "-i", help="Network interface to capture on.")] = "",
    count: Annotated[int, typer.Option("--count", "-c", help="Number of packets to capture (0 = infinite).")] = 50,
    proto_filter: Annotated[str, typer.Option("--filter", "-f", help="Protocol filter: tcp, udp, icmp, arp, all.")] = "all",
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    Capture live packets on your network interface.

    Only captures on your own network. Shows src, dst, protocol, size.

    Example:
      sudo devha packetlab capture --count 20
      sudo devha packetlab capture --filter tcp --iface eth0
    """
    _need_root()
    sniff, ARP, IP, TCP, UDP, ICMP, Ether, Raw, get_if_list = _get_scapy()

    bpf = "" if proto_filter == "all" else proto_filter
    iface_arg = iface or None

    captured = []

    def packet_handler(pkt):
        rec = {"time": time.strftime("%H:%M:%S"), "proto": "?", "src": "?", "dst": "?", "len": len(pkt), "info": ""}
        if pkt.haslayer(IP):
            rec["src"] = pkt[IP].src
            rec["dst"] = pkt[IP].dst
        if pkt.haslayer(TCP):
            rec["proto"] = "TCP"
            rec["info"] = f"port {pkt[TCP].sport}→{pkt[TCP].dport} [{_tcp_flags(pkt[TCP].flags)}]"
        elif pkt.haslayer(UDP):
            rec["proto"] = "UDP"
            rec["info"] = f"port {pkt[UDP].sport}→{pkt[UDP].dport}"
        elif pkt.haslayer(ICMP):
            rec["proto"] = "ICMP"
            rec["info"] = f"type={pkt[ICMP].type}"
        elif pkt.haslayer(ARP):
            rec["proto"] = "ARP"
            rec["src"] = pkt[ARP].psrc
            rec["dst"] = pkt[ARP].pdst
            rec["info"] = "who-has" if pkt[ARP].op == 1 else "is-at"
        else:
            rec["proto"] = pkt.name
        captured.append(rec)

    info(f"Capturing [cyan]{count if count else '∞'}[/cyan] packets on [cyan]{iface or 'default'}[/cyan]  filter=[cyan]{proto_filter}[/cyan]")
    info("Press [bold]Ctrl+C[/bold] to stop early.\n")

    try:
        sniff(iface=iface_arg, filter=bpf, count=count or 0, prn=packet_handler, store=False)
    except KeyboardInterrupt:
        pass

    if json_out:
        console.print_json(json.dumps({"packets": captured}))
        return

    table = make_table("TIME", "PROTO", "SRC", "DST", "LEN", "INFO", title=f"📦 Captured {len(captured)} packets")
    proto_colors = {"TCP": "cyan", "UDP": "blue", "ICMP": "yellow", "ARP": "magenta"}
    for r in captured:
        c = proto_colors.get(r["proto"], "white")
        table.add_row(
            f"[dim]{r['time']}[/dim]",
            f"[{c}]{r['proto']}[/{c}]",
            r["src"], r["dst"],
            str(r["len"]),
            f"[dim]{r['info']}[/dim]",
        )
    console.print(table)


def _tcp_flags(flags) -> str:
    names = {0x01: "FIN", 0x02: "SYN", 0x04: "RST", 0x08: "PSH", 0x10: "ACK", 0x20: "URG"}
    return "+".join(v for k, v in names.items() if int(flags) & k) or str(flags)


@app.command("arp-scan")
def arp_scan(
    subnet: Annotated[str, typer.Option("--subnet", "-s", help="Subnet, e.g. 192.168.1.0/24")] = "",
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    ARP scan to discover all devices on your local subnet.

    Example:
      sudo devha packetlab arp-scan
      sudo devha packetlab arp-scan --subnet 10.0.0.0/24
    """
    _need_root()
    sniff, ARP, IP, TCP, UDP, ICMP, Ether, Raw, get_if_list = _get_scapy()
    from scapy.all import srp  # type: ignore[import]

    if not subnet:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        subnet = ".".join(local_ip.split(".")[:3]) + ".0/24"

    info(f"ARP scanning [cyan]{subnet}[/cyan]...")

    arp_req = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet)
    answered, _ = srp(arp_req, timeout=3, retry=1, verbose=False)

    devices = []
    for _, recv in answered:
        try:
            hostname = socket.gethostbyaddr(recv.psrc)[0]
        except socket.herror:
            hostname = "?"
        devices.append({"ip": recv.psrc, "mac": recv.hwsrc, "hostname": hostname})

    devices.sort(key=lambda x: [int(p) for p in x["ip"].split(".")])

    if json_out:
        console.print_json(json.dumps({"subnet": subnet, "devices": devices}))
        return

    table = make_table("IP ADDRESS", "MAC ADDRESS", "HOSTNAME", title=f"🖥️  ARP Scan — {subnet}")
    for d in devices:
        table.add_row(f"[cyan]{d['ip']}[/cyan]", f"[dim]{d['mac']}[/dim]", d["hostname"])
    console.print(table)
    console.print(f"\n[bright_green]Found {len(devices)} device(s).[/bright_green]")


@app.command("build")
def build_packet(
    dst: Annotated[str, typer.Argument(help="Destination IP (your own test target).")],
    proto: Annotated[str, typer.Option("--proto", "-p", help="Protocol: tcp, udp, icmp.")] = "icmp",
    dport: Annotated[int, typer.Option("--dport", help="Destination port (TCP/UDP).")] = 80,
    payload: Annotated[str, typer.Option("--payload", help="Payload string.")] = "devha-test",
    count: Annotated[int, typer.Option("--count", "-n", help="Number of packets.")] = 1,
) -> None:
    """
    Build and send a custom packet to your own test system.

    Educational — shows what raw packets look like.

    Example:
      sudo devha packetlab build 127.0.0.1 --proto icmp
      sudo devha packetlab build 192.168.1.1 --proto tcp --dport 80
    """
    _need_root()
    sniff, ARP, IP, TCP, UDP, ICMP, Ether, Raw, get_if_list = _get_scapy()
    from scapy.all import send  # type: ignore[import]

    warn("⚡ Sending to your own system only — educational packet builder")

    if proto == "icmp":
        pkt = IP(dst=dst) / ICMP() / Raw(load=payload.encode())
    elif proto == "tcp":
        pkt = IP(dst=dst) / TCP(dport=dport, flags="S") / Raw(load=payload.encode())
    elif proto == "udp":
        pkt = IP(dst=dst) / UDP(dport=dport) / Raw(load=payload.encode())
    else:
        error(f"Unknown protocol: {proto}")
        raise typer.Exit(1)

    info(f"Packet summary: [cyan]{pkt.summary()}[/cyan]")
    console.print()
    console.print(pkt.show(dump=True))

    send(pkt, count=count, verbose=False)
    success(f"Sent {count} x {proto.upper()} packet(s) to {dst}.")


@app.command("stats")
def network_stats(
    iface: Annotated[str, typer.Option("--iface", "-i", help="Interface to monitor.")] = "",
    duration: Annotated[int, typer.Option("--duration", "-d", help="Monitoring duration in seconds.")] = 10,
) -> None:
    """
    Live traffic statistics — count packets by protocol.

    Example:
      sudo devha packetlab stats --duration 15
    """
    _need_root()
    sniff, ARP, IP, TCP, UDP, ICMP, Ether, Raw, get_if_list = _get_scapy()

    counts: dict[str, int] = defaultdict(int)
    bytes_: dict[str, int] = defaultdict(int)
    start = time.time()

    def handler(pkt):
        if pkt.haslayer(TCP):
            k = "TCP"
        elif pkt.haslayer(UDP):
            k = "UDP"
        elif pkt.haslayer(ICMP):
            k = "ICMP"
        elif pkt.haslayer(ARP):
            k = "ARP"
        else:
            k = "Other"
        counts[k] += 1
        bytes_[k] += len(pkt)

    info(f"Monitoring traffic for [cyan]{duration}s[/cyan]...")
    sniff(iface=iface or None, prn=handler, timeout=duration, store=False)

    table = make_table("PROTOCOL", "PACKETS", "BYTES", "% TRAFFIC", title=f"📊 Traffic Stats ({duration}s)")
    total = max(sum(counts.values()), 1)
    for proto in sorted(counts, key=lambda k: -counts[k]):
        pct = counts[proto] / total * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        table.add_row(
            f"[cyan]{proto}[/cyan]",
            str(counts[proto]),
            f"{bytes_[proto]:,} B",
            f"{bar} {pct:.1f}%",
        )
    console.print(table)

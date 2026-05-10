"""Main Typer application for devha — Hacking Studio v2.0."""

from __future__ import annotations

import subprocess
import sys
from typing import Annotated

import typer

from devha import __version__
from devha.ui import print_banner, console

from devha.commands import (
    portscan,
    username,
    wifi,
    cipher,
    subdomains,
    dirscan,
    crawl,
    harvest,
    headers,
    ping,
    wifilab,
    passlab,
    packetlab,
)
from devha.commands.devscanner import devscanner

app = typer.Typer(
    name="devha",
    help="[cyan]devha Hacking Studio v2.0[/cyan] — ethical hacking & developer toolkit.",
    rich_markup_mode="rich",
    no_args_is_help=False,
    add_completion=True,
)

# ─── Sub-apps (grouped commands) ──────────────────────────────────────────────────
app.add_typer(cipher.app,    name="cipher",    help="🔐 Classical & modern ciphers.")
app.add_typer(wifilab.app,   name="wifilab",   help="📡 WiFi Lab — scan, map devices, test own AP.")
app.add_typer(passlab.app,   name="passlab",   help="🔑 Password Lab — hash, crack, generate.")
app.add_typer(packetlab.app, name="packetlab", help="📦 Packet Lab — capture, ARP scan, builder.")

# ─── Single commands ────────────────────────────────────────────────────────────
app.command("portscan")(portscan.portscan)
app.command("username")(username.username)
app.command("wifi")(wifi.wifi)
app.command("subdomains")(subdomains.subdomains)
app.command("dirscan")(dirscan.dirscan)
app.command("crawl")(crawl.crawl)
app.command("harvest")(harvest.harvest)
app.command("headers")(headers.headers)
app.command("ping")(ping.ping)
app.command("devscanner")(devscanner)


# ─── Studio TUI ───────────────────────────────────────────────────────────────

@app.command("studio")
def studio(
    no_fx: Annotated[bool, typer.Option("--no-fx", help="Skip boot animation.")] = False,
) -> None:
    """
    🎮 Open the interactive Hacking Studio TUI menu.

    Navigate with [1-9] keys. All tools available in one interface.
    """
    if not no_fx:
        from devha.fx import hacker_boot
        hacker_boot()

    from devha.studio import run_studio
    module = run_studio()

    if module:
        _launch_module(module)


# ─── Version + main callback ───────────────────────────────────────────────────

def _version_callback(value: bool) -> None:
    if value:
        console.print(f"[cyan]devha[/cyan] Hacking Studio version [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", "-V", callback=_version_callback, is_eager=True, help="Show version."),
    ] = False,
    no_banner: Annotated[bool, typer.Option("--no-banner", help="Skip the ASCII banner.")] = False,
    studio_mode: Annotated[bool, typer.Option("--studio", "-s", help="Launch interactive Studio TUI.")] = False,
) -> None:
    """[cyan bold]devha[/cyan bold] Hacking Studio — Developer & Hacking CLI v2.0."""
    if studio_mode:
        ctx.invoke(studio)
        return

    if ctx.invoked_subcommand is None:
        from devha.fx import hacker_boot
        if not no_banner:
            hacker_boot()
        from devha.studio import run_studio
        module = run_studio()
        if module:
            _launch_module(module)
    elif not no_banner:
        print_banner()


def _ask(prompt: str) -> str:
    """Ask user for input, return empty string on cancel."""
    try:
        return input(f"  {prompt}: ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def _run(*args: str) -> None:
    subprocess.run(["devha", *args])


def _launch_module(module: str) -> None:  # noqa: C901
    console.print()

    if module == "network":
        console.print("[bold cyan]── Network Scanner ──[/bold cyan]")
        host = _ask("Hostname or IP (e.g. scanme.nmap.org)")
        if host:
            _run("devscanner", host)

    elif module == "wifi":
        console.print("[bold cyan]── WiFi Lab ──[/bold cyan]")
        console.print("  [1] Scan nearby networks\n  [2] Find devices on my network\n  [3] Check my router security")
        choice = _ask("Choose (1/2/3)")
        if choice == "1":
            _run("wifilab", "scan")
        elif choice == "2":
            _run("wifilab", "devices")
        elif choice == "3":
            host = _ask("Router IP (e.g. 192.168.1.1)") or "192.168.1.1"
            _run("wifilab", "security", host)

    elif module == "osint":
        console.print("[bold cyan]── OSINT Suite ──[/bold cyan]")
        console.print("  [1] Check username on 50+ sites\n  [2] Harvest info about a domain\n  [3] Find subdomains")
        choice = _ask("Choose (1/2/3)")
        if choice == "1":
            name = _ask("Username")
            if name:
                _run("username", name)
        elif choice == "2":
            domain = _ask("Domain (e.g. example.com)")
            if domain:
                _run("harvest", domain)
        elif choice == "3":
            domain = _ask("Domain (e.g. example.com)")
            if domain:
                _run("subdomains", domain)

    elif module == "cipher":
        console.print("[bold cyan]── Crypto & Cipher ──[/bold cyan]")
        console.print("  [1] Encode text\n  [2] Decode text\n  [3] Crack caesar cipher\n  [4] Show all encodings")
        choice = _ask("Choose (1/2/3/4)")
        if choice in ("1", "2"):
            text = _ask("Text")
            if not text:
                return
            console.print("  Types: caesar  rot13  rot47  atbash  vigenere  base64  hex  binary  morse")
            cipher_type = _ask("Cipher type") or "caesar"
            op = "encode" if choice == "1" else "decode"
            if cipher_type == "caesar":
                key = _ask("Shift (default 13)") or "13"
                _run("cipher", op, text, "--type", cipher_type, "--key", key)
            elif cipher_type == "vigenere":
                key = _ask("Key word")
                if key:
                    _run("cipher", op, text, "--type", cipher_type, "--key", key)
            else:
                _run("cipher", op, text, "--type", cipher_type)
        elif choice == "3":
            text = _ask("Ciphertext to crack")
            if text:
                _run("cipher", "crack", text)
        elif choice == "4":
            text = _ask("Text")
            if text:
                _run("cipher", "all", text)

    elif module == "web":
        console.print("[bold cyan]── Web Recon ──[/bold cyan]")
        console.print("  [1] Directory scan\n  [2] Crawl & extract links/emails\n  [3] Check security headers")
        choice = _ask("Choose (1/2/3)")
        url = _ask("URL (e.g. https://example.com)")
        if not url:
            return
        if not url.startswith("http"):
            url = "https://" + url
        if choice == "1":
            _run("dirscan", url)
        elif choice == "2":
            _run("crawl", url)
        elif choice == "3":
            _run("headers", url)

    elif module == "password":
        console.print("[bold cyan]── Password Lab ──[/bold cyan]")
        console.print("  [1] Generate a strong password\n  [2] Hash a password\n  [3] Check password strength\n  [4] Identify hash type")
        choice = _ask("Choose (1/2/3/4)")
        if choice == "1":
            _run("passlab", "generate")
        elif choice == "2":
            pw = _ask("Password to hash")
            if pw:
                _run("passlab", "hash", pw)
        elif choice == "3":
            pw = _ask("Password to check")
            if pw:
                _run("passlab", "strength", pw)
        elif choice == "4":
            h = _ask("Hash string")
            if h:
                _run("passlab", "identify", h)

    elif module == "packets":
        console.print("[bold cyan]── Packet Lab ──[/bold cyan]")
        console.print("  [1] ARP scan (find devices)\n  [2] Capture packets\n  [3] Traffic stats")
        choice = _ask("Choose (1/2/3)")
        if choice == "1":
            _run("packetlab", "arp-scan")
        elif choice == "2":
            iface = _ask("Interface (e.g. en0, eth0)") or "eth0"
            count = _ask("How many packets (default 20)") or "20"
            _run("packetlab", "capture", "--iface", iface, "--count", count)
        elif choice == "3":
            _run("packetlab", "stats")

    elif module == "headers":
        console.print("[bold cyan]── Headers Audit ──[/bold cyan]")
        url = _ask("URL to audit (e.g. https://example.com)")
        if not url:
            return
        if not url.startswith("http"):
            url = "https://" + url
        _run("headers", url)

    elif module == "ping":
        console.print("[bold cyan]── Ping ──[/bold cyan]")
        host = _ask("Hostname or IP (e.g. 8.8.8.8)")
        if host:
            _run("ping", host)

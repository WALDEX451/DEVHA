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

# ─── Sub-apps (grouped commands) ─────────────────────────────────────────────
app.add_typer(cipher.app,    name="cipher",    help="🔐 Classical & modern ciphers.")
app.add_typer(wifilab.app,   name="wifilab",   help="📡 WiFi Lab — scan, map devices, test own AP.")
app.add_typer(passlab.app,   name="passlab",   help="🔑 Password Lab — hash, crack, generate.")
app.add_typer(packetlab.app, name="packetlab", help="📦 Packet Lab — capture, ARP scan, builder.")

# ─── Single commands ──────────────────────────────────────────────────────────
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

    # Map module name → CLI command to run
    _module_map = {
        "network":  ["devha", "devscanner", "--help"],
        "wifi":     ["devha", "wifilab", "--help"],
        "osint":    ["devha", "username", "--help"],
        "cipher":   ["devha", "cipher", "--help"],
        "web":      ["devha", "dirscan", "--help"],
        "password": ["devha", "passlab", "--help"],
        "packets":  ["devha", "packetlab", "--help"],
        "headers":  ["devha", "headers", "--help"],
        "ping":     ["devha", "ping", "--help"],
    }

    if module and module in _module_map:
        subprocess.run(_module_map[module])


# ─── Version + main callback ─────────────────────────────────────────────────

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
        # No subcommand → show studio TUI
        from devha.fx import hacker_boot
        if not no_banner:
            hacker_boot()
        from devha.studio import run_studio
        module = run_studio()
        if module:
            _launch_module(module)
    elif not no_banner:
        print_banner()


def _launch_module(module: str) -> None:
    _map = {
        "network":  ["devha", "devscanner", "--help"],
        "wifi":     ["devha", "wifilab", "--help"],
        "osint":    ["devha", "username", "--help"],
        "cipher":   ["devha", "cipher", "--help"],
        "web":      ["devha", "dirscan", "--help"],
        "password": ["devha", "passlab", "--help"],
        "packets":  ["devha", "packetlab", "--help"],
        "headers":  ["devha", "headers", "--help"],
        "ping":     ["devha", "ping", "--help"],
    }
    if module in _map:
        subprocess.run(_map[module])

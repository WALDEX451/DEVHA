"""Main Typer application for devha."""

from __future__ import annotations

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
)

app = typer.Typer(
    name="devha",
    help="[cyan]Developer & Hacking CLI[/cyan] — ethical hacking and developer toolkit.",
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=True,
)

# Register sub-apps
app.add_typer(cipher.app, name="cipher", help="Classical cipher encode / decode / crack.")
app.command("portscan")(portscan.portscan)
app.command("username")(username.username)
app.command("wifi")(wifi.wifi)
app.command("subdomains")(subdomains.subdomains)
app.command("dirscan")(dirscan.dirscan)
app.command("crawl")(crawl.crawl)
app.command("harvest")(harvest.harvest)
app.command("headers")(headers.headers)
app.command("ping")(ping.ping)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"[cyan]devha[/cyan] version [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", "-V", callback=_version_callback, is_eager=True, help="Show version."),
    ] = False,
    no_banner: Annotated[bool, typer.Option("--no-banner", help="Skip the ASCII banner.")] = False,
) -> None:
    """[cyan bold]devha[/cyan bold] — Developer & Hacking CLI."""
    if not no_banner and ctx.invoked_subcommand is not None:
        print_banner()

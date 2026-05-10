"""Ethical-use warnings and confirmation helpers."""

from __future__ import annotations

import typer
from rich.panel import Panel
from rich.text import Text

from devha.ui import console, warn

_WHITELIST = {"localhost", "127.0.0.1", "::1", "scanme.nmap.org"}

WARNING_TEXT = """[yellow bold]ETHICAL WARNING[/yellow bold]

This scan sends traffic to an external host.
Only run this against:

  • Systems you own
  • Systems for which you have [bold]explicit written permission[/bold]
  • Legal test environments ([cyan]scanme.nmap.org[/cyan], HackTheBox, TryHackMe)

Unauthorised scanning may be illegal in your jurisdiction."""


def ethics_check(target: str, *, yes: bool = False) -> None:
    """Show ethics warning and ask for confirmation unless bypassed."""
    if yes or target.lower() in _WHITELIST:
        return

    console.print(Panel(Text.from_markup(WARNING_TEXT), border_style="yellow", title="⚠  devha"))
    confirmed = typer.confirm("Continue?", default=False)
    if not confirmed:
        raise typer.Abort()

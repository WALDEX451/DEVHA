"""Shared Rich UI helpers for devha."""

from __future__ import annotations

import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()
err_console = Console(stderr=True)


BANNER = r"""
   ╔══════════════════════════════════════════╗
   ║  ██████╗ ███████╗██╗   ██╗██╗  ██╗ █████╗  ║
   ║  ██╔══██╗██╔════╝██║   ██║██║  ██║██╔══██╗ ║
   ║  ██║  ██║█████╗  ██║   ██║███████║███████║ ║
   ║  ██║  ██║██╔══╝  ╚██╗ ██╔╝██╔══██║██╔══██║ ║
   ║  ██████╔╝███████╗ ╚████╔╝ ██║  ██║██║  ██║ ║
   ║  ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝ ║
   ║                                            ║
   ║   Developer & Hacking CLI  v0.1.0          ║
   ║   ⚠  For ethical use only                  ║
   ╚══════════════════════════════════════════╝
"""


def print_banner() -> None:
    console.print(Text(BANNER, style="cyan dim"))


def make_table(*columns: str, title: str | None = None) -> Table:
    table = Table(
        title=title,
        box=box.ROUNDED,
        border_style="cyan",
        header_style="bold magenta",
        show_lines=False,
    )
    for col in columns:
        table.add_column(col)
    return table


def print_panel(content: Any, title: str = "", style: str = "cyan") -> None:
    console.print(Panel(content, title=title, border_style=style, expand=False))


def success(msg: str) -> None:
    console.print(f"[bright_green]✔[/bright_green]  {msg}")


def warn(msg: str) -> None:
    console.print(f"[yellow]⚠[/yellow]  {msg}")


def error(msg: str) -> None:
    err_console.print(f"[bright_red]✘[/bright_red]  {msg}")


def info(msg: str) -> None:
    console.print(f"[blue]ℹ[/blue]  {msg}")


def fatal(msg: str, code: int = 1) -> None:
    error(msg)
    sys.exit(code)

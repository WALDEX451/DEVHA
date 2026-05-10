"""devha Hacking Studio — Textual TUI main menu."""

from __future__ import annotations

import asyncio
import random
import time
from typing import Callable

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Label, Static, RichLog

# ─── Matrix rain effect ───────────────────────────────────────────────────────

_MATRIX_CHARS = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ01アイウエオカキクケコ"

_MENU_ITEMS = [
    ("1", "🔌", "Network Scanner",   "Port scan · OS detect · CVE lookup"),
    ("2", "📡", "WiFi Lab",          "Scan · Device map · Security test"),
    ("3", "👤", "OSINT Suite",       "Username · Harvest · Subdomains"),
    ("4", "🔐", "Crypto & Cipher",   "Encode · Decode · Crack · Steg"),
    ("5", "🕸️ ", "Web Recon",        "Dirscan · Headers · Crawl"),
    ("6", "🔑", "Password Lab",      "Hash ID · Crack · Generator"),
    ("7", "📦", "Packet Lab",        "Capture · ARP scan · Builder"),
    ("8", "🛡️ ", "Headers Audit",    "Security score · Missing headers"),
    ("9", "🏓", "Ping & Trace",      "ICMP · Traceroute · Latency"),
]

_BANNER = """[bold cyan]
  ██████╗ ███████╗██╗   ██╗██║  ██╗ █████╗
  ██╔══██╗██╔════╝██║   ██║██║  ██║██╔══██╗
  ██║  ██║█████╗  ██║   ██║███████║███████║
  ██║  ██║██╔══╝  ╚██╗ ██╔╝██╔══██║██╔══██║
  ██████╔╝███████╗ ╚████╔╝ ██║  ██║██║  ██║
  ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝[/bold cyan]
[dim cyan]  Hacking Studio v2.0  ·  Ethical use only  ·  Own systems only[/dim cyan]"""


class MatrixColumn(Static):
    """Single column of falling matrix characters."""

    DEFAULT_CSS = """
    MatrixColumn {
        width: 1;
        color: green;
        text-opacity: 60%;
    }
    """

    chars: reactive[str] = reactive("")

    def on_mount(self) -> None:
        self.col_chars = [random.choice(_MATRIX_CHARS) for _ in range(40)]
        self.offset = random.randint(0, 30)
        self.speed = random.uniform(0.05, 0.15)
        self.set_interval(self.speed, self._tick)

    def _tick(self) -> None:
        self.offset = (self.offset + 1) % 40
        self.col_chars[random.randint(0, 39)] = random.choice(_MATRIX_CHARS)
        self.chars = "\n".join(self.col_chars)

    def render(self) -> Text:
        t = Text()
        chars = self.col_chars
        for i, ch in enumerate(chars):
            dist = (i - self.offset) % len(chars)
            if dist == 0:
                t.append(ch, "bold bright_white")
            elif dist < 4:
                t.append(ch, "bold bright_green")
            elif dist < 10:
                t.append(ch, "green")
            else:
                t.append(ch, "dim green")
        return t


class MenuCard(Static):
    """A single menu item card."""

    DEFAULT_CSS = """
    MenuCard {
        border: round #1a1a2e;
        padding: 0 1;
        margin: 0 0 1 0;
        background: #0a0a0f;
        color: #aaaaaa;
    }
    MenuCard:hover {
        border: round cyan;
        background: #0d1f2d;
        color: bright_white;
    }
    MenuCard.selected {
        border: round bright_cyan;
        background: #0d2137;
        color: bright_white;
    }
    """

    def __init__(self, key: str, icon: str, title: str, desc: str, **kwargs):
        super().__init__(**kwargs)
        self.key = key
        self.icon = icon
        self.title = title
        self.desc = desc

    def render(self) -> Text:
        t = Text()
        t.append(f" [{self.key}] ", "bold cyan")
        t.append(f"{self.icon} ", "")
        t.append(self.title, "bold bright_white")
        t.append(f"  —  {self.desc}", "dim")
        return t


class DevhaStudio(App):
    """devha Hacking Studio — main TUI application."""

    CSS = """
    Screen {
        background: #050508;
        layers: matrix menu;
    }

    #matrix-bg {
        layer: matrix;
        layout: horizontal;
        width: 100%;
        height: 100%;
        opacity: 15%;
        overflow: hidden;
    }

    #main-container {
        layer: menu;
        align: center middle;
        width: 100%;
        height: 100%;
    }

    #center-panel {
        width: 70;
        height: auto;
        background: #050508;
        border: double cyan;
        padding: 1 2;
    }

    #banner {
        width: 100%;
        text-align: center;
        margin: 0 0 1 0;
    }

    #ethics-note {
        color: #aaaa00;
        text-align: center;
        margin: 0 0 1 0;
    }

    #menu-list {
        width: 100%;
        height: auto;
    }

    Footer {
        background: #050508;
        color: cyan;
    }
    """

    BINDINGS = [
        Binding("1", "launch('network')", "Network"),
        Binding("2", "launch('wifi')", "WiFi Lab"),
        Binding("3", "launch('osint')", "OSINT"),
        Binding("4", "launch('cipher')", "Crypto"),
        Binding("5", "launch('web')", "Web"),
        Binding("6", "launch('password')", "Passwords"),
        Binding("7", "launch('packets')", "Packets"),
        Binding("8", "launch('headers')", "Headers"),
        Binding("9", "launch('ping')", "Ping"),
        Binding("q", "quit", "Quit"),
    ]

    TITLE = "devha Hacking Studio"

    def compose(self) -> ComposeResult:
        # Matrix background
        with Horizontal(id="matrix-bg"):
            for _ in range(80):
                yield MatrixColumn()

        # Main menu
        with Container(id="main-container"):
            with Vertical(id="center-panel"):
                yield Static(_BANNER, id="banner")
                yield Static(
                    "⚡ Own systems only  ·  Stay legal  ·  Be ethical",
                    id="ethics-note",
                )
                with Vertical(id="menu-list"):
                    for key, icon, title, desc in _MENU_ITEMS:
                        yield MenuCard(key, icon, title, desc)

        yield Footer()

    def action_launch(self, module: str) -> None:
        """Launch a module — exit TUI and run the command."""
        self.exit(result=module)


def run_studio() -> str | None:
    """Run the TUI and return the selected module name."""
    app = DevhaStudio()
    return app.run()

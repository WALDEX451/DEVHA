"""Movie-hacker visual effects — glitch text, typing animation, matrix."""

from __future__ import annotations

import random
import sys
import time

from rich.console import Console
from rich.live import Live
from rich.text import Text

console = Console()

_GLITCH_CHARS = "!@#$%^&*<>?/|\\[]{}~`ﾊﾐﾋｰｳｼﾅﾓﾆ01"
_MATRIX_CHARS = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ0123456789"


def glitch_print(text: str, iterations: int = 6, delay: float = 0.06) -> None:
    """Print text with a glitch effect that resolves to the real text."""
    chars = list(text)
    resolved = [False] * len(chars)

    with Live(console=console, refresh_per_second=20) as live:
        for _ in range(iterations):
            display = Text()
            for i, ch in enumerate(chars):
                if resolved[i] or ch == " ":
                    display.append(ch, "bold bright_green" if resolved[i] else "")
                else:
                    display.append(random.choice(_GLITCH_CHARS), "bold bright_red")
            live.update(display)
            time.sleep(delay)

            # Resolve random characters each round
            unresolve = [i for i, r in enumerate(resolved) if not r and chars[i] != " "]
            for i in random.sample(unresolve, min(len(unresolve), max(1, len(unresolve) // 3))):
                resolved[i] = True

        # Final resolved text
        live.update(Text(text, style="bold bright_green"))


def typing_print(text: str, delay: float = 0.03, style: str = "bright_green") -> None:
    """Print text character by character like a movie hacker."""
    for ch in text:
        console.print(ch, end="", style=style)
        sys.stdout.flush()
        jitter = delay + random.uniform(-delay * 0.3, delay * 0.3)
        time.sleep(max(0.005, jitter))
    console.print()


def matrix_splash(duration: float = 2.0, width: int = 60, height: int = 15) -> None:
    """Display a matrix rain splash screen."""
    columns = [[random.choice(_MATRIX_CHARS) for _ in range(height)] for _ in range(width)]
    offsets = [random.randint(0, height) for _ in range(width)]
    speeds = [random.uniform(0.5, 2.0) for _ in range(width)]
    ticks = [0.0] * width

    start = time.time()
    with Live(console=console, refresh_per_second=15) as live:
        while time.time() - start < duration:
            now = time.time() - start
            lines = []
            for row in range(height):
                line = Text()
                for col in range(width):
                    ch_row = (offsets[col] + row) % height
                    ch = columns[col][ch_row]
                    dist = (row - offsets[col]) % height
                    if dist == 0:
                        line.append(ch, "bold bright_white")
                    elif dist < 3:
                        line.append(ch, "bold bright_green")
                    elif dist < 8:
                        line.append(ch, "green")
                    else:
                        line.append(ch, "dim green")
                lines.append(line)

            # Scroll columns
            for col in range(width):
                ticks[col] += 0.07
                if ticks[col] >= 1.0 / speeds[col]:
                    ticks[col] = 0
                    offsets[col] = (offsets[col] + 1) % height
                    columns[col][random.randint(0, height - 1)] = random.choice(_MATRIX_CHARS)

            combined = Text("\n").join(lines)
            live.update(combined)
            time.sleep(0.05)


def hacker_boot(target: str = "") -> None:
    """Cinematic boot sequence — movie-style hacker startup."""
    lines = [
        "[dim cyan]Initializing devha Hacking Studio...[/dim cyan]",
        "[dim cyan]Loading modules: portscan · wifi · osint · crypto · passlab · packetlab[/dim cyan]",
        f"[dim cyan]Target: [bold]{target or 'interactive mode'}[/bold][/dim cyan]",
        "[bright_green][ OK ] All systems nominal[/bright_green]",
        "[bright_green][ OK ] Ethics module loaded — own systems only[/bright_green]",
    ]

    matrix_splash(1.2, width=70, height=8)

    for line in lines:
        console.print(line)
        time.sleep(0.15)

    time.sleep(0.2)
    glitch_print("  DEVHA HACKING STUDIO v2.0  ", iterations=8, delay=0.05)
    time.sleep(0.3)

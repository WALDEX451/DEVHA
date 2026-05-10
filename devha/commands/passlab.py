"""Password Lab — hash identification, cracking, strength meter, generator."""

from __future__ import annotations

import hashlib
import json
import random
import re
import string
import struct
from typing import Annotated

import typer
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn

from devha.ui import console, make_table, print_panel, info, warn, error, success

app = typer.Typer(help="🔑 Password Lab — hash ID, crack, strength meter, generator.")

# ─── Hash patterns ─────────────────────────────────────────────────────────────

_HASH_PATTERNS = [
    (r"^[a-f0-9]{32}$",  "MD5"),
    (r"^[a-f0-9]{40}$",  "SHA-1"),
    (r"^[a-f0-9]{56}$",  "SHA-224"),
    (r"^[a-f0-9]{64}$",  "SHA-256"),
    (r"^[a-f0-9]{96}$",  "SHA-384"),
    (r"^[a-f0-9]{128}$", "SHA-512"),
    (r"^\$2[ayb]\$.{56}$", "bcrypt"),
    (r"^\$1\$.{1,8}\$.{22}$", "MD5-crypt"),
    (r"^\$5\$.*\$.{43}$", "SHA-256-crypt"),
    (r"^\$6\$.*\$.{86}$", "SHA-512-crypt"),
    (r"^[a-f0-9]{8}:[a-f0-9]{40}$", "SHA-1+salt"),
    (r"^[A-Za-z0-9+/]{24}$", "Base64 (possible MD5)"),
    (r"^[A-Z]{13}$", "ROT13"),
    (r"^[a-f0-9]{16}$", "MySQL 3.x / DES"),
    (r"^\*[A-F0-9]{40}$", "MySQL 4.1+"),
    (r"^[a-zA-Z0-9]{13}$", "DES-crypt"),
]

_HASH_FUNCS = {
    "MD5": lambda p: hashlib.md5(p).hexdigest(),
    "SHA-1": lambda p: hashlib.sha1(p).hexdigest(),
    "SHA-224": lambda p: hashlib.sha224(p).hexdigest(),
    "SHA-256": lambda p: hashlib.sha256(p).hexdigest(),
    "SHA-384": lambda p: hashlib.sha384(p).hexdigest(),
    "SHA-512": lambda p: hashlib.sha512(p).hexdigest(),
}

_COMMON_PASSWORDS = [
    "password", "123456", "password123", "admin", "letmein", "qwerty",
    "monkey", "dragon", "master", "abc123", "iloveyou", "1234567890",
    "sunshine", "princess", "welcome", "shadow", "superman", "michael",
    "football", "baseball", "trustno1", "passw0rd", "p@ssword", "hunter2",
]


# ─── Commands ──────────────────────────────────────────────────────────────────

@app.command("identify")
def identify_hash(
    hash_val: Annotated[str, typer.Argument(help="Hash string to identify.")],
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    Identify the type of a hash string.

    Example:
      devha passlab identify 5f4dcc3b5aa765d61d8327deb882cf99
    """
    matches = []
    for pattern, name in _HASH_PATTERNS:
        if re.match(pattern, hash_val, re.IGNORECASE):
            matches.append(name)

    if json_out:
        console.print_json(json.dumps({"hash": hash_val, "possible_types": matches}))
        return

    if not matches:
        warn(f"Could not identify hash: [cyan]{hash_val}[/cyan]")
        return

    table = make_table("POSSIBLE HASH TYPE", "LENGTH", title="🔍 Hash Identification")
    for m in matches:
        table.add_row(f"[bright_green]{m}[/bright_green]", str(len(hash_val)))
    console.print(table)


@app.command("crack")
def crack_hash(
    hash_val: Annotated[str, typer.Argument(help="Hash to crack.")],
    wordlist: Annotated[str, typer.Option("--wordlist", "-w", help="Path to wordlist file (one password per line).")] = "",
    hash_type: Annotated[str, typer.Option("--type", "-t", help="Hash type: md5, sha1, sha256, sha512 (auto-detect if not set).")] = "",
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    Crack a hash using a wordlist or built-in common passwords.

    Example:
      devha passlab crack 5f4dcc3b5aa765d61d8327deb882cf99
      devha passlab crack <hash> --wordlist /usr/share/wordlists/rockyou.txt
    """
    # Auto-detect type
    if not hash_type:
        for pattern, name in _HASH_PATTERNS:
            if re.match(pattern, hash_val, re.IGNORECASE) and name in _HASH_FUNCS:
                hash_type = name
                break

    if not hash_type or hash_type.upper() not in _HASH_FUNCS:
        # Try all supported types
        candidates = [t for t in _HASH_FUNCS if t != "bcrypt"]
    else:
        candidates = [hash_type.upper()]

    # Load wordlist
    if wordlist:
        try:
            with open(wordlist, encoding="utf-8", errors="ignore") as f:
                words = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            error(f"Wordlist not found: {wordlist}")
            raise typer.Exit(1)
    else:
        words = list(_COMMON_PASSWORDS)
        warn(f"No wordlist specified — using {len(words)} common passwords. Use --wordlist for better results.")

    info(f"Cracking [cyan]{hash_val[:20]}...[/cyan] with {len(words)} words...")

    found = None
    with Progress(SpinnerColumn(), "[cyan]Cracking...", BarColumn(), TaskProgressColumn(), console=console) as prog:
        task = prog.add_task("crack", total=len(words) * len(candidates))
        for word in words:
            for htype in candidates:
                h = _HASH_FUNCS[htype](word.encode())
                if h.lower() == hash_val.lower():
                    found = (word, htype)
                    prog.update(task, completed=prog.tasks[task].total)
                    break
            if found:
                break
            prog.advance(task, len(candidates))

    if json_out:
        console.print_json(json.dumps({"hash": hash_val, "found": found[0] if found else None, "type": found[1] if found else None}))
        return

    if found:
        success(f"CRACKED! Hash type: [cyan]{found[1]}[/cyan]")
        print_panel(f"[bold bright_green]Password: {found[0]}[/bold bright_green]", title="💥 Cracked!", style="bright_green")
    else:
        warn("Not found in wordlist. Try a larger wordlist like rockyou.txt")


@app.command("strength")
def check_strength(
    password: Annotated[str, typer.Argument(help="Password to check.")],
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    Check password strength with a detailed score breakdown.

    Example:
      devha passlab strength "MyP@ssw0rd!"
    """
    score = 0
    checks = []

    def chk(name: str, passed: bool, points: int, tip: str = "") -> None:
        nonlocal score
        if passed:
            score += points
        checks.append({"name": name, "passed": passed, "points": points if passed else 0, "tip": tip})

    chk("Length ≥ 8",   len(password) >= 8,  10, "Use at least 8 characters")
    chk("Length ≥ 12",  len(password) >= 12, 10, "Use at least 12 characters")
    chk("Length ≥ 16",  len(password) >= 16, 10, "Use at least 16 characters")
    chk("Uppercase",    any(c.isupper() for c in password), 15, "Add uppercase letters (A-Z)")
    chk("Lowercase",    any(c.islower() for c in password), 15, "Add lowercase letters (a-z)")
    chk("Digits",       any(c.isdigit() for c in password), 15, "Add numbers (0-9)")
    chk("Symbols",      any(c in string.punctuation for c in password), 20, "Add symbols (!@#$%)")
    chk("Not common",   password.lower() not in _COMMON_PASSWORDS, 15, "Avoid common passwords")

    max_score = sum(c["points"] + (c["points"] if not c["passed"] else 0) for c in checks)
    pct = int(score / 85 * 100)

    if pct >= 80:
        label, style = "STRONG 💪", "bright_green"
    elif pct >= 55:
        label, style = "MEDIUM ⚠️", "yellow"
    else:
        label, style = "WEAK 💀", "bright_red"

    if json_out:
        console.print_json(json.dumps({"password": "*" * len(password), "score": score, "percent": pct, "rating": label, "checks": checks}))
        return

    table = make_table("CHECK", "RESULT", "POINTS", title="🔑 Password Strength")
    for c in checks:
        status = "[bright_green]✔[/bright_green]" if c["passed"] else "[bright_red]✘[/bright_red]"
        pts = f"[bright_green]+{c['points']}[/bright_green]" if c["passed"] else f"[dim]0[/dim]"
        tip = f"[dim] — {c['tip']}[/dim]" if not c["passed"] and c["tip"] else ""
        table.add_row(c["name"] + tip, status, pts)
    console.print(table)

    bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
    console.print(f"\n[{style}]  {bar}  {pct}%  {label}[/{style}]")


@app.command("generate")
def generate_password(
    length: Annotated[int, typer.Option("--length", "-l", help="Password length.")] = 20,
    count: Annotated[int, typer.Option("--count", "-n", help="Number of passwords to generate.")] = 5,
    no_symbols: Annotated[bool, typer.Option("--no-symbols", help="Exclude special characters.")] = False,
    memorable: Annotated[bool, typer.Option("--memorable", help="Generate word-based passphrase.")] = False,
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    Generate strong random passwords or passphrases.

    Example:
      devha passlab generate --length 24 --count 3
      devha passlab generate --memorable
    """
    _WORDS = [
        "correct", "horse", "battery", "staple", "purple", "monkey",
        "dishwasher", "rainbow", "quantum", "laser", "cyber", "pixel",
        "shadow", "thunder", "falcon", "vector", "matrix", "ninja",
        "cosmic", "eclipse", "phoenix", "dragon", "titan", "nova",
    ]

    passwords = []
    charset = string.ascii_letters + string.digits + ("" if no_symbols else "!@#$%^&*-_=+")

    for _ in range(count):
        if memorable:
            pw = "-".join(random.choices(_WORDS, k=4)) + str(random.randint(10, 99))
        else:
            pw = "".join(random.choices(charset, k=length))
        passwords.append(pw)

    if json_out:
        console.print_json(json.dumps({"passwords": passwords}))
        return

    table = make_table("#", "PASSWORD", "LENGTH", title="🎲 Generated Passwords")
    for i, pw in enumerate(passwords, 1):
        table.add_row(str(i), f"[bright_green]{pw}[/bright_green]", str(len(pw)))
    console.print(table)
    console.print("[dim]Tip: use a password manager to store these.[/dim]")


@app.command("hash")
def hash_text(
    text: Annotated[str, typer.Argument(help="Text to hash.")],
    algo: Annotated[str, typer.Option("--algo", "-a", help="Algorithm: md5, sha1, sha256, sha512, all.")] = "all",
    json_out: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """
    Hash a string with common algorithms.

    Example:
      devha passlab hash "hello world" --algo sha256
      devha passlab hash "password" --algo all
    """
    algos = list(_HASH_FUNCS.keys()) if algo == "all" else [algo.upper()]
    results = {}
    for a in algos:
        if a in _HASH_FUNCS:
            results[a] = _HASH_FUNCS[a](text.encode())

    if json_out:
        console.print_json(json.dumps({"input": text, "hashes": results}))
        return

    table = make_table("ALGORITHM", "HASH", title=f"🔒 Hashes of '{text[:30]}'")
    for a, h in results.items():
        table.add_row(f"[cyan]{a}[/cyan]", h)
    console.print(table)

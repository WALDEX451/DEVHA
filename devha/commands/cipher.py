"""Cipher command: encode, decode, crack classical ciphers."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich.text import Text

from devha.ui import console, make_table, print_panel, error

app = typer.Typer(help="Classical cipher [encode / decode / crack].", rich_markup_mode="rich")

# English letter frequency for readability scoring
_EN_FREQ = {
    "e": 12.70, "t": 9.06, "a": 8.17, "o": 7.51, "i": 6.97,
    "n": 6.75, "s": 6.33, "h": 6.09, "r": 5.99, "d": 4.25,
    "l": 4.03, "c": 2.78, "u": 2.76, "m": 2.41, "w": 2.36,
    "f": 2.23, "g": 2.02, "y": 1.97, "p": 1.93, "b": 1.29,
    "v": 0.98, "k": 0.77, "j": 0.15, "x": 0.15, "q": 0.10, "z": 0.07,
}


# ─── Core cipher implementations ─────────────────────────────────────────────


def caesar_encode(text: str, shift: int) -> str:
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            result.append(ch)
    return "".join(result)


def caesar_decode(text: str, shift: int) -> str:
    return caesar_encode(text, -shift)


def rot13_encode(text: str) -> str:
    return caesar_encode(text, 13)


def rot13_decode(text: str) -> str:
    return rot13_encode(text)


def atbash_encode(text: str) -> str:
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            result.append(chr(base + 25 - (ord(ch) - base)))
        else:
            result.append(ch)
    return "".join(result)


def atbash_decode(text: str) -> str:
    return atbash_encode(text)


def vigenere_encode(text: str, key: str) -> str:
    key = key.lower()
    result = []
    ki = 0
    for ch in text:
        if ch.isalpha():
            shift = ord(key[ki % len(key)]) - ord("a")
            base = ord("A") if ch.isupper() else ord("a")
            result.append(chr((ord(ch) - base + shift) % 26 + base))
            ki += 1
        else:
            result.append(ch)
    return "".join(result)


def vigenere_decode(text: str, key: str) -> str:
    key = key.lower()
    result = []
    ki = 0
    for ch in text:
        if ch.isalpha():
            shift = ord(key[ki % len(key)]) - ord("a")
            base = ord("A") if ch.isupper() else ord("a")
            result.append(chr((ord(ch) - base - shift) % 26 + base))
            ki += 1
        else:
            result.append(ch)
    return "".join(result)


def _readability_score(text: str) -> float:
    """Score 0-100 based on English letter frequency match."""
    letters = [ch.lower() for ch in text if ch.isalpha()]
    if not letters:
        return 0.0
    total = len(letters)
    score = sum(_EN_FREQ.get(ch, 0) * (letters.count(ch) / total) for ch in set(letters))
    return round(score, 2)


# ─── Typer sub-commands ───────────────────────────────────────────────────────


@app.command("encode")
def encode(
    text: Annotated[str, typer.Argument(help="Text to encode.")],
    cipher_type: Annotated[str, typer.Option("--type", "-t", help="[caesar|vigenere|rot13|atbash]")] = "caesar",
    key: Annotated[str, typer.Option("--key", "-k", help="Key (shift for caesar, phrase for vigenere).")] = "13",
    json_out: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
) -> None:
    """Encode text using a classical cipher."""
    result = _apply_cipher(text, cipher_type, key, mode="encode")
    if json_out:
        console.print_json(json.dumps({"cipher": cipher_type, "input": text, "output": result}))
    else:
        print_panel(f"[bright_green]{result}[/bright_green]", title=f"Encoded ({cipher_type})")


@app.command("decode")
def decode(
    text: Annotated[str, typer.Argument(help="Text to decode.")],
    cipher_type: Annotated[str, typer.Option("--type", "-t", help="[caesar|vigenere|rot13|atbash]")] = "caesar",
    key: Annotated[str, typer.Option("--key", "-k", help="Key.")] = "13",
    json_out: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
) -> None:
    """Decode text using a classical cipher."""
    result = _apply_cipher(text, cipher_type, key, mode="decode")
    if json_out:
        console.print_json(json.dumps({"cipher": cipher_type, "input": text, "output": result}))
    else:
        print_panel(f"[bright_green]{result}[/bright_green]", title=f"Decoded ({cipher_type})")


@app.command("crack")
def crack(
    text: Annotated[str, typer.Argument(help="Ciphertext to crack.")],
    cipher_type: Annotated[str, typer.Option("--type", "-t", help="Cipher type to crack (currently: caesar).")] = "caesar",
    json_out: Annotated[bool, typer.Option("--json", help="Output as JSON.")] = False,
) -> None:
    """Try all possible keys and rank by readability score."""
    if cipher_type.lower() != "caesar":
        error("Only Caesar cracking is supported.")
        raise typer.Exit(1)

    results = []
    for shift in range(1, 26):
        decoded = caesar_decode(text, shift)
        score = _readability_score(decoded)
        results.append({"shift": shift, "text": decoded, "score": score})

    results.sort(key=lambda x: x["score"], reverse=True)

    if json_out:
        console.print_json(json.dumps(results))
        return

    table = make_table("SHIFT", "SCORE", "PLAINTEXT", title="Caesar Crack — All 25 Shifts")
    for r in results:
        score_style = "bright_green" if r["score"] == results[0]["score"] else "white"
        table.add_row(
            str(r["shift"]),
            f"[{score_style}]{r['score']}[/{score_style}]",
            r["text"][:80],
        )
    console.print(table)
    console.print(f"\n[bold]Best guess (shift={results[0]['shift']}):[/bold] [bright_green]{results[0]['text']}[/bright_green]")


@app.command("tui")
def tui() -> None:
    """Open an interactive TUI for live cipher encode/decode."""
    try:
        from devha.commands._cipher_tui import CipherTUI
        app_tui = CipherTUI()
        app_tui.run()
    except ImportError:
        error("Textual is not installed. Run: pip install textual")
        raise typer.Exit(1)


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _apply_cipher(text: str, cipher_type: str, key: str, mode: str) -> str:
    ct = cipher_type.lower()
    try:
        if ct == "caesar":
            shift = int(key)
            return caesar_encode(text, shift) if mode == "encode" else caesar_decode(text, shift)
        elif ct == "rot13":
            return rot13_encode(text)
        elif ct == "atbash":
            return atbash_encode(text)
        elif ct == "vigenere":
            if not key.isalpha():
                error("Vigenere key must be alphabetic.")
                raise typer.Exit(1)
            return vigenere_encode(text, key) if mode == "encode" else vigenere_decode(text, key)
        else:
            error(f"Unknown cipher: {cipher_type}. Choose: caesar, vigenere, rot13, atbash")
            raise typer.Exit(1)
    except ValueError:
        error(f"Invalid key '{key}' for {cipher_type}.")
        raise typer.Exit(1)

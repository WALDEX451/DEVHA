"""Textual TUI for live cipher encode/decode."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Select, Label, Static
from textual.reactive import reactive

from devha.commands.cipher import caesar_encode, rot13_encode, atbash_encode, vigenere_encode

CIPHERS = ["caesar", "rot13", "atbash", "vigenere"]


class CipherTUI(App):
    """Live cipher encode/decode TUI."""

    CSS = """
    Screen { background: #0d0d0d; }
    Label { color: cyan; margin: 1 0 0 1; }
    Input { margin: 0 1; }
    Static#output { color: bright_green; margin: 1; padding: 1; border: round cyan; height: 5; }
    """

    TITLE = "devha — Cipher TUI"
    BINDINGS = [("q", "quit", "Quit"), ("ctrl+c", "quit", "Quit")]

    cipher_type: reactive[str] = reactive("caesar")
    key_value: reactive[str] = reactive("13")

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Label("Cipher type:")
            yield Select([(c, c) for c in CIPHERS], value="caesar", id="cipher_select")
            yield Label("Key (shift for caesar, phrase for vigenere):")
            yield Input(placeholder="13", id="key_input")
            yield Label("Plaintext:")
            yield Input(placeholder="Type something...", id="plain_input")
            yield Label("Output:")
            yield Static("", id="output")
        yield Footer()

    def on_select_changed(self, event: Select.Changed) -> None:
        self.cipher_type = str(event.value)
        self._update_output()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "key_input":
            self.key_value = event.value
        self._update_output()

    def _update_output(self) -> None:
        plain_input = self.query_one("#plain_input", Input)
        text = plain_input.value
        ct = self.cipher_type
        key = self.key_value or "13"
        try:
            if ct == "caesar":
                result = caesar_encode(text, int(key) if key.lstrip("-").isdigit() else 13)
            elif ct == "rot13":
                result = rot13_encode(text)
            elif ct == "atbash":
                result = atbash_encode(text)
            elif ct == "vigenere":
                result = vigenere_encode(text, key if key.isalpha() else "key")
            else:
                result = text
        except Exception:
            result = "⚠  Invalid input"
        self.query_one("#output", Static).update(result)

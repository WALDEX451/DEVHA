"""Tests for cipher module."""

import pytest
from devha.commands.cipher import (
    caesar_encode,
    caesar_decode,
    rot13_encode,
    rot13_decode,
    atbash_encode,
    atbash_decode,
    vigenere_encode,
    vigenere_decode,
    _readability_score,
    _apply_cipher,
)


class TestCaesar:
    def test_encode_basic(self):
        assert caesar_encode("ABC", 3) == "DEF"

    def test_encode_wrap(self):
        assert caesar_encode("XYZ", 3) == "ABC"

    def test_encode_lowercase(self):
        assert caesar_encode("abc", 1) == "bcd"

    def test_encode_preserves_non_alpha(self):
        assert caesar_encode("Hello, World!", 13) == "Uryyb, Jbeyq!"

    def test_decode_reverses_encode(self):
        original = "The quick brown fox"
        assert caesar_decode(caesar_encode(original, 7), 7) == original

    def test_decode_shift_13(self):
        assert caesar_decode("Uryyb", 13) == "Hello"

    def test_zero_shift_identity(self):
        text = "Hello"
        assert caesar_encode(text, 0) == text

    def test_full_alphabet_cycle(self):
        assert caesar_encode("A", 26) == "A"


class TestRot13:
    def test_encode(self):
        assert rot13_encode("Hello") == "Uryyb"

    def test_decode_is_encode(self):
        assert rot13_decode("Uryyb") == "Hello"

    def test_involution(self):
        text = "Testing ROT13!"
        assert rot13_encode(rot13_encode(text)) == text

    def test_numbers_unchanged(self):
        assert rot13_encode("abc123") == "nop123"


class TestAtbash:
    def test_encode_a_z(self):
        assert atbash_encode("A") == "Z"
        assert atbash_encode("Z") == "A"

    def test_encode_word(self):
        assert atbash_encode("ABC") == "ZYX"

    def test_involution(self):
        text = "Hello World"
        assert atbash_decode(atbash_encode(text)) == text

    def test_preserves_case(self):
        assert atbash_encode("a") == "z"
        assert atbash_encode("A") == "Z"

    def test_preserves_spaces(self):
        assert atbash_encode("A B") == "Z Y"


class TestVigenere:
    def test_encode_basic(self):
        result = vigenere_encode("HELLO", "KEY")
        assert result == "RIJVS"

    def test_decode_reverses_encode(self):
        original = "Hello World"
        encoded = vigenere_encode(original, "secret")
        assert vigenere_decode(encoded, "secret") == original

    def test_key_wraps_around(self):
        text = "AAAAAA"
        key = "AB"
        encoded = vigenere_encode(text, key)
        assert encoded == "ABABAB"

    def test_preserves_non_alpha(self):
        encoded = vigenere_encode("Hello, World!", "key")
        assert "," in encoded
        assert " " in encoded
        assert "!" in encoded


class TestReadabilityScore:
    def test_english_text_high_score(self):
        score = _readability_score("the quick brown fox jumps over the lazy dog")
        assert score > 4.5

    def test_random_garbage_low_score(self):
        score = _readability_score("ZZZZQQQXXX")
        assert score < 3.0

    def test_empty_string(self):
        assert _readability_score("") == 0.0


class TestApplyCipher:
    def test_caesar_encode(self):
        result = _apply_cipher("Hello", "caesar", "3", "encode")
        assert result == "Khoor"

    def test_rot13(self):
        result = _apply_cipher("Hello", "rot13", "0", "encode")
        assert result == "Uryyb"

    def test_atbash(self):
        result = _apply_cipher("ABC", "atbash", "0", "encode")
        assert result == "ZYX"

    def test_vigenere(self):
        result = _apply_cipher("HELLO", "vigenere", "KEY", "encode")
        assert result == "RIJVS"

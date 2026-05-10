"""Tests for portscan module."""

import socket
from unittest.mock import patch, MagicMock

import pytest
from devha.commands.portscan import _parse_port_range, _scan_port, _get_service


class TestParsePortRange:
    def test_single_range(self):
        assert _parse_port_range("1-5") == [1, 2, 3, 4, 5]

    def test_single_port(self):
        assert _parse_port_range("80") == [80]

    def test_comma_separated(self):
        assert _parse_port_range("22,80,443") == [22, 80, 443]

    def test_mixed(self):
        result = _parse_port_range("22,80-82,443")
        assert result == [22, 80, 81, 82, 443]

    def test_single_port_range(self):
        assert _parse_port_range("100-100") == [100]


class TestGetService:
    def test_known_port(self):
        # Port 80 is universally "http"
        assert _get_service(80) == "http"

    def test_ssh_port(self):
        assert _get_service(22) == "ssh"

    def test_unknown_port_returns_unknown(self):
        # Very high port unlikely to be in the services DB
        result = _get_service(65432)
        assert result == "unknown"


class TestScanPort:
    def test_open_port_returns_dict(self):
        with patch("socket.socket") as mock_socket_cls:
            mock_sock = MagicMock()
            mock_sock.__enter__ = MagicMock(return_value=mock_sock)
            mock_sock.__exit__ = MagicMock(return_value=False)
            mock_sock.connect_ex.return_value = 0
            mock_socket_cls.return_value = mock_sock

            result = _scan_port("127.0.0.1", 80, 1.0)
            assert result is not None
            assert result["port"] == 80
            assert result["status"] == "open"

    def test_closed_port_returns_none(self):
        with patch("socket.socket") as mock_socket_cls:
            mock_sock = MagicMock()
            mock_sock.__enter__ = MagicMock(return_value=mock_sock)
            mock_sock.__exit__ = MagicMock(return_value=False)
            mock_sock.connect_ex.return_value = 111  # connection refused
            mock_socket_cls.return_value = mock_sock

            result = _scan_port("127.0.0.1", 9999, 1.0)
            assert result is None

    def test_socket_error_returns_none(self):
        with patch("socket.socket") as mock_socket_cls:
            mock_sock = MagicMock()
            mock_sock.__enter__ = MagicMock(return_value=mock_sock)
            mock_sock.__exit__ = MagicMock(return_value=False)
            mock_sock.connect_ex.side_effect = OSError("network error")
            mock_socket_cls.return_value = mock_sock

            result = _scan_port("127.0.0.1", 80, 1.0)
            assert result is None

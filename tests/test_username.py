"""Tests for username module."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from devha.commands.username import _load_sites, _check_site


class TestLoadSites:
    def test_returns_dict(self):
        sites = _load_sites()
        assert isinstance(sites, dict)

    def test_has_required_sites(self):
        sites = _load_sites()
        required = ["GitHub", "Reddit", "Twitter", "Instagram"]
        for site in required:
            assert site in sites, f"{site} missing from sites.json"

    def test_site_has_url_and_error_code(self):
        sites = _load_sites()
        for name, data in sites.items():
            assert "url" in data, f"{name} missing 'url'"
            assert "error_code" in data, f"{name} missing 'error_code'"
            assert "{}" in data["url"], f"{name} url missing {{}} placeholder"

    def test_minimum_count(self):
        sites = _load_sites()
        assert len(sites) >= 50


class TestCheckSite:
    @pytest.mark.asyncio
    async def test_found_returns_found(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)

        result = await _check_site(
            mock_client,
            "GitHub",
            {"url": "https://github.com/{}", "error_code": 404},
            "torvalds",
            5.0,
        )
        assert result["status"] == "found"
        assert result["site"] == "GitHub"
        assert "torvalds" in result["url"]

    @pytest.mark.asyncio
    async def test_not_found_on_error_code(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)

        result = await _check_site(
            mock_client,
            "GitHub",
            {"url": "https://github.com/{}", "error_code": 404},
            "thisuserdoesnotexist99999",
            5.0,
        )
        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_timeout_returns_timeout(self):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        result = await _check_site(
            mock_client,
            "GitHub",
            {"url": "https://github.com/{}", "error_code": 404},
            "user",
            5.0,
        )
        assert result["status"] == "timeout"

    @pytest.mark.asyncio
    async def test_request_error_returns_error(self):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("connection error"))

        result = await _check_site(
            mock_client,
            "GitHub",
            {"url": "https://github.com/{}", "error_code": 404},
            "user",
            5.0,
        )
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_url_substitution(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_resp)

        result = await _check_site(
            mock_client,
            "TestSite",
            {"url": "https://example.com/user/{}/profile", "error_code": 404},
            "myuser",
            5.0,
        )
        assert result["url"] == "https://example.com/user/myuser/profile"

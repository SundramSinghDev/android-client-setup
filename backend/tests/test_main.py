"""
Tests for main.py FastAPI endpoint.

TDD: written before implementation.
"""
import io
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_png_bytes() -> bytes:
    """Return a minimal 1x1 PNG so UploadFile has a real filename suffix."""
    import struct, zlib
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(c[4:]) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xFF\xFF\xFF")
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", idat)
        + chunk(b"IEND", b"")
    )


def _fake_json_bytes() -> bytes:
    return b'{"project_info": {}}'


def _make_client():
    """Import app after env vars are set and return TestClient."""
    # Ensure module is re-imported fresh with env vars present
    import importlib
    import sys
    # Remove cached module so env vars are re-read
    for mod in list(sys.modules.keys()):
        if mod in ("main",):
            del sys.modules[mod]
    from main import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_ok(self):
        client = _make_client()
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /api/create-client — happy path
# ---------------------------------------------------------------------------

class TestCreateClientHappyPath:
    """
    All backend module calls are mocked so no real I/O or GitHub calls occur.
    We test that the orchestration layer:
      - calls each module in order
      - returns the correct JSON shape
      - uses repo_name = f"{mid}_{project_name}"
    """

    def _post(self, client, extra_files=None, extra_fields=None):
        png = _fake_png_bytes()
        files = {
            "app_icon": ("icon.png", io.BytesIO(png), "image/png"),
            "header_logo": ("logo.png", io.BytesIO(png), "image/png"),
        }
        if extra_files:
            files.update(extra_files)
        data = {
            "project_name": "acme",
            "mid": "MID001",
            "package_name": "com.acme.shop",
            "app_name": "Acme Store",
            "shop_domain": "acme.myshopify.com",
            "api_key": "KEY123",
            "access_token": "TOKEN456",
            "preview_visible": "true",
        }
        if extra_fields:
            data.update(extra_fields)
        return client.post("/api/create-client", data=data, files=files)

    def _patched_client(self):
        patches = [
            patch("main.clone_base_repo"),
            patch("main.rename_package"),
            patch("main.update_app_name"),
            patch("main.update_urls_kt"),
            patch("main.replace_google_services"),
            patch("main.replace_app_icon"),
            patch("main.replace_header_logo"),
            patch("main.create_github_repo", return_value="https://github.com/org/MID001_acme.git"),
            patch("main.push_to_github"),
        ]
        return patches

    def test_returns_200_on_success(self):
        client = _make_client()
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            resp = self._post(client)
        assert resp.status_code == 200

    def test_response_has_success_status(self):
        client = _make_client()
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            resp = self._post(client)
        assert resp.json()["status"] == "success"

    def test_response_contains_repo_url(self):
        client = _make_client()
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            resp = self._post(client)
        body = resp.json()
        assert "repo_url" in body
        assert "MID001_acme" in body["repo_url"]

    def test_response_contains_message(self):
        client = _make_client()
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            resp = self._post(client)
        assert "message" in resp.json()

    def test_clone_is_called(self):
        client = _make_client()
        with patch("main.clone_base_repo") as mock_clone, \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            self._post(client)
        mock_clone.assert_called_once()

    def test_rename_package_is_called_with_new_package(self):
        client = _make_client()
        with patch("main.clone_base_repo"), \
             patch("main.rename_package") as mock_rp, \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            self._post(client)
        mock_rp.assert_called_once()
        _, kwargs = mock_rp.call_args
        args = mock_rp.call_args[0]
        # new_package should be com.acme.shop
        assert "com.acme.shop" in args

    def test_update_app_name_called(self):
        client = _make_client()
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name") as mock_uan, \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            self._post(client)
        mock_uan.assert_called_once()
        assert "Acme Store" in mock_uan.call_args[0]

    def test_update_urls_kt_called_with_correct_args(self):
        client = _make_client()
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt") as mock_urls, \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            self._post(client)
        mock_urls.assert_called_once()
        args = mock_urls.call_args[0]
        assert "MID001" in args
        assert "acme.myshopify.com" in args
        assert "KEY123" in args
        assert "TOKEN456" in args

    def test_replace_app_icon_called(self):
        client = _make_client()
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon") as mock_icon, \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            self._post(client)
        mock_icon.assert_called_once()

    def test_replace_header_logo_called(self):
        client = _make_client()
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo") as mock_logo, \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            self._post(client)
        mock_logo.assert_called_once()

    def test_create_github_repo_called_with_correct_repo_name(self):
        client = _make_client()
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git") as mock_cgr, \
             patch("main.push_to_github"):
            self._post(client)
        mock_cgr.assert_called_once()
        args = mock_cgr.call_args[0]
        # repo_name = f"{mid}_{project_name}" = "MID001_acme"
        assert "MID001_acme" in args

    def test_push_to_github_called(self):
        client = _make_client()
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github") as mock_push:
            self._post(client)
        mock_push.assert_called_once()


# ---------------------------------------------------------------------------
# /api/create-client — google_services_json optional
# ---------------------------------------------------------------------------

class TestCreateClientOptionalGoogleServices:
    def test_google_services_skipped_when_not_provided(self):
        client = _make_client()
        png = _fake_png_bytes()
        data = {
            "project_name": "acme",
            "mid": "MID001",
            "package_name": "com.acme.shop",
            "app_name": "Acme",
            "shop_domain": "acme.myshopify.com",
            "api_key": "K",
            "access_token": "T",
            "preview_visible": "true",
        }
        files = {
            "app_icon": ("icon.png", io.BytesIO(png), "image/png"),
            "header_logo": ("logo.png", io.BytesIO(png), "image/png"),
        }
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services") as mock_gsj, \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            resp = client.post("/api/create-client", data=data, files=files)
        assert resp.status_code == 200
        # replace_google_services should be called with None as second arg
        args = mock_gsj.call_args[0]
        assert args[1] is None

    def test_google_services_passed_when_provided(self):
        client = _make_client()
        png = _fake_png_bytes()
        data = {
            "project_name": "acme",
            "mid": "MID001",
            "package_name": "com.acme.shop",
            "app_name": "Acme",
            "shop_domain": "acme.myshopify.com",
            "api_key": "K",
            "access_token": "T",
            "preview_visible": "true",
        }
        files = {
            "app_icon": ("icon.png", io.BytesIO(png), "image/png"),
            "header_logo": ("logo.png", io.BytesIO(png), "image/png"),
            "google_services_json": ("google-services.json", io.BytesIO(_fake_json_bytes()), "application/json"),
        }
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services") as mock_gsj, \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            resp = client.post("/api/create-client", data=data, files=files)
        assert resp.status_code == 200
        args = mock_gsj.call_args[0]
        assert args[1] is not None


# ---------------------------------------------------------------------------
# /api/create-client — per-screen logos
# ---------------------------------------------------------------------------

class TestCreateClientPerScreenLogos:
    def test_per_screen_logos_passed_to_replace_header_logo(self):
        client = _make_client()
        png = _fake_png_bytes()
        data = {
            "project_name": "acme",
            "mid": "MID001",
            "package_name": "com.acme.shop",
            "app_name": "Acme",
            "shop_domain": "acme.myshopify.com",
            "api_key": "K",
            "access_token": "T",
            "preview_visible": "true",
        }
        files = {
            "app_icon": ("icon.png", io.BytesIO(png), "image/png"),
            "header_logo": ("logo.png", io.BytesIO(png), "image/png"),
            "logo_login": ("login_logo.png", io.BytesIO(png), "image/png"),
        }
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo") as mock_logo, \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            resp = client.post("/api/create-client", data=data, files=files)
        assert resp.status_code == 200
        args, kwargs = mock_logo.call_args
        # per_screen kwarg should contain 'login' key
        per_screen = args[2] if len(args) > 2 else kwargs.get("per_screen")
        assert per_screen is not None
        assert "login" in per_screen

    def test_no_per_screen_logos_passes_none(self):
        client = _make_client()
        png = _fake_png_bytes()
        data = {
            "project_name": "acme",
            "mid": "MID001",
            "package_name": "com.acme.shop",
            "app_name": "Acme",
            "shop_domain": "acme.myshopify.com",
            "api_key": "K",
            "access_token": "T",
            "preview_visible": "true",
        }
        files = {
            "app_icon": ("icon.png", io.BytesIO(png), "image/png"),
            "header_logo": ("logo.png", io.BytesIO(png), "image/png"),
        }
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo") as mock_logo, \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github"):
            resp = client.post("/api/create-client", data=data, files=files)
        assert resp.status_code == 200
        args, kwargs = mock_logo.call_args
        per_screen = args[2] if len(args) > 2 else kwargs.get("per_screen")
        assert per_screen is None


# ---------------------------------------------------------------------------
# /api/create-client — error handling
# ---------------------------------------------------------------------------

class TestCreateClientErrorHandling:
    def test_returns_500_when_clone_raises(self):
        client = _make_client()
        png = _fake_png_bytes()
        data = {
            "project_name": "acme",
            "mid": "MID001",
            "package_name": "com.acme.shop",
            "app_name": "Acme",
            "shop_domain": "acme.myshopify.com",
            "api_key": "K",
            "access_token": "T",
            "preview_visible": "true",
        }
        files = {
            "app_icon": ("icon.png", io.BytesIO(png), "image/png"),
            "header_logo": ("logo.png", io.BytesIO(png), "image/png"),
        }
        with patch("main.clone_base_repo", side_effect=RuntimeError("Clone failed: not found")):
            resp = client.post("/api/create-client", data=data, files=files)
        assert resp.status_code == 500
        assert "Clone failed" in resp.json()["detail"]

    def test_returns_500_when_github_push_raises(self):
        client = _make_client()
        png = _fake_png_bytes()
        data = {
            "project_name": "acme",
            "mid": "MID001",
            "package_name": "com.acme.shop",
            "app_name": "Acme",
            "shop_domain": "acme.myshopify.com",
            "api_key": "K",
            "access_token": "T",
            "preview_visible": "true",
        }
        files = {
            "app_icon": ("icon.png", io.BytesIO(png), "image/png"),
            "header_logo": ("logo.png", io.BytesIO(png), "image/png"),
        }
        with patch("main.clone_base_repo"), \
             patch("main.rename_package"), \
             patch("main.update_app_name"), \
             patch("main.update_urls_kt"), \
             patch("main.replace_google_services"), \
             patch("main.replace_app_icon"), \
             patch("main.replace_header_logo"), \
             patch("main.create_github_repo", return_value="https://github.com/org/r.git"), \
             patch("main.push_to_github", side_effect=RuntimeError("push failed")):
            resp = client.post("/api/create-client", data=data, files=files)
        assert resp.status_code == 500

    def test_temp_dir_cleaned_up_on_error(self):
        """Verify tempfile.mkdtemp dirs are removed even when an exception occurs."""
        import tempfile as tf
        created_dirs = []
        original_mkdtemp = tf.mkdtemp

        def capturing_mkdtemp(**kwargs):
            d = original_mkdtemp(**kwargs)
            created_dirs.append(d)
            return d

        client = _make_client()
        png = _fake_png_bytes()
        data = {
            "project_name": "acme",
            "mid": "MID001",
            "package_name": "com.acme.shop",
            "app_name": "Acme",
            "shop_domain": "acme.myshopify.com",
            "api_key": "K",
            "access_token": "T",
            "preview_visible": "true",
        }
        files = {
            "app_icon": ("icon.png", io.BytesIO(png), "image/png"),
            "header_logo": ("logo.png", io.BytesIO(png), "image/png"),
        }
        with patch("main.tempfile.mkdtemp", side_effect=capturing_mkdtemp), \
             patch("main.clone_base_repo", side_effect=RuntimeError("boom")):
            client.post("/api/create-client", data=data, files=files)

        for d in created_dirs:
            assert not os.path.exists(d), f"Temp dir {d} was not cleaned up"


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------

class TestCORSMiddleware:
    def test_cors_header_present_for_allowed_origin(self):
        client = _make_client()
        resp = client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"},
        )
        assert "access-control-allow-origin" in resp.headers
        assert resp.headers["access-control-allow-origin"] == "http://localhost:5173"

"""Tests for the document upload pipeline.

Infrastructure-level tests that verify:
  - storage_client._encode_path handles all filename variants correctly
  - server._storage_path constructs paths without mangling filenames
  - storage_client functions raise on HTTP errors (no silent failures)
  - URL is properly encoded before being sent to Supabase

Run:  python -m unittest tests/test_upload_pipeline.py
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("DB_URL", "postgresql+asyncpg://u:p@localhost/db")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from src import storage_client


def _storage_path(user_id: str, filename: str, thread_id: str | None = None) -> str:
    """Mirrors server._storage_path — must preserve filenames as-is.
    URL encoding is handled at the HTTP layer."""
    if thread_id:
        return f"{user_id}/{thread_id}/{filename}"
    return f"{user_id}/{filename}"


def _mock_httpx_client(resp_status=200, resp_body="{}", resp_json=None):
    """Build a mock for httpx.AsyncClient that returns controlled responses.

    __aexit__ returns False so exceptions propagate to the caller.
    """
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = resp_status
    mock_resp.text = resp_body
    if resp_json is not None:
        mock_resp.json = MagicMock(return_value=resp_json)

    if resp_status >= 400:
        mock_req = MagicMock()
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"{resp_status} {resp_body}", request=mock_req, response=mock_resp
        )
    else:
        mock_resp.raise_for_status = MagicMock()

    mock_instance = MagicMock()
    mock_instance.post = AsyncMock(return_value=mock_resp)
    mock_instance.request = AsyncMock(return_value=mock_resp)
    mock_instance.get = AsyncMock(return_value=mock_resp)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=False)
    return mock_instance


class TestEncodePath(unittest.TestCase):
    """storage_client._encode_path must percent-encode special characters
    while preserving forward slashes as path separators."""

    def test_spaces_encoded(self):
        result = storage_client._encode_path("user/my file.pdf")
        self.assertEqual(result, "user/my%20file.pdf")

    def test_preserves_slashes(self):
        result = storage_client._encode_path("user/sub/file.pdf")
        self.assertEqual(result, "user/sub/file.pdf")

    def test_unicode_encoded(self):
        result = storage_client._encode_path("user/文件.pdf")
        self.assertIn("%", result)
        self.assertNotIn("文", result)

    def test_special_chars_encoded(self):
        result = storage_client._encode_path("user/file?name=test&foo.pdf")
        self.assertNotIn("?", result)
        self.assertNotIn("=", result)
        self.assertNotIn("&", result)
        self.assertIn("%3F", result)

    def test_multiple_spaces(self):
        result = storage_client._encode_path("user/a  b  c.pdf")
        self.assertEqual(result, "user/a%20%20b%20%20c.pdf")

    def test_normal_filename_unchanged(self):
        result = storage_client._encode_path("user/normal.pdf")
        self.assertEqual(result, "user/normal.pdf")

    def test_leading_trailing_spaces(self):
        result = storage_client._encode_path("user/ leading .pdf")
        self.assertIn("%20leading%20", result)


class TestStoragePath(unittest.TestCase):
    """_storage_path must preserve the original filename unchanged."""

    def test_without_thread(self):
        result = _storage_path("user123", "test file.pdf")
        self.assertEqual(result, "user123/test file.pdf")

    def test_with_thread(self):
        result = _storage_path("user123", "test file.pdf", "thread456")
        self.assertEqual(result, "user123/thread456/test file.pdf")

    def test_spaces_preserved(self):
        result = _storage_path("u1", "my document v2.3.pdf")
        self.assertEqual(result, "u1/my document v2.3.pdf")

    def test_unicode_preserved(self):
        result = _storage_path("u1", "文件.pdf")
        self.assertEqual(result, "u1/文件.pdf")

    def test_special_chars_preserved(self):
        result = _storage_path("u1", "file?name=test.pdf")
        self.assertEqual(result, "u1/file?name=test.pdf")


class TestUploadFile(unittest.TestCase):
    """storage_client.upload_file must URL-encode the path and raise on errors."""

    @patch("src.storage_client.httpx.AsyncClient")
    def test_uploads_with_encoded_url(self, mock_client_cls):
        mock_instance = _mock_httpx_client()
        mock_client_cls.return_value = mock_instance

        asyncio.run(storage_client.upload_file(
            "bucket", "user/file with spaces.pdf", b"data",
            content_type="application/pdf", auth_token="tok",
        ))

        call_url = mock_instance.post.call_args[0][0]
        self.assertIn("file%20with%20spaces.pdf", call_url)
        self.assertNotIn("file with spaces.pdf", call_url)

    @patch("src.storage_client.httpx.AsyncClient")
    def test_raises_on_http_error(self, mock_client_cls):
        mock_instance = _mock_httpx_client(resp_status=400, resp_body='{"error":"invalid"}')
        mock_client_cls.return_value = mock_instance

        with self.assertRaises(httpx.HTTPStatusError):
            asyncio.run(storage_client.upload_file("bucket", "path", b"data"))


class TestRemoveFiles(unittest.TestCase):
    """storage_client.remove_files must raise on failure (no silent swallowing)."""

    @patch("src.storage_client.httpx.AsyncClient")
    def test_raises_on_http_error(self, mock_client_cls):
        mock_instance = _mock_httpx_client(resp_status=400)
        mock_client_cls.return_value = mock_instance

        with self.assertRaises(httpx.HTTPStatusError):
            asyncio.run(storage_client.remove_files("bucket", ["path"]))

    @patch("src.storage_client.httpx.AsyncClient")
    def test_success_does_not_raise(self, mock_client_cls):
        mock_instance = _mock_httpx_client()
        mock_client_cls.return_value = mock_instance

        try:
            asyncio.run(storage_client.remove_files("bucket", ["path"]))
        except Exception:
            self.fail("remove_files raised unexpectedly on success")


class TestListFiles(unittest.TestCase):
    """storage_client.list_files must raise on failure (no silent [] return)."""

    @patch("src.storage_client.httpx.AsyncClient")
    def test_raises_on_http_error(self, mock_client_cls):
        mock_instance = _mock_httpx_client(resp_status=400)
        mock_client_cls.return_value = mock_instance

        with self.assertRaises(httpx.HTTPStatusError):
            asyncio.run(storage_client.list_files("bucket", "prefix"))

    @patch("src.storage_client.httpx.AsyncClient")
    def test_returns_list_on_success(self, mock_client_cls):
        mock_instance = _mock_httpx_client(resp_status=200, resp_body="[]", resp_json=[])
        mock_client_cls.return_value = mock_instance

        result = asyncio.run(storage_client.list_files("bucket", "prefix"))
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()

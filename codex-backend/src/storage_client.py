import os

import httpx
from dotenv import load_dotenv

from src.log_utils import logger

load_dotenv()

_SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
_SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
_SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")


def _auth_headers(auth_token: str | None = None) -> dict:
    if auth_token:
        return {
            "Authorization": f"Bearer {auth_token}",
            "apiKey": _SUPABASE_ANON_KEY,
        }
    return {
        "Authorization": f"Bearer {_SUPABASE_ANON_KEY}",
        "apiKey": _SUPABASE_ANON_KEY,
    }


def _file_url(bucket: str, path: str) -> str:
    return f"{_SUPABASE_URL}/storage/v1/object/{bucket}/{path}"


def upload_file(bucket: str, path: str, data: bytes, content_type: str | None = None, auth_token: str | None = None) -> None:
    url = _file_url(bucket, path)
    headers = _auth_headers(auth_token)
    headers["Content-Type"] = content_type or "application/octet-stream"
    headers["x-upsert"] = "true"
    try:
        resp = httpx.post(url, headers=headers, content=data, timeout=30)
        resp.raise_for_status()
        logger.info(f"Uploaded to storage: {bucket}/{path}")
    except Exception as e:
        logger.error(f"Storage upload failed for {bucket}/{path}: {e}")
        raise


def download_file(bucket: str, path: str, auth_token: str | None = None) -> bytes:
    url = _file_url(bucket, path)
    try:
        resp = httpx.get(url, headers=_auth_headers(auth_token), timeout=30)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.error(f"Storage download failed for {bucket}/{path}: {e}")
        raise


def list_files(bucket: str, prefix: str, auth_token: str | None = None) -> list[dict]:
    url = f"{_SUPABASE_URL}/storage/v1/object/list/{bucket}"
    try:
        resp = httpx.post(url, headers=_auth_headers(auth_token), json={"prefix": prefix, "limit": 100, "offset": 0}, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Storage list failed for {bucket}/{prefix}: {e}")
        return []


def remove_files(bucket: str, paths: list[str], auth_token: str | None = None) -> None:
    url = f"{_SUPABASE_URL}/storage/v1/object/{bucket}/remove"
    try:
        resp = httpx.post(url, headers=_auth_headers(auth_token), json={"prefixes": paths}, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Storage remove failed for {bucket}/{paths}: {e}")


def ensure_bucket(bucket: str) -> None:
    if not _SUPABASE_SERVICE_KEY:
        logger.warning("SUPABASE_SERVICE_KEY not set; skipping bucket auto-creation")
        return
    url = f"{_SUPABASE_URL}/storage/v1/buckets"
    headers = {
        "Authorization": f"Bearer {_SUPABASE_SERVICE_KEY}",
        "apiKey": _SUPABASE_SERVICE_KEY,
    }
    try:
        resp = httpx.get(f"{url}/{bucket}", headers=headers, timeout=10)
        if resp.status_code == 404:
            resp = httpx.post(
                url,
                headers=headers,
                json={
                    "id": bucket,
                    "name": bucket,
                    "public": False,
                    "file_size_limit": 52428800,
                    "allowed_mime_types": ["application/pdf"],
                },
                timeout=10,
            )
            resp.raise_for_status()
            logger.info(f"Created storage bucket: {bucket}")
        else:
            logger.info(f"Storage bucket already exists: {bucket}")
    except Exception as e:
        logger.error(f"Failed to ensure bucket {bucket} exists: {e}")

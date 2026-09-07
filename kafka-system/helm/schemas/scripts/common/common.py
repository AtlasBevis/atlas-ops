#!/usr/bin/env python3
"""Shared helpers """

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc

def path_seg(value: str) -> str:
    return urllib.parse.quote(str(value), safe="")

def api_request(method: str, url: str, body: dict | None = None) -> tuple[int, str]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"API request failed: {method} {url}: {e}"
        ) from e


def get_json(url: str, *, allow_404: bool = False) -> dict[str, Any]:
    code, text = api_request("GET", url)
    if allow_404 and code == 404:
        return {}
    if code != 200:
        raise RuntimeError(f"GET {url} failed ({code}): {text}")
    return json.loads(text) if text else {}

def get_json_list(url: str, *, allow_404: bool = False) -> list[Any]:
    code, text = api_request("GET", url)
    if allow_404 and code == 404:
        return []
    if code != 200:
        raise RuntimeError(f"GET {url} failed ({code}): {text}")
    data = json.loads(text) if text else []
    if not isinstance(data, list):
        raise TypeError(f"GET {url} expected array, got {type(data).__name__}")
    return data

def post_json(url: str, body: dict) -> int:
    """POST JSON. Returns 200 or 409; other codes raise."""
    code, text = api_request("POST", url, body=body)
    if code in (200, 204, 409):
        return code
    raise RuntimeError(f"POST {url} failed ({code}): {text}")


def put_json(url: str, body: dict) -> int:
    """PUT JSON. Returns 200 or 204; other codes raise."""
    code, text = api_request("PUT", url, body=body)
    if code in (200, 204):
        return code
    raise RuntimeError(f"PUT {url} failed ({code}): {text}")


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML object: {path}")
    return data


def require(data: dict, key: str, path: Path) -> Any:
    if key not in data or data[key] in (None, "", []):
        raise ValueError(f"Missing required key '{key}' in {path}")
    return data[key]


def content_payload(content: str) -> dict:
    return {"content": content, "contentType": "application/json"}

"""
Version update checker for CodeTrellis.

Checks PyPI for newer versions and notifies the user in the terminal.
Results are cached locally so the check runs at most once per day.
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple


# How often to check (in seconds) — once per 24 hours
_CHECK_INTERVAL = 86400

# Where to cache the last check result
_CACHE_FILE = Path.home() / ".codetrellis" / ".update_check"


def _get_cache_dir() -> Path:
    """Ensure the cache directory exists and return the cache file path."""
    _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    return _CACHE_FILE


def _read_cache() -> Optional[dict]:
    """Read cached update check result."""
    cache_file = _get_cache_dir()
    if not cache_file.exists():
        return None
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        return data
    except (json.JSONDecodeError, OSError):
        return None


def _write_cache(latest_version: str) -> None:
    """Write update check result to cache."""
    cache_file = _get_cache_dir()
    try:
        cache_file.write_text(
            json.dumps({"ts": time.time(), "latest": latest_version}),
            encoding="utf-8",
        )
    except OSError:
        pass


def _fetch_latest_version() -> Optional[str]:
    """Fetch the latest version from PyPI (timeout: 3s)."""
    try:
        req = urllib.request.Request(
            "https://pypi.org/pypi/codetrellis/json",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("info", {}).get("version")
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        return None


def _parse_version(v: str) -> Tuple[int, ...]:
    """Parse a PEP 440 version string into a tuple for comparison."""
    parts = []
    for seg in v.split("."):
        try:
            parts.append(int(seg))
        except ValueError:
            break
    return tuple(parts)


def _is_newer(latest: str, current: str) -> bool:
    """Return True if *latest* is strictly newer than *current*."""
    return _parse_version(latest) > _parse_version(current)


def check_for_update(current_version: str) -> Optional[str]:
    """Check if a newer version of CodeTrellis is available on PyPI.

    Returns the latest version string if an update is available,
    or None if already up-to-date (or if the check was skipped/failed).

    The check is cached for 24 hours so it doesn't slow down every run.
    """
    # Check cache first
    cached = _read_cache()
    if cached:
        elapsed = time.time() - cached.get("ts", 0)
        if elapsed < _CHECK_INTERVAL:
            latest = cached.get("latest", "")
            if latest and _is_newer(latest, current_version):
                return latest
            return None

    # Fetch from PyPI
    latest = _fetch_latest_version()
    if latest:
        _write_cache(latest)
        if _is_newer(latest, current_version):
            return latest

    return None


def _is_editable_install() -> bool:
    """Return True if codetrellis is installed in editable (dev) mode."""
    try:
        import importlib.metadata
        dist = importlib.metadata.distribution("codetrellis")
        direct_url_text = dist.read_text("direct_url.json")
        if direct_url_text:
            data = json.loads(direct_url_text)
            return bool(data.get("dir_info", {}).get("editable"))
    except Exception:
        pass
    return False


def print_update_notice(current_version: str) -> None:
    """Print an update notice to stderr if a newer version is available.

    This is a no-op if:
    - Already on the latest version
    - Running as an editable (development) install
    - The check was performed recently (cached for 24 hours)
    - The network request fails (offline, timeout, etc.)
    - The CODETRELLIS_NO_UPDATE_CHECK env variable is set
    """
    import os
    import sys

    if os.environ.get("CODETRELLIS_NO_UPDATE_CHECK"):
        return

    if _is_editable_install():
        return

    try:
        latest = check_for_update(current_version)
        if latest:
            print(
                f"\n[CodeTrellis] Update available: {current_version} → {latest}"
                f"\n[CodeTrellis] Run: pip install --upgrade codetrellis\n",
                file=sys.stderr,
            )
    except Exception:
        # Never let the update check break the CLI
        pass

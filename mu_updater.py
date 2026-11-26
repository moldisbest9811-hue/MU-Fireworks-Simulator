"""
MU Fireworks Simulator updater
Checks GitHub for updates, asks before installing, and keeps a backup.
Uses only Python's standard library.
"""

import json
import os
import shutil
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GAME_FILE = ROOT / "mu_fireworks.py"
VERSION_FILE = ROOT / ".mu_fireworks_version"
MANIFEST_URL = (
    "https://raw.githubusercontent.com/"
    "moldisbest9811-hue/MU-Fireworks-Simulator/main/version.json"
)
TIMEOUT = 20


def read_local_version():
    try:
        return VERSION_FILE.read_text(encoding="utf-8").strip() or "0.0.0"
    except OSError:
        return "0.0.0"


def version_key(value):
    try:
        return tuple(int(part) for part in value.split("."))
    except (TypeError, ValueError):
        raise ValueError(f"Invalid version number: {value!r}")


def uncached_url(url):
    """Add a unique query string to avoid stale CDN/browser cache responses."""
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("update_check", str(time.time_ns())))
    return urllib.parse.urlunsplit((
        parsed.scheme, parsed.netloc, parsed.path,
        urllib.parse.urlencode(query), parsed.fragment
    ))


def fetch_bytes(url):
    request = urllib.request.Request(
        uncached_url(url),
        headers={
            "User-Agent": "MU-Fireworks-Simulator-Updater/1.1",
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read()


def pause_exit(code):
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass
    return code


def main():
    print("=" * 58)
    print(" MU FIREWORKS SIMULATOR — UPDATER")
    print("=" * 58)
    print("Checking GitHub (fresh manifest request)...\n")

    try:
        manifest_data = fetch_bytes(MANIFEST_URL)
        manifest = json.loads(manifest_data.decode("utf-8"))
        latest_version = manifest["version"]
        game_url = manifest["game_url"]
        version_key(latest_version)
        if not game_url.startswith("https://raw.githubusercontent.com/"):
            raise ValueError("The update URL is not an approved GitHub raw URL.")
    except (OSError, urllib.error.URLError, UnicodeError,
            json.JSONDecodeError, KeyError, ValueError) as error:
        print(f"Could not check for updates: {error}")
        return pause_exit(1)

    local_version = read_local_version()
    print(f"Installed version: {local_version}")
    print(f"Latest version:    {latest_version}")

    try:
        is_newer = version_key(latest_version) > version_key(local_version)
    except ValueError as error:
        print(error)
        return pause_exit(1)

    if not is_newer:
        print("\nYou're already up to date.")
        return pause_exit(0)

    print(f"\nUPDATE AVAILABLE: {local_version} -> {latest_version}")
    try:
        answer = input("Download and install it now? [Y/n]: ").strip().lower()
    except EOFError:
        answer = "n"
    if answer not in ("", "y", "yes"):
        print("Update skipped.")
        return 0

    temporary_path = None
    try:
        new_code = fetch_bytes(game_url)
        source = new_code.decode("utf-8")
        compile(source, str(GAME_FILE), "exec")

        if not GAME_FILE.exists():
            raise FileNotFoundError(
                f"{GAME_FILE.name} is missing. Put the updater beside the game."
            )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = ROOT / f"mu_fireworks_backup_{timestamp}.py"
        shutil.copy2(GAME_FILE, backup)

        with tempfile.NamedTemporaryFile(
            mode="wb", dir=ROOT, prefix="mu_update_", suffix=".tmp",
            delete=False
        ) as temporary:
            temporary.write(new_code)
            temporary_path = Path(temporary.name)

        os.replace(temporary_path, GAME_FILE)
        temporary_path = None
        VERSION_FILE.write_text(latest_version, encoding="utf-8")

        print("\nUpdate installed successfully!")
        print(f"Backup saved as: {backup.name}")
        print("The launcher will now start the updated game.")
        return pause_exit(0)

    except Exception as error:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
        print(f"\nUpdate failed: {error}")
        print("Your existing game file was preserved.")
        return pause_exit(1)


if __name__ == "__main__":
    raise SystemExit(main())

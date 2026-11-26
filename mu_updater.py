"""
MU Fireworks Simulator updater
Checks the project's GitHub version manifest and installs updates on confirmation.
Uses only Python's standard library.
"""

import json
import os
import shutil
import sys
import tempfile
import urllib.error
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
TIMEOUT = 12


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


def fetch_bytes(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "MU-Fireworks-Simulator-Updater/1.0"},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read()


def main():
    print("=" * 58)
    print(" MU FIREWORKS SIMULATOR — UPDATER")
    print("=" * 58)
    print("Checking GitHub for updates...\n")

    try:
        manifest_data = fetch_bytes(MANIFEST_URL)
        manifest = json.loads(manifest_data.decode("utf-8"))
        latest_version = manifest["version"]
        game_url = manifest["game_url"]
        version_key(latest_version)
        if not game_url.startswith("https://raw.githubusercontent.com/"):
            raise ValueError("The update URL is not an approved GitHub raw URL.")
    except (OSError, urllib.error.URLError, UnicodeError, json.JSONDecodeError,
            KeyError, ValueError) as error:
        print(f"Could not check for updates: {error}")
        input("\nPress Enter to close...")
        return 1

    local_version = read_local_version()
    print(f"Installed version: {local_version}")
    print(f"Latest version:    {latest_version}")

    try:
        is_newer = version_key(latest_version) > version_key(local_version)
    except ValueError as error:
        print(error)
        input("\nPress Enter to close...")
        return 1

    if not is_newer:
        print("\nYou're up to date!")
        input("\nPress Enter to close...")
        return 0

    print("\nA new version is available.")
    answer = input("Download and install it now? [Y/n]: ").strip().lower()
    if answer not in ("", "y", "yes"):
        print("Update skipped.")
        return 0

    try:
        new_code = fetch_bytes(game_url)
        # Validate syntax before touching the installed game.
        compile(new_code.decode("utf-8"), str(GAME_FILE), "exec")

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
        VERSION_FILE.write_text(latest_version, encoding="utf-8")

        print("\nUpdate installed successfully!")
        print(f"Backup saved as: {backup.name}")
        print("Start the game with: py mu_fireworks.py")
        input("\nPress Enter to close...")
        return 0

    except Exception as error:
        try:
            if "temporary_path" in locals() and temporary_path.exists():
                temporary_path.unlink()
        except OSError:
            pass
        print(f"\nUpdate failed: {error}")
        print("Your existing game file has not been intentionally removed.")
        input("\nPress Enter to close...")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

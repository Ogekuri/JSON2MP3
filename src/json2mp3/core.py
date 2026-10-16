"""Command-line interface, update checks, and ID3/JSON synchronisation."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import __version__

PROGRAM = "json2mp3"
OWNER = "Ogekuri"
REPOSITORY = "JSON2MP3"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/releases/latest"
HTTP_TIMEOUT_SECONDS = 2
IDLE_DELAY_SECONDS = 3600
ERROR_IDLE_DELAY_SECONDS = 86400
CACHE_FILE = Path.home() / ".cache" / PROGRAM / "check_version_idle-time.json"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


HELP_TEXT = f"""Usage: {PROGRAM} [command] [options] ({__version__})

Management Commands:
  --upgrade   - Reinstall {PROGRAM} on Linux; print manual command elsewhere.
  --uninstall - Uninstall {PROGRAM} on Linux; print manual command elsewhere.
  --ver       - Print the {PROGRAM} version.
  --version   - Print the {PROGRAM} version.
  --help      - Print the full help screen or the help text of a specific command.

Commands:
  ...
"""


def _human_timestamp(timestamp: float) -> str:
    """Return a local, human-readable representation of an epoch timestamp."""
    return datetime.fromtimestamp(timestamp).astimezone().isoformat(timespec="seconds")


def _cache_path() -> Path:
    """Return the canonical per-user version-check cache path."""
    return CACHE_FILE


def _write_cache(delay: int, now: float | None = None) -> None:
    """Persist the successful-check or backoff window in the required JSON format."""
    checked_at = time.time() if now is None else now
    idle_until = checked_at + delay
    data = {
        "last_check_epoch": checked_at,
        "last_check_human": _human_timestamp(checked_at),
        "idle_time_epoch": idle_until,
        "idle_time_human": _human_timestamp(idle_until),
    }
    cache_file = _cache_path()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _cache_is_active(now: float | None = None) -> bool:
    """Return whether the last check's idle window is still active."""
    try:
        data = json.loads(_cache_path().read_text(encoding="utf-8"))
        idle_until = float(data["idle_time_epoch"])
    except (OSError, ValueError, TypeError, KeyError):
        return False
    current_time = time.time() if now is None else now
    return idle_until > current_time


def _version_key(version: str) -> tuple[int, ...] | None:
    """Turn a conventional release tag (``v1.2.3``) into a comparable tuple."""
    normalized = version.strip().lstrip("vV")
    parts = normalized.split(".")
    if not parts or any(not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def _is_newer_version(candidate: str, installed: str) -> bool:
    """Compare release tags without adding a runtime dependency for one comparison."""
    candidate_key = _version_key(candidate)
    installed_key = _version_key(installed)
    if candidate_key is None or installed_key is None:
        return candidate.strip().lstrip("vV") != installed.strip().lstrip("vV")
    width = max(len(candidate_key), len(installed_key))
    return candidate_key + (0,) * (width - len(candidate_key)) > installed_key + (0,) * (width - len(installed_key))


def _print_coloured(colour: str, message: str) -> None:
    print(f"{colour}{message}{RESET}")


def _fetch_latest_version(opener: Callable[..., Any] | None = None) -> str:
    """Fetch and validate the latest GitHub release tag."""
    request = Request(LATEST_RELEASE_URL, headers={"Accept": "application/vnd.github+json", "User-Agent": PROGRAM})
    request_opener = urlopen if opener is None else opener
    with request_opener(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        status = response.getcode()
        if status is not None and not 200 <= status < 300:
            raise RuntimeError(f"HTTP {status}")
        payload = json.loads(response.read().decode("utf-8"))
    tag_name = payload.get("tag_name")
    if not isinstance(tag_name, str) or not tag_name.strip():
        raise ValueError("latest release response does not contain a tag_name")
    return tag_name.strip()


def check_for_update(*, force: bool = False, opener: Callable[..., Any] | None = None) -> bool:
    """Check GitHub when permitted and report a newer installed release.

    A failed request gets a one-day backoff; every valid response gets the normal
    one-hour backoff.  Failures are intentionally non-fatal to the CLI.
    """
    if not force and _cache_is_active():
        return False

    try:
        latest = _fetch_latest_version(opener)
    except HTTPError as error:
        message = f"Version check failed: HTTP {error.code} {error.reason}".rstrip()
    except URLError as error:
        message = f"Version check failed: {error.reason}"
    except (OSError, ValueError, RuntimeError) as error:
        message = f"Version check failed: {error}"
    else:
        try:
            _write_cache(IDLE_DELAY_SECONDS)
        except OSError as error:
            _print_coloured(RED, f"Version check cache error: {error}")
        if _is_newer_version(latest, __version__):
            _print_coloured(GREEN, f"Versione Disponibile: {latest} | Versione Installata: {__version__}")
            return True
        return False

    _print_coloured(RED, message)
    try:
        _write_cache(ERROR_IDLE_DELAY_SECONDS)
    except OSError as cache_error:
        _print_coloured(RED, f"Version check cache error: {cache_error}")
    return False


def _run_tool_command(action: str) -> int:
    """Install or remove this tool, only automatically on Linux."""
    if action == "upgrade":
        command = ["uv", "tool", "install", PROGRAM, "--force", "--from", f"git+https://github.com/{OWNER}/{REPOSITORY}.git"]
    else:
        command = ["uv", "tool", "uninstall", PROGRAM]

    manual_command = " ".join(command)
    if platform.system() != "Linux":
        print(f"Warning: automatic {action} is supported only on Linux.")
        print(f"Run manually: {manual_command}")
        return 0

    try:
        return subprocess.run(command, check=False).returncode
    except OSError as error:
        _print_coloured(RED, f"Unable to run {manual_command}: {error}")
        return 1


def _load_tracks(json_file: Path) -> list[dict[str, Any]]:
    """Read either ``{\"files\": [...]}`` or ``{\"path.mp3\": {tags}}`` JSON."""
    try:
        document = json.loads(json_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON file {json_file}: {error}") from error

    if isinstance(document, dict) and isinstance(document.get("files"), list):
        tracks = document["files"]
    elif isinstance(document, dict) and isinstance(document.get("tracks"), list):
        tracks = document["tracks"]
    elif isinstance(document, dict):
        tracks = [{"path": path, "tags": tags} for path, tags in document.items()]
    else:
        raise ValueError("JSON root must be an object")
    if not all(isinstance(track, dict) for track in tracks):
        raise ValueError("every track must be an object")
    return tracks


def _write_id3_tags(audio_file: Path, tags: dict[str, Any]) -> None:
    """Write supported JSON metadata to the target MP3's ID3 tag."""
    try:
        from mutagen.id3 import COMM, TALB, TCON, TDRC, TIT2, TPE1, TPE2, TPOS, TRCK, ID3, ID3NoHeaderError
    except ImportError as error:  # pragma: no cover - protects direct source execution
        raise RuntimeError("ID3 support requires the 'mutagen' package") from error

    try:
        id3 = ID3(audio_file)
    except ID3NoHeaderError:
        id3 = ID3()

    frames = {
        "title": (TIT2, "text"), "artist": (TPE1, "text"), "album": (TALB, "text"),
        "albumartist": (TPE2, "text"), "date": (TDRC, "text"), "year": (TDRC, "text"),
        "genre": (TCON, "text"), "tracknumber": (TRCK, "text"), "discnumber": (TPOS, "text"),
    }
    for name, (frame_type, attribute) in frames.items():
        if name in tags and tags[name] is not None:
            id3.delall(frame_type.__name__)
            id3.add(frame_type(encoding=3, **{attribute: [str(tags[name])] }))
    if "comment" in tags and tags["comment"] is not None:
        id3.delall("COMM")
        id3.add(COMM(encoding=3, lang="eng", desc="", text=[str(tags["comment"])]))
    id3.save(audio_file)


def sync_from_json(json_filename: str, *, dry_run: bool = False) -> int:
    """Synchronise supported ID3 metadata from a JSON manifest to MP3 files."""
    json_file = Path(json_filename).expanduser().resolve()
    try:
        tracks = _load_tracks(json_file)
    except ValueError as error:
        _print_coloured(RED, f"Error: {error}")
        return 2

    failures = 0
    for track in tracks:
        path = track.get("path", track.get("file"))
        tags = track.get("tags")
        if not isinstance(path, str) or not isinstance(tags, dict):
            _print_coloured(RED, "Error: each track requires string 'path' and object 'tags'.")
            failures += 1
            continue
        audio_file = Path(path).expanduser()
        if not audio_file.is_absolute():
            audio_file = json_file.parent / audio_file
        if not audio_file.is_file():
            _print_coloured(RED, f"Error: MP3 file not found: {audio_file}")
            failures += 1
            continue
        if dry_run:
            print(f"Would update: {audio_file}")
            continue
        try:
            _write_id3_tags(audio_file, tags)
        except Exception as error:  # A malformed audio file must not stop remaining tracks.
            _print_coloured(RED, f"Error updating {audio_file}: {error}")
            failures += 1
        else:
            print(f"Updated: {audio_file}")
    return 1 if failures else 0


def _sync_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=f"{PROGRAM} sync", description="Synchronise ID3 tags from a JSON manifest.")
    parser.add_argument("json_file", help="JSON manifest containing files/tracks and their tags")
    parser.add_argument("--dry-run", action="store_true", help="show files that would be changed")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return its process exit status."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    check_for_update(force="--ver" in arguments or "--version" in arguments)

    if not arguments or arguments == ["--help"]:
        print(HELP_TEXT, end="")
        return 0
    if arguments[0] == "--help" and len(arguments) == 2 and arguments[1] == "sync":
        _sync_parser().print_help()
        return 0
    if arguments in (["--ver"], ["--version"]):
        print(__version__)
        return 0
    if arguments == ["--upgrade"]:
        return _run_tool_command("upgrade")
    if arguments == ["--uninstall"]:
        return _run_tool_command("uninstall")
    if arguments[0] == "sync":
        parsed = _sync_parser().parse_args(arguments[1:])
        return sync_from_json(parsed.json_file, dry_run=parsed.dry_run)

    _print_coloured(RED, f"Unknown command: {' '.join(arguments)}")
    print(HELP_TEXT, end="")
    return 2

# Files Structure
```
.
└── src
    ├── j2m
    │   ├── __init__.py
    │   ├── __main__.py
    │   └── core.py
    └── json2mp3
        ├── __init__.py
        ├── __main__.py
        ├── core.py
        └── tag_manifest.py
```

# __init__.py | Python | 13L | 0 symbols | 1 imports | 7 comments
> Path: `src/j2m/__init__.py`

## Imports
```
from .core import main  # noqa: F401
```


---

# __main__.py | Python | 11L | 0 symbols | 2 imports | 5 comments
> Path: `src/j2m/__main__.py`

## Imports
```
from .core import main
import sys
```


---

# core.py | Python | 9L | 0 symbols | 1 imports | 1 comments
> Path: `src/j2m/core.py`

## Imports
```
from json2mp3.core import main
```


---

# __init__.py | Python | 5L | 0 symbols | 0 imports | 1 comments
> Path: `src/json2mp3/__init__.py`


---

# __main__.py | Python | 6L | 0 symbols | 1 imports | 1 comments
> Path: `src/json2mp3/__main__.py`

## Imports
```
from .core import main
```


---

# core.py | Python | 348L | 28 symbols | 17 imports | 27 comments
> Path: `src/json2mp3/core.py`

## Imports
```
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
from .tag_manifest import tags_extract, update_tags
from mutagen.id3 import ID3
from mutagen.id3._frames import COMM, TALB, TCON, TDRC, TIT2, TPE1, TPE2, TPOS, TRCK
from mutagen.id3._util import ID3NoHeaderError
```

## Definitions

- var `PROGRAM = "json2mp3"` (L20)
- var `OWNER = "Ogekuri"` (L21)
- var `REPOSITORY = "JSON2MP3"` (L22)
- var `LATEST_RELEASE_URL = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/releases/latest"` (L23)
- var `HTTP_TIMEOUT_SECONDS = 2` (L24)
- var `IDLE_DELAY_SECONDS = 3600` (L25)
- var `ERROR_IDLE_DELAY_SECONDS = 86400` (L26)
- var `CACHE_FILE = Path.home() / ".cache" / PROGRAM / "check_version_idle-time.json"` (L27)
- var `GREEN = "\033[92m"` (L28)
- var `RED = "\033[91m"` (L29)
- var `RESET = "\033[0m"` (L30)
### fn `def _human_timestamp(timestamp: float) -> str` `priv` (L55-59)
- @brief Stores the full CLI help screen rendered by main.
- @details Documents management commands and every data command with its manifest
semantics; rendered verbatim for no-argument and --help invocations.
- @satisfies REQ-009, REQ-050

### fn `def _cache_path() -> Path` `priv` (L60-64)

### fn `def _write_cache(delay: int, now: float | None = None) -> None` `priv` (L65-79)

### fn `def _cache_is_active(now: float | None = None) -> bool` `priv` (L80-90)

### fn `def _version_key(version: str) -> tuple[int, ...] | None` `priv` (L91-99)

### fn `def _is_newer_version(candidate: str, installed: str) -> bool` `priv` (L100-109)

### fn `def _print_coloured(colour: str, message: str) -> None` `priv` (L110-113)

### fn `def _fetch_latest_version(opener: Callable[..., Any] | None = None) -> str` `priv` (L114-128)

### fn `def check_for_update(*, force: bool = False, opener: Callable[..., Any] | None = None) -> bool` (L129-163)

### fn `def _run_tool_command(action: str) -> int` `priv` (L164-183)

### fn `def _load_tracks(json_file: Path) -> list[dict[str, Any]]` `priv` (L184-203)

### fn `def _write_id3_tags(audio_file: Path, tags: dict[str, Any]) -> None` `priv` (L204-232)

### fn `def sync_from_json(json_filename: str, *, dry_run: bool = False) -> int` (L233-269)

### fn `def _sync_parser() -> argparse.ArgumentParser` `priv` (L270-276)

- var `TAG_COMMAND_DESCRIPTIONS = {` (L282)
### fn `def _tag_command_parser(command: str) -> argparse.ArgumentParser` `priv` (L289-304)
- @brief Creates the shared parser for an EyeD3 manifest command.
- @details Defines positional MP3-root and JSON-manifest arguments plus the command description consumed by command-specific help. Complexity: O(1). Side effects: none.
- @param command {str} CLI command name.
- @return {argparse.ArgumentParser} Configured parser instance.
- @satisfies REQ-032, REQ-040

### fn `def main(argv: Sequence[str] | None = None) -> int` (L305-349)
- @brief Dispatches command-line arguments to management and tag operations.
- @details Performs the existing release check before routing recognized command sequences; delegates EyeD3 manifest commands without altering sync behavior. Complexity: O(1) excluding delegated operations. Side effects: stdout, network, filesystem, and optional subprocess interactions.
- @param argv {Sequence[str] | None} Explicit CLI tokens or null for sys.argv.
- @return {int} Delegated command status or CLI validation status.
- @satisfies PRJ-003, PRJ-006, PRJ-007, REQ-001, REQ-032, REQ-040

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|20||
|`OWNER`|var|pub|21||
|`REPOSITORY`|var|pub|22||
|`LATEST_RELEASE_URL`|var|pub|23||
|`HTTP_TIMEOUT_SECONDS`|var|pub|24||
|`IDLE_DELAY_SECONDS`|var|pub|25||
|`ERROR_IDLE_DELAY_SECONDS`|var|pub|26||
|`CACHE_FILE`|var|pub|27||
|`GREEN`|var|pub|28||
|`RED`|var|pub|29||
|`RESET`|var|pub|30||
|`_human_timestamp`|fn|priv|55-59|def _human_timestamp(timestamp: float) -> str|
|`_cache_path`|fn|priv|60-64|def _cache_path() -> Path|
|`_write_cache`|fn|priv|65-79|def _write_cache(delay: int, now: float | None = None) ->...|
|`_cache_is_active`|fn|priv|80-90|def _cache_is_active(now: float | None = None) -> bool|
|`_version_key`|fn|priv|91-99|def _version_key(version: str) -> tuple[int, ...] | None|
|`_is_newer_version`|fn|priv|100-109|def _is_newer_version(candidate: str, installed: str) -> ...|
|`_print_coloured`|fn|priv|110-113|def _print_coloured(colour: str, message: str) -> None|
|`_fetch_latest_version`|fn|priv|114-128|def _fetch_latest_version(opener: Callable[..., Any] | No...|
|`check_for_update`|fn|pub|129-163|def check_for_update(*, force: bool = False, opener: Call...|
|`_run_tool_command`|fn|priv|164-183|def _run_tool_command(action: str) -> int|
|`_load_tracks`|fn|priv|184-203|def _load_tracks(json_file: Path) -> list[dict[str, Any]]|
|`_write_id3_tags`|fn|priv|204-232|def _write_id3_tags(audio_file: Path, tags: dict[str, Any...|
|`sync_from_json`|fn|pub|233-269|def sync_from_json(json_filename: str, *, dry_run: bool =...|
|`_sync_parser`|fn|priv|270-276|def _sync_parser() -> argparse.ArgumentParser|
|`TAG_COMMAND_DESCRIPTIONS`|var|pub|282||
|`_tag_command_parser`|fn|priv|289-304|def _tag_command_parser(command: str) -> argparse.Argumen...|
|`main`|fn|pub|305-349|def main(argv: Sequence[str] | None = None) -> int|


---

# tag_manifest.py | Python | 370L | 13 symbols | 7 imports | 31 comments
> Path: `src/json2mp3/tag_manifest.py`

## Imports
```
from __future__ import annotations
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any
import eyed3
```

## Definitions

- var `EYED3_LOG_LEVEL = logging.ERROR` (L26)
- var `SUPPORTED_TAG_FIELDS = (` (L42)
### fn `def _normalise_value(value: Any) -> Any` `priv` (L62-78)
- @brief Defines the injectable EyeD3-compatible MP3 loader signature. */
- @brief Converts an EyeD3 value into a JSON-compatible scalar or list.
- @details Converts tuples and lists recursively, preserves JSON primitives, and converts EyeD3 domain values to their stable string form. Complexity: O(n) for sequence length n. Side effects: none.
- @param value {Any} EyeD3 field value.
- @return {Any} JSON-compatible normalized representation.
- @satisfies DES-011, REQ-049

### fn `def _tag_values(tag: Any | None) -> dict[str, Any]` `priv` (L79-97)
- @brief Extracts supported non-null fields from one EyeD3 tag object.
- @details Reads each SUPPORTED_TAG_FIELDS attribute once and excludes null values, producing the canonical manifest tag object. Complexity: O(T).
- @param tag {Any | None} EyeD3 tag object or null for an untagged file.
- @return {dict[str, Any]} Supported field-name to normalized-value mapping.
- @satisfies DES-011, REQ-025, REQ-049

### fn `def _load_audio(path: str) -> Any` `priv` (L98-109)
- @brief Loads one MP3 through the EyeD3 module.
- @details Delegates MP3 parsing to eyed3.load; null is returned by EyeD3 for unreadable or unsupported audio data. Complexity: external-library bound.
- @param path {str} Existing target MP3 path.
- @return {Any} EyeD3 audio object or null.
- @satisfies CTN-004

### fn `def _normalise_relative_path(root: Path, audio_file: Path) -> str` `priv` (L110-122)
- @brief Produces a POSIX-relative manifest key for one scanned file.
- @details Computes the path relative to root and converts platform separators to POSIX separators. Complexity: O(path-length). Side effects: none.
- @param root {Path} Resolved MP3 scan root.
- @param audio_file {Path} File located under root.
- @return {str} Normalized relative manifest path.
- @satisfies REQ-048

### fn `def _scan_mp3_files(root: Path) -> list[tuple[str, Path]]` `priv` (L123-142)
- @brief Recursively discovers MP3 files below a directory.
- @details Selects regular files whose suffix equals .mp3 case-insensitively and sorts output by normalized relative path. Complexity: O(F log F).
- @param root {Path} Candidate MP3 root directory.
- @return {list[tuple[str, Path]]} Sorted manifest-key and absolute-path pairs. @raises ValueError If root is not a directory.
- @satisfies REQ-032, REQ-048

### fn `def _read_manifest(` `priv` (L143-146)

### fn `def _write_manifest(json_file: Path, manifest: dict[str, dict[str, Any]]) -> None` `priv` (L182-202)
- @brief Loads a JSON array manifest into a relative-path index.
- @brief Serializes a normalized tag index as a deterministic JSON array.
- @details Returns an empty index for a missing destination, validates entry
shape for existing files, and normalizes separators in entry paths.
Complexity: O(E), where E is entry count. Side effects: file read.
- @details Creates parent directories, orders entries by path, and writes UTF-8 JSON with indentation. Complexity: O(E log E). Side effects: filesystem write.
- @param json_file {Path} Source or destination manifest path.
- @param missing_is_empty {bool} True only when a missing extraction destination is valid.
- @param json_file {Path} Destination manifest path.
- @param manifest {dict[str, dict[str, Any]]} Relative path to tag-object index.
- @return {dict[str, dict[str, Any]]} Relative path to tag-object index.
@raises ValueError If JSON is invalid or the manifest structure is invalid.
- @return {None} No value.
- @satisfies REQ-033, REQ-040, REQ-048
- @satisfies DES-012, REQ-033

### fn `def _changed_fields(old_tags: dict[str, Any], new_tags: dict[str, Any]) -> list[str]` `priv` (L203-219)
- @brief Lists supported fields with unequal old and new values.
- @details Compares the union of supported keys in lexical order and omits unchanged or unsupported fields. Complexity: O(T log T). Side effects: none.
- @param old_tags {dict[str, Any]} Previous field-value mapping.
- @param new_tags {dict[str, Any]} Current field-value mapping.
- @return {list[str]} Lexically ordered differing supported field names.
- @satisfies REQ-037, REQ-046

### fn `def tags_extract(` (L220-224)

### fn `def _set_tag_field(tag: Any, field: str, value: Any) -> None` `priv` (L267-284)
- @brief Extracts recursive MP3 ID3 data and reconciles one JSON manifest.
- @brief Assigns or clears one supported EyeD3 tag attribute.
- @details Loads existing entries, replaces scanned entries by normalized path,
removes stale entries, writes the complete sorted array, and emits only
changed existing-field details plus file-count summary. Complexity: O(F log F).
- @details Converts JSON track/disc arrays into EyeD3 number tuples; other supported values are assigned unchanged, including null removals. Complexity: O(1). Side effects: mutates tag.
- @param mp3_root {str | Path} Recursive MP3 directory root.
- @param json_filename {str | Path} JSON destination manifest path.
- @param loader {AudioLoader} Injectable EyeD3-compatible MP3 loader.
- @param tag {Any} Mutable EyeD3 tag object.
- @param field {str} Supported tag attribute name.
- @param value {Any} Manifest value or null for removal.
- @return {int} Zero on successful reconciliation; two on input/manifest error.
- @return {None} No value.
- @satisfies REQ-032, REQ-039, REQ-048, REQ-049
- @satisfies REQ-042, REQ-043, REQ-044

### fn `def update_tags(` (L285-289)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`EYED3_LOG_LEVEL`|var|pub|26||
|`SUPPORTED_TAG_FIELDS`|var|pub|42||
|`_normalise_value`|fn|priv|62-78|def _normalise_value(value: Any) -> Any|
|`_tag_values`|fn|priv|79-97|def _tag_values(tag: Any | None) -> dict[str, Any]|
|`_load_audio`|fn|priv|98-109|def _load_audio(path: str) -> Any|
|`_normalise_relative_path`|fn|priv|110-122|def _normalise_relative_path(root: Path, audio_file: Path...|
|`_scan_mp3_files`|fn|priv|123-142|def _scan_mp3_files(root: Path) -> list[tuple[str, Path]]|
|`_read_manifest`|fn|priv|143-146|def _read_manifest(|
|`_write_manifest`|fn|priv|182-202|def _write_manifest(json_file: Path, manifest: dict[str, ...|
|`_changed_fields`|fn|priv|203-219|def _changed_fields(old_tags: dict[str, Any], new_tags: d...|
|`tags_extract`|fn|pub|220-224|def tags_extract(|
|`_set_tag_field`|fn|priv|267-284|def _set_tag_field(tag: Any, field: str, value: Any) -> None|
|`update_tags`|fn|pub|285-289|def update_tags(|


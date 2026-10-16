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
        └── core.py
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

# core.py | Python | 290L | 26 symbols | 14 imports | 15 comments
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
from mutagen.id3 import COMM, TALB, TCON, TDRC, TIT2, TPE1, TPE2, TPOS, TRCK, ID3, ID3NoHeaderError
```

## Definitions

- var `PROGRAM = "json2mp3"` (L19)
- var `OWNER = "Ogekuri"` (L20)
- var `REPOSITORY = "JSON2MP3"` (L21)
- var `LATEST_RELEASE_URL = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/releases/latest"` (L22)
- var `HTTP_TIMEOUT_SECONDS = 2` (L23)
- var `IDLE_DELAY_SECONDS = 3600` (L24)
- var `ERROR_IDLE_DELAY_SECONDS = 86400` (L25)
- var `CACHE_FILE = Path.home() / ".cache" / PROGRAM / "check_version_idle-time.json"` (L26)
- var `GREEN = "\033[92m"` (L27)
- var `RED = "\033[91m"` (L28)
- var `RESET = "\033[0m"` (L29)
### fn `def _human_timestamp(timestamp: float) -> str` `priv` (L46-50)

### fn `def _cache_path() -> Path` `priv` (L51-55)

### fn `def _write_cache(delay: int, now: float | None = None) -> None` `priv` (L56-70)

### fn `def _cache_is_active(now: float | None = None) -> bool` `priv` (L71-81)

### fn `def _version_key(version: str) -> tuple[int, ...] | None` `priv` (L82-90)

### fn `def _is_newer_version(candidate: str, installed: str) -> bool` `priv` (L91-100)

### fn `def _print_coloured(colour: str, message: str) -> None` `priv` (L101-104)

### fn `def _fetch_latest_version(opener: Callable[..., Any] | None = None) -> str` `priv` (L105-119)

### fn `def check_for_update(*, force: bool = False, opener: Callable[..., Any] | None = None) -> bool` (L120-154)

### fn `def _run_tool_command(action: str) -> int` `priv` (L155-174)

### fn `def _load_tracks(json_file: Path) -> list[dict[str, Any]]` `priv` (L175-194)

### fn `def _write_id3_tags(audio_file: Path, tags: dict[str, Any]) -> None` `priv` (L195-221)

### fn `def sync_from_json(json_filename: str, *, dry_run: bool = False) -> int` (L222-258)

### fn `def _sync_parser() -> argparse.ArgumentParser` `priv` (L259-265)

### fn `def main(argv: Sequence[str] | None = None) -> int` (L266-291)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`PROGRAM`|var|pub|19||
|`OWNER`|var|pub|20||
|`REPOSITORY`|var|pub|21||
|`LATEST_RELEASE_URL`|var|pub|22||
|`HTTP_TIMEOUT_SECONDS`|var|pub|23||
|`IDLE_DELAY_SECONDS`|var|pub|24||
|`ERROR_IDLE_DELAY_SECONDS`|var|pub|25||
|`CACHE_FILE`|var|pub|26||
|`GREEN`|var|pub|27||
|`RED`|var|pub|28||
|`RESET`|var|pub|29||
|`_human_timestamp`|fn|priv|46-50|def _human_timestamp(timestamp: float) -> str|
|`_cache_path`|fn|priv|51-55|def _cache_path() -> Path|
|`_write_cache`|fn|priv|56-70|def _write_cache(delay: int, now: float | None = None) ->...|
|`_cache_is_active`|fn|priv|71-81|def _cache_is_active(now: float | None = None) -> bool|
|`_version_key`|fn|priv|82-90|def _version_key(version: str) -> tuple[int, ...] | None|
|`_is_newer_version`|fn|priv|91-100|def _is_newer_version(candidate: str, installed: str) -> ...|
|`_print_coloured`|fn|priv|101-104|def _print_coloured(colour: str, message: str) -> None|
|`_fetch_latest_version`|fn|priv|105-119|def _fetch_latest_version(opener: Callable[..., Any] | No...|
|`check_for_update`|fn|pub|120-154|def check_for_update(*, force: bool = False, opener: Call...|
|`_run_tool_command`|fn|priv|155-174|def _run_tool_command(action: str) -> int|
|`_load_tracks`|fn|priv|175-194|def _load_tracks(json_file: Path) -> list[dict[str, Any]]|
|`_write_id3_tags`|fn|priv|195-221|def _write_id3_tags(audio_file: Path, tags: dict[str, Any...|
|`sync_from_json`|fn|pub|222-258|def sync_from_json(json_filename: str, *, dry_run: bool =...|
|`_sync_parser`|fn|priv|259-265|def _sync_parser() -> argparse.ArgumentParser|
|`main`|fn|pub|266-291|def main(argv: Sequence[str] | None = None) -> int|


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

# tag_manifest.py | Python | 926L | 31 symbols | 10 imports | 61 comments
> Path: `src/json2mp3/tag_manifest.py`

## Imports
```
from __future__ import annotations
import json
import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any
import eyed3
from eyed3.id3 import (
from eyed3.id3.frames import (
```

## Definitions

- var `EYED3_LOG_LEVEL = logging.ERROR` (L47)
- var `SUPPORTED_TAG_FIELDS = (` (L63)
- var `ATTRIBUTE_FRAME_IDS = {` (L84)
### fn `def _normalise_value(value: Any) -> Any` `priv` (L116-135)
- @brief Defines the injectable EyeD3-compatible MP3 loader signature. */
- @brief Converts an EyeD3 value into a JSON-compatible scalar, list, or object.
- @details Converts tuples and lists recursively, preserves JSON primitives, recursively normalizes mapping values, and converts EyeD3 domain values to their stable string form. Complexity: O(n) for sequence length n. Side effects: none.
- @param value {Any} EyeD3 field or frame value.
- @return {Any} JSON-compatible normalized representation.
- @satisfies DES-011, REQ-049, REQ-055

### fn `def _normalise_frame_id(fid: bytes) -> bytes` `priv` (L136-150)
- @brief Normalizes an ID3 frame identifier to its four-character form.
- @details Maps three-character ID3v2.2 identifiers through the EyeD3 mapping table and returns four-character identifiers unchanged. Complexity: O(1). Side effects: none.
- @param fid {bytes} Raw frame identifier from an EyeD3 frame set key or frame.
- @return {bytes} Canonical four-character frame identifier.
- @satisfies REQ-054

### fn `def _decode_id3_string(data: bytes, encoding: bytes) -> str` `priv` (L151-170)
- @brief Decodes one ID3 text field payload using its encoding byte.
- @details Supports latin-1, UTF-16 with BOM, UTF-16BE, and UTF-8 codecs used by ID3v2 text frames. Complexity: O(n). Side effects: none.
- @param data {bytes} Encoded text field bytes without terminator.
- @param encoding {bytes} ID3 encoding byte constant.
- @return {str} Decoded text. @raises UnicodeDecodeError If bytes are invalid for the codec.
- @satisfies REQ-055

### fn `def _id3_encoding_for(*values: str) -> tuple[bytes, bytes]` `priv` (L171-190)
- @brief Selects the deterministic ID3 encoding for a set of strings.
- @details Chooses latin-1 when every value is latin-1 encodable and UTF-8 otherwise. Both codecs use a one-byte terminator, preventing UTF-16 terminator overlap with low-order text bytes during SYLT parsing. Encoding selection is content-deterministic and independent of stored bytes. Complexity: O(total-characters). Side effects: none.
- @param values {str} Strings that share one frame encoding.
- @return {tuple[bytes, bytes]} Encoding byte and string terminator bytes.
- @satisfies REQ-055

### fn `def _encode_id3_string(encoding: bytes, value: str) -> bytes` `priv` (L191-209)
- @brief Encodes one string with a previously selected ID3 encoding.
- @details Inverse of _decode_id3_string for the same encoding byte. Complexity: O(n). Side effects: none.
- @param encoding {bytes} ID3 encoding byte constant.
- @param value {str} Text to encode.
- @return {bytes} Encoded bytes without terminator.
- @satisfies REQ-055

### fn `def _split_terminated(data: bytes, delimiter: bytes) -> tuple[bytes, bytes]` `priv` (L210-225)
- @brief Splits one ID3 payload at its first string terminator.
- @details Complexity: O(n). Side effects: none.
- @param data {bytes} Payload starting with a terminated string.
- @param delimiter {bytes} One- or two-byte string terminator.
- @return {tuple[bytes, bytes]} Terminated string bytes and remaining payload. @raises ValueError If the terminator is absent.
- @satisfies REQ-055

### fn `def _parse_sylt_payload(payload: bytes) -> dict[str, Any]` `priv` (L226-264)
- @brief Parses one raw SYLT frame payload into a structured mapping.
- @details Decodes the encoding byte, three-byte language, timestamp format, content type, terminated descriptor, and repeated terminated-text plus four-byte big-endian timestamp entries. Complexity: O(payload-length). Side effects: none.
- @param payload {bytes} Raw SYLT frame payload bytes from an EyeD3 raw frame.
- @return {dict[str, Any]} Keys lang, description, format, type, and lyrics list of `[timestamp, text]` pairs. @raises ValueError If the payload is truncated or malformed.
- @satisfies REQ-052, REQ-055

### fn `def _render_sylt_payload(` `priv` (L265-266)

### fn `def _frame_key(frame: Any) -> str | None` `priv` (L306-342)
- @brief Serializes one SYLT manifest value into raw frame payload bytes.
- @brief Computes the canonical manifest key for one EyeD3 frame.
- @details Selects a deterministic encoding covering the descriptor and every
lyric text, then emits encoding, language, timestamp format, content type,
terminated descriptor, and terminated-text plus four-byte big-endian
timestamp entries. Complexity: O(total-characters). Side effects: none.
- @details Builds description- and language-bearing keys for TXXX, WXXX, COMM, USLT, SYLT, and USER frames, the email-bearing key for POPM frames, plain frame-identifier keys for other text and URL frames, and returns null for binary frames requiring preservation. Complexity: O(payload-length) for raw SYLT frames, otherwise O(1). Side effects: none.
- @param lang {bytes} Three-byte ISO-639-2 language code from the manifest key.
- @param description {str} Frame descriptor from the manifest key.
- @param value {Any} Manifest object with integer format, integer type, and
lyrics list of `[timestamp, text]` pairs.
- @param frame {Any} EyeD3 frame object from a tag frame set.
- @return {bytes} Raw SYLT frame payload.
@raises ValueError If the manifest value shape is invalid.
- @return {str | None} Canonical manifest key or null for binary frames.
- @satisfies REQ-055
- @satisfies REQ-052, REQ-053, REQ-054, REQ-056, REQ-057

### fn `def _frame_value(frame: Any) -> Any` `priv` (L343-373)
- @brief Computes the JSON value for one EyeD3 frame.
- @details Returns text for description-bearing text frames, URL for URL frames, text or text list for generic text frames, the structured SYLT object for raw synchronized-lyrics frames, and the rating/counter object for POPM frames. Complexity: O(payload-length) for raw SYLT frames, otherwise O(1). Side effects: none.
- @param frame {Any} EyeD3 frame object from a tag frame set.
- @return {Any} JSON-compatible frame value. @raises ValueError If a raw SYLT payload is malformed.
- @satisfies REQ-052, REQ-054, REQ-055, REQ-057

### fn `def _parse_frame_key(field: str) -> dict[str, Any] | None` `priv` (L374-421)
- @brief Parses one manifest tag key into a frame construction specification.
- @details Validates `<FRAME>` plain identifiers, `TXXX:` and `WXXX:` description keys, `POPM:` email keys, `COMM:`, `USLT:`, and `SYLT:` language-description keys, and `USER:` language keys; rejects identifiers covered by attribute fields. Complexity: O(key-length). Side effects: none.
- @param field {str} Manifest tag key.
- @return {dict[str, Any] | None} Specification with fid bytes and optional description or lang, or null when the key is not a settable frame key.
- @satisfies REQ-053, REQ-054, REQ-057, REQ-058

### fn `def _is_settable_key(field: str) -> bool` `priv` (L422-432)
- @brief Reports whether one manifest tag key maps to an ID3 attribute or frame.
- @details Complexity: O(key-length). Side effects: none.
- @param field {str} Manifest tag key.
- @return {bool} True for supported attribute fields and valid frame keys.
- @satisfies REQ-042, REQ-043, REQ-044

### fn `def _matching_frames(tag: Any, field: str) -> list[Any]` `priv` (L433-447)
- @brief Lists tag frames whose canonical manifest key equals one key.
- @details Complexity: O(F) frames plus raw SYLT payload parsing. Side effects: none.
- @param tag {Any} Mutable EyeD3 tag object.
- @param field {str} Canonical manifest frame key.
- @return {list[Any]} Matching EyeD3 frame objects.
- @satisfies REQ-044

### fn `def _text_value(value: Any) -> str` `priv` (L448-460)
- @brief Coerces one manifest scalar into a frame text string.
- @details Complexity: O(value-length). Side effects: none.
- @param value {Any} Manifest scalar value.
- @return {str} Frame text. @raises ValueError If the value is not a string scalar.

### fn `def _popularity_values(value: Any) -> tuple[int, int]` `priv` (L461-489)
- @brief Normalizes one POPM manifest value into rating and counter integers.
- @details Accepts a bare integer rating with implicit zero counter and an object with integer rating plus optional integer counter defaulting to zero; rejects boolean values that Python would otherwise accept as integers. Rating range and counter sign remain enforced by the EyeD3 PopularityFrame setters. Complexity: O(1). Side effects: none.
- @param value {Any} Manifest value bound to a `POPM:<email>` key.
- @return {tuple[int, int]} Rating value and play-counter value. @raises ValueError If the value is neither an integer rating nor an object with integer rating and optional integer counter.
- @satisfies REQ-058

### fn `def _build_frame(spec: dict[str, Any], value: Any) -> Any` `priv` (L490-535)
- @brief Constructs one EyeD3 frame from a key specification and value.
- @details Builds UserTextFrame, UserUrlFrame, CommentFrame, LyricsFrame, TermsOfUseFrame, PopularityFrame, raw SYLT, generic UrlFrame, or generic TextFrame instances according to the specification frame identifier. Complexity: O(value-size). Side effects: none.
- @param spec {dict[str, Any]} Output of _parse_frame_key for the target key.
- @param value {Any} Manifest value for the frame.
- @return {Any} Unattached EyeD3 frame object. @raises ValueError If the value shape is invalid for the frame type.
- @satisfies REQ-043, REQ-055, REQ-057, REQ-058

### fn `def _set_frame_field(tag: Any, spec: dict[str, Any], field: str, value: Any) -> None` `priv` (L536-561)
- @brief Replaces or removes the frames bound to one manifest frame key.
- @details Removes every existing frame with the canonical key, then attaches one newly constructed frame when the value is non-null. Complexity: O(F) frames plus value size. Side effects: mutates the tag frame set.
- @param tag {Any} Mutable EyeD3 tag object.
- @param spec {dict[str, Any]} Output of _parse_frame_key for the target key.
- @param field {str} Canonical manifest frame key.
- @param value {Any} Manifest value or null for removal.
- @return {None} No value. @raises ValueError If the value shape is invalid for the frame type.
- @satisfies REQ-042, REQ-043, REQ-044

### fn `def _attribute_value(tag: Any, field: str) -> Any` `priv` (L562-589)
- @brief Reads one supported EyeD3 tag attribute with raw-frame fallback.
- @details Returns getattr(tag, field) when EyeD3 parses the attribute and falls back to the raw value of the first ATTRIBUTE_FRAME_IDS covering frame when EyeD3 raises GenreException for a stored value such as a numeric genre string absent from the standard genre map. Complexity: O(1) normally, O(F) frames on fallback. Side effects: none.
- @param tag {Any} EyeD3 tag object.
- @param field {str} Supported attribute field name from SUPPORTED_TAG_FIELDS.
- @return {Any} Parsed attribute value, first covering-frame value, or null.
- @satisfies REQ-049, REQ-052

### fn `def _tag_values(tag: Any | None) -> dict[str, Any]` `priv` (L590-623)
- @brief Extracts all manifest tag values from one EyeD3 tag object.
- @details Reads each SUPPORTED_TAG_FIELDS attribute once through the _attribute_value GenreException raw-frame fallback, then scans the tag frame set and emits canonical keys for every additional text-bearing frame, including TXXX, WXXX, COMM, USLT, USER, raw SYLT, and POPM frames; binary frames are omitted. Complexity: O(T + F). Side effects: none.
- @param tag {Any | None} EyeD3 tag object or null for an untagged file.
- @return {dict[str, Any]} Tag-key to normalized-value mapping.
- @satisfies DES-011, REQ-025, REQ-049, REQ-052, REQ-053, REQ-054, REQ-056, REQ-057

### fn `def _load_audio(path: str) -> Any` `priv` (L624-635)
- @brief Loads one MP3 through the EyeD3 module.
- @details Delegates MP3 parsing to eyed3.load; null is returned by EyeD3 for unreadable or unsupported audio data. Complexity: external-library bound.
- @param path {str} Existing target MP3 path.
- @return {Any} EyeD3 audio object or null.
- @satisfies CTN-004

### fn `def _normalise_relative_path(root: Path, audio_file: Path) -> str` `priv` (L636-648)
- @brief Produces a POSIX-relative manifest key for one scanned file.
- @details Computes the path relative to root and converts platform separators to POSIX separators. Complexity: O(path-length). Side effects: none.
- @param root {Path} Resolved MP3 scan root.
- @param audio_file {Path} File located under root.
- @return {str} Normalized relative manifest path.
- @satisfies REQ-048

### fn `def _scan_mp3_files(root: Path) -> list[tuple[str, Path]]` `priv` (L649-668)
- @brief Recursively discovers MP3 files below a directory.
- @details Selects regular files whose suffix equals .mp3 case-insensitively and sorts output by normalized relative path. Complexity: O(F log F).
- @param root {Path} Candidate MP3 root directory.
- @return {list[tuple[str, Path]]} Sorted manifest-key and absolute-path pairs. @raises ValueError If root is not a directory.
- @satisfies REQ-032, REQ-048

### fn `def _read_manifest(` `priv` (L669-672)

### fn `def _write_manifest(json_file: Path, manifest: dict[str, dict[str, Any]]) -> None` `priv` (L708-728)
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

### fn `def _changed_fields(old_tags: dict[str, Any], new_tags: dict[str, Any]) -> list[str]` `priv` (L729-746)
- @brief Lists tag keys with unequal old and new values.
- @details Compares the union of keys in lexical order and omits unchanged keys, covering attribute keys and frame keys uniformly. Complexity: O(T log T). Side effects: none.
- @param old_tags {dict[str, Any]} Previous key-value mapping.
- @param new_tags {dict[str, Any]} Current key-value mapping.
- @return {list[str]} Lexically ordered differing tag keys.
- @satisfies REQ-037, REQ-046

### fn `def tags_extract(` (L747-751)

### fn `def _set_tag_field(tag: Any, field: str, value: Any) -> None` `priv` (L794-834)
- @brief Extracts recursive MP3 ID3 data and reconciles one JSON manifest.
- @brief Assigns or clears one manifest tag key on an EyeD3 tag object.
- @details Loads existing entries, replaces scanned entries by normalized path,
removes stale entries, writes the complete sorted array, and emits only
changed existing-tag details plus file-count summary. Complexity: O(F log F).
- @details Routes supported attribute fields through EyeD3 attribute setters, converting track and disc lists to tuples, and routes canonical frame keys through frame replacement or removal. Attribute writes rejected by EyeD3 with GenreException for non-standard numeric genre strings fall back to replacing the covering ATTRIBUTE_FRAME_IDS frame with the literal string value. Complexity: O(F) frames. Side effects: mutates tag.
- @param mp3_root {str | Path} Recursive MP3 directory root.
- @param json_filename {str | Path} JSON destination manifest path.
- @param loader {AudioLoader} Injectable EyeD3-compatible MP3 loader.
- @param tag {Any} Mutable EyeD3 tag object.
- @param field {str} Supported attribute name or canonical frame key.
- @param value {Any} Manifest value or null for removal.
- @return {int} Zero on successful reconciliation; two on input/manifest error.
- @return {None} No value. @raises ValueError If a frame value shape is invalid.
- @note The GenreException fallback writes str(value) as raw covering-frame text; null values never reach it because EyeD3 removes attributes without parsing.
- @satisfies REQ-032, REQ-039, REQ-048, REQ-049, REQ-052, REQ-056
- @satisfies REQ-042, REQ-043, REQ-044, REQ-053

### fn `def update_tags(` (L835-839)

## Symbol Index
|Symbol|Kind|Vis|Lines|Sig|
|---|---|---|---|---|
|`EYED3_LOG_LEVEL`|var|pub|47||
|`SUPPORTED_TAG_FIELDS`|var|pub|63||
|`ATTRIBUTE_FRAME_IDS`|var|pub|84||
|`_normalise_value`|fn|priv|116-135|def _normalise_value(value: Any) -> Any|
|`_normalise_frame_id`|fn|priv|136-150|def _normalise_frame_id(fid: bytes) -> bytes|
|`_decode_id3_string`|fn|priv|151-170|def _decode_id3_string(data: bytes, encoding: bytes) -> str|
|`_id3_encoding_for`|fn|priv|171-190|def _id3_encoding_for(*values: str) -> tuple[bytes, bytes]|
|`_encode_id3_string`|fn|priv|191-209|def _encode_id3_string(encoding: bytes, value: str) -> bytes|
|`_split_terminated`|fn|priv|210-225|def _split_terminated(data: bytes, delimiter: bytes) -> t...|
|`_parse_sylt_payload`|fn|priv|226-264|def _parse_sylt_payload(payload: bytes) -> dict[str, Any]|
|`_render_sylt_payload`|fn|priv|265-266|def _render_sylt_payload(|
|`_frame_key`|fn|priv|306-342|def _frame_key(frame: Any) -> str | None|
|`_frame_value`|fn|priv|343-373|def _frame_value(frame: Any) -> Any|
|`_parse_frame_key`|fn|priv|374-421|def _parse_frame_key(field: str) -> dict[str, Any] | None|
|`_is_settable_key`|fn|priv|422-432|def _is_settable_key(field: str) -> bool|
|`_matching_frames`|fn|priv|433-447|def _matching_frames(tag: Any, field: str) -> list[Any]|
|`_text_value`|fn|priv|448-460|def _text_value(value: Any) -> str|
|`_popularity_values`|fn|priv|461-489|def _popularity_values(value: Any) -> tuple[int, int]|
|`_build_frame`|fn|priv|490-535|def _build_frame(spec: dict[str, Any], value: Any) -> Any|
|`_set_frame_field`|fn|priv|536-561|def _set_frame_field(tag: Any, spec: dict[str, Any], fiel...|
|`_attribute_value`|fn|priv|562-589|def _attribute_value(tag: Any, field: str) -> Any|
|`_tag_values`|fn|priv|590-623|def _tag_values(tag: Any | None) -> dict[str, Any]|
|`_load_audio`|fn|priv|624-635|def _load_audio(path: str) -> Any|
|`_normalise_relative_path`|fn|priv|636-648|def _normalise_relative_path(root: Path, audio_file: Path...|
|`_scan_mp3_files`|fn|priv|649-668|def _scan_mp3_files(root: Path) -> list[tuple[str, Path]]|
|`_read_manifest`|fn|priv|669-672|def _read_manifest(|
|`_write_manifest`|fn|priv|708-728|def _write_manifest(json_file: Path, manifest: dict[str, ...|
|`_changed_fields`|fn|priv|729-746|def _changed_fields(old_tags: dict[str, Any], new_tags: d...|
|`tags_extract`|fn|pub|747-751|def tags_extract(|
|`_set_tag_field`|fn|priv|794-834|def _set_tag_field(tag: Any, field: str, value: Any) -> None|
|`update_tags`|fn|pub|835-839|def update_tags(|


"""
@brief Implements EyeD3-backed JSON tag manifest operations.
@details Provides deterministic recursive extraction and reconciliation operations
for supported scalar ID3 fields. Manifest paths are POSIX-relative to the caller
supplied root. Complexity: O(F log F + F*T), where F is file count and T is
supported field count.
@satisfies PRJ-006, PRJ-007, REQ-032, REQ-049
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import eyed3

#/** @brief Defines the minimum log level retained for the EyeD3 logger.
# * @details WARNING-level EyeD3 parse notices (unsupported frames and
# * non-standard genre names) otherwise leak to the terminal through the
# * logging last-resort handler and pollute the documented CLI output.
# * @satisfies REQ-037, REQ-038
# */
EYED3_LOG_LEVEL = logging.ERROR

#/** @brief Suppresses EyeD3 WARNING-level library noise once at module import.
# * @details Sets the effective level of the standard-library logger named
# * "eyed3" so child loggers such as "eyed3.id3" filter WARNING records before
# * propagation, while ERROR-or-higher records still reach configured root
# * handlers. Complexity: O(1). Side effects: mutates the process-wide
# * "eyed3" logger level exactly once per interpreter run.
# * @satisfies REQ-037, REQ-038
# */
logging.getLogger("eyed3").setLevel(EYED3_LOG_LEVEL)

#/** @brief Enumerates JSON-manifest fields mapped to EyeD3 scalar attributes.
# * @details Ordered tuple controls extraction and reconciliation scope.
# * @satisfies DES-011 REQ-049
# */
SUPPORTED_TAG_FIELDS = (
    "title",
    "artist",
    "album",
    "album_artist",
    "composer",
    "publisher",
    "copyright",
    "genre",
    "track_num",
    "disc_num",
    "recording_date",
    "release_date",
    "original_release_date",
)

#/** @brief Defines the injectable EyeD3-compatible MP3 loader signature. */
AudioLoader = Callable[[str], Any]


def _normalise_value(value: Any) -> Any:
    """
    @brief Converts an EyeD3 value into a JSON-compatible scalar or list.
    @details Converts tuples and lists recursively, preserves JSON primitives,
    and converts EyeD3 domain values to their stable string form. Complexity:
    O(n) for sequence length n. Side effects: none.
    @param value {Any} EyeD3 field value.
    @return {Any} JSON-compatible normalized representation.
    @satisfies DES-011, REQ-049
    """
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, tuple | list):
        return [_normalise_value(item) for item in value]
    return str(value)


def _tag_values(tag: Any | None) -> dict[str, Any]:
    """
    @brief Extracts supported non-null fields from one EyeD3 tag object.
    @details Reads each SUPPORTED_TAG_FIELDS attribute once and excludes null
    values, producing the canonical manifest tag object. Complexity: O(T).
    @param tag {Any | None} EyeD3 tag object or null for an untagged file.
    @return {dict[str, Any]} Supported field-name to normalized-value mapping.
    @satisfies DES-011, REQ-025, REQ-049
    """
    if tag is None:
        return {}
    values: dict[str, Any] = {}
    for field in SUPPORTED_TAG_FIELDS:
        value = _normalise_value(getattr(tag, field, None))
        if value is not None:
            values[field] = value
    return values


def _load_audio(path: str) -> Any:
    """
    @brief Loads one MP3 through the EyeD3 module.
    @details Delegates MP3 parsing to eyed3.load; null is returned by EyeD3 for
    unreadable or unsupported audio data. Complexity: external-library bound.
    @param path {str} Existing target MP3 path.
    @return {Any} EyeD3 audio object or null.
    @satisfies CTN-004
    """
    return eyed3.load(path)


def _normalise_relative_path(root: Path, audio_file: Path) -> str:
    """
    @brief Produces a POSIX-relative manifest key for one scanned file.
    @details Computes the path relative to root and converts platform separators
    to POSIX separators. Complexity: O(path-length). Side effects: none.
    @param root {Path} Resolved MP3 scan root.
    @param audio_file {Path} File located under root.
    @return {str} Normalized relative manifest path.
    @satisfies REQ-048
    """
    return audio_file.relative_to(root).as_posix()


def _scan_mp3_files(root: Path) -> list[tuple[str, Path]]:
    """
    @brief Recursively discovers MP3 files below a directory.
    @details Selects regular files whose suffix equals .mp3 case-insensitively
    and sorts output by normalized relative path. Complexity: O(F log F).
    @param root {Path} Candidate MP3 root directory.
    @return {list[tuple[str, Path]]} Sorted manifest-key and absolute-path pairs.
    @raises ValueError If root is not a directory.
    @satisfies REQ-032, REQ-048
    """
    if not root.is_dir():
        raise ValueError(f"MP3 root is not a directory: {root}")
    files = [
        (_normalise_relative_path(root, candidate), candidate)
        for candidate in root.rglob("*")
        if candidate.is_file() and candidate.suffix.lower() == ".mp3"
    ]
    return sorted(files, key=lambda item: item[0])


def _read_manifest(
    json_file: Path,
    *,
    missing_is_empty: bool = True,
) -> dict[str, dict[str, Any]]:
    """
    @brief Loads a JSON array manifest into a relative-path index.
    @details Returns an empty index for a missing destination, validates entry
    shape for existing files, and normalizes separators in entry paths.
    Complexity: O(E), where E is entry count. Side effects: file read.
    @param json_file {Path} Source or destination manifest path.
    @param missing_is_empty {bool} True only when a missing extraction destination is valid.
    @return {dict[str, dict[str, Any]]} Relative path to tag-object index.
    @raises ValueError If JSON is invalid or the manifest structure is invalid.
    @satisfies REQ-033, REQ-040, REQ-048
    """
    if not json_file.exists():
        if missing_is_empty:
            return {}
        raise ValueError(f"JSON manifest does not exist: {json_file}")
    try:
        payload = json.loads(json_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON manifest {json_file}: {error}") from error
    if not isinstance(payload, list):
        raise ValueError("tag manifest root must be an array")

    manifest: dict[str, dict[str, Any]] = {}
    for entry in payload:
        if not isinstance(entry, dict):
            raise ValueError("tag manifest entries must be objects")
        path = entry.get("path")
        tags = entry.get("tags")
        if not isinstance(path, str) or not isinstance(tags, dict):
            raise ValueError("tag manifest entries require string path and object tags")
        manifest[path.replace("\\", "/")] = tags
    return manifest


def _write_manifest(json_file: Path, manifest: dict[str, dict[str, Any]]) -> None:
    """
    @brief Serializes a normalized tag index as a deterministic JSON array.
    @details Creates parent directories, orders entries by path, and writes UTF-8
    JSON with indentation. Complexity: O(E log E). Side effects: filesystem write.
    @param json_file {Path} Destination manifest path.
    @param manifest {dict[str, dict[str, Any]]} Relative path to tag-object index.
    @return {None} No value.
    @satisfies DES-012, REQ-033
    """
    entries = [
        {"path": path, "tags": manifest[path]}
        for path in sorted(manifest)
    ]
    json_file.parent.mkdir(parents=True, exist_ok=True)
    json_file.write_text(
        json.dumps(entries, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _changed_fields(old_tags: dict[str, Any], new_tags: dict[str, Any]) -> list[str]:
    """
    @brief Lists supported fields with unequal old and new values.
    @details Compares the union of supported keys in lexical order and omits
    unchanged or unsupported fields. Complexity: O(T log T). Side effects: none.
    @param old_tags {dict[str, Any]} Previous field-value mapping.
    @param new_tags {dict[str, Any]} Current field-value mapping.
    @return {list[str]} Lexically ordered differing supported field names.
    @satisfies REQ-037, REQ-046
    """
    return [
        field
        for field in sorted(set(old_tags) | set(new_tags))
        if field in SUPPORTED_TAG_FIELDS and old_tags.get(field) != new_tags.get(field)
    ]


def tags_extract(
    mp3_root: str | Path,
    json_filename: str | Path,
    *,
    loader: AudioLoader = _load_audio,
) -> int:
    """
    @brief Extracts recursive MP3 ID3 data and reconciles one JSON manifest.
    @details Loads existing entries, replaces scanned entries by normalized path,
    removes stale entries, writes the complete sorted array, and emits only
    changed existing-field details plus file-count summary. Complexity: O(F log F).
    @param mp3_root {str | Path} Recursive MP3 directory root.
    @param json_filename {str | Path} JSON destination manifest path.
    @param loader {AudioLoader} Injectable EyeD3-compatible MP3 loader.
    @return {int} Zero on successful reconciliation; two on input/manifest error.
    @satisfies REQ-032, REQ-039, REQ-048, REQ-049
    """
    root = Path(mp3_root).expanduser().resolve()
    json_file = Path(json_filename).expanduser().resolve()
    try:
        existing = _read_manifest(json_file)
        scanned = _scan_mp3_files(root)
    except ValueError as error:
        print(f"Error: {error}")
        return 2

    current: dict[str, dict[str, Any]] = {}
    added = 0
    updated = 0
    for relative_path, audio_file in scanned:
        audio = loader(str(audio_file))
        tags = _tag_values(None if audio is None else audio.tag)
        current[relative_path] = tags
        if relative_path not in existing:
            added += 1
            continue
        changes = _changed_fields(existing[relative_path], tags)
        if changes:
            updated += 1
            print(f"Updated {relative_path}: {', '.join(changes)}")

    removed = len(set(existing) - set(current))
    _write_manifest(json_file, current)
    print(f"Summary: updated={updated} added={added} removed={removed}")
    return 0


def _set_tag_field(tag: Any, field: str, value: Any) -> None:
    """
    @brief Assigns or clears one supported EyeD3 tag attribute.
    @details Converts JSON track/disc arrays into EyeD3 number tuples; other
    supported values are assigned unchanged, including null removals. Complexity:
    O(1). Side effects: mutates tag.
    @param tag {Any} Mutable EyeD3 tag object.
    @param field {str} Supported tag attribute name.
    @param value {Any} Manifest value or null for removal.
    @return {None} No value.
    @satisfies REQ-042, REQ-043, REQ-044
    """
    if field in {"track_num", "disc_num"} and isinstance(value, list):
        setattr(tag, field, tuple(value))
    else:
        setattr(tag, field, value)


def update_tags(
    mp3_root: str | Path,
    json_filename: str | Path,
    *,
    loader: AudioLoader = _load_audio,
) -> int:
    """
    @brief Reconciles MP3 ID3 fields with a JSON manifest.
    @details Resolves every manifest path below root, reports missing files,
    applies changed, added, and removed supported fields once per changed file,
    and summarizes updated, unchanged, and error file counts. Complexity: O(E*T).
    @param mp3_root {str | Path} Base directory for manifest paths.
    @param json_filename {str | Path} JSON source manifest path.
    @param loader {AudioLoader} Injectable EyeD3-compatible MP3 loader.
    @return {int} Zero without errors; one for per-file errors; two for manifest errors.
    @satisfies REQ-040, REQ-049
    """
    root = Path(mp3_root).expanduser().resolve()
    json_file = Path(json_filename).expanduser().resolve()
    if not root.is_dir():
        print(f"Error: MP3 root is not a directory: {root}")
        return 2
    try:
        manifest = _read_manifest(json_file, missing_is_empty=False)
    except ValueError as error:
        print(f"Error: {error}")
        return 2

    errors = 0
    unchanged = 0
    updated = 0
    for relative_path in sorted(manifest):
        target = root / Path(relative_path)
        if not target.is_file():
            print(f"Error: MP3 file not found: {target}")
            errors += 1
            continue
        audio = loader(str(target))
        if audio is None:
            print(f"Error: unable to read MP3 file: {target}")
            errors += 1
            continue
        if audio.tag is None:
            audio.initTag()
        tag: Any = audio.tag
        if tag is None:
            print(f"Error: unable to initialize ID3 tag: {target}")
            errors += 1
            continue
        current = _tag_values(tag)
        desired = {
            field: value
            for field, value in manifest[relative_path].items()
            if field in SUPPORTED_TAG_FIELDS
        }
        changed = []
        added = []
        removed = []
        for field in sorted(set(current) | set(desired)):
            old_value = current.get(field)
            new_value = desired.get(field)
            if old_value == new_value:
                continue
            if field not in current:
                added.append(field)
            elif field not in desired:
                removed.append(field)
            else:
                changed.append(field)
            _set_tag_field(tag, field, new_value)
        if not changed and not added and not removed:
            unchanged += 1
            continue
        tag.save()
        updated += 1
        details = []
        if changed:
            details.append(f"changed={','.join(changed)}")
        if added:
            details.append(f"added={','.join(added)}")
        if removed:
            details.append(f"removed={','.join(removed)}")
        print(f"Updated {relative_path}: {'; '.join(details)}")

    print(f"Summary: updated={updated} unchanged={unchanged} errors={errors}")
    return 1 if errors else 0

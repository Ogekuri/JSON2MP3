"""
@brief Implements EyeD3-backed JSON tag manifest operations.
@details Provides deterministic recursive extraction and reconciliation of all
text-bearing ID3 frames, including user-defined text and lyrics frames, while
preserving binary frames. Manifest paths are POSIX-relative to the caller
supplied root. Complexity: O(F log F + F*(T+F)), where F is file count and T is
supported field count.
@satisfies PRJ-006, PRJ-007, REQ-032, REQ-049, REQ-052, REQ-056
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import eyed3
from eyed3.id3 import (
    LATIN1_ENCODING,
    UTF_16BE_ENCODING,
    UTF_16_ENCODING,
    UTF_8_ENCODING,
)
from eyed3.id3.frames import (
    CommentFrame,
    Frame,
    LyricsFrame,
    TermsOfUseFrame,
    TextFrame,
    UrlFrame,
    UserTextFrame,
    UserUrlFrame,
    map2_2FrameId,
)

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

#/** @brief Maps supported attribute fields to their covering ID3 frame identifiers.
# * @details Frames listed here are serialized under their attribute key and are
# * excluded from frame-identifier key emission during extraction.
# * @satisfies REQ-052, REQ-049
# */
ATTRIBUTE_FRAME_IDS = {
    "title": b"TIT2",
    "artist": b"TPE1",
    "album": b"TALB",
    "album_artist": b"TPE2",
    "composer": b"TCOM",
    "publisher": b"TPUB",
    "copyright": b"TCOP",
    "genre": b"TCON",
    "track_num": b"TRCK",
    "disc_num": b"TPOS",
    "recording_date": b"TDRC",
    "release_date": b"TDRL",
    "original_release_date": b"TDOR",
}

#/** @brief Matches canonical three- or four-character ID3 frame identifiers.
# * @details Three-character identifiers are ID3v2.2 forms normalized before use.
# * @satisfies REQ-054
# */
_FRAME_ID_PATTERN = re.compile(r"[A-Z0-9]{3,4}")

#/** @brief Enumerates description- and language-bearing manifest key prefixes.
# * @details Keys use `<FRAME>:<language>:<description>` for these identifiers.
# * @satisfies REQ-053
# */
_LANG_KEY_FRAMES = frozenset({"COMM", "USLT", "SYLT"})

#/** @brief Defines the injectable EyeD3-compatible MP3 loader signature. */
AudioLoader = Callable[[str], Any]


def _normalise_value(value: Any) -> Any:
    """
    @brief Converts an EyeD3 value into a JSON-compatible scalar, list, or object.
    @details Converts tuples and lists recursively, preserves JSON primitives,
    recursively normalizes mapping values, and converts EyeD3 domain values to
    their stable string form. Complexity: O(n) for sequence length n. Side
    effects: none.
    @param value {Any} EyeD3 field or frame value.
    @return {Any} JSON-compatible normalized representation.
    @satisfies DES-011, REQ-049, REQ-055
    """
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {str(key): _normalise_value(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_normalise_value(item) for item in value]
    return str(value)


def _normalise_frame_id(fid: bytes) -> bytes:
    """
    @brief Normalizes an ID3 frame identifier to its four-character form.
    @details Maps three-character ID3v2.2 identifiers through the EyeD3 mapping
    table and returns four-character identifiers unchanged. Complexity: O(1).
    Side effects: none.
    @param fid {bytes} Raw frame identifier from an EyeD3 frame set key or frame.
    @return {bytes} Canonical four-character frame identifier.
    @satisfies REQ-054
    """
    if len(fid) == 3:
        return map2_2FrameId(fid)
    return fid


def _decode_id3_string(data: bytes, encoding: bytes) -> str:
    """
    @brief Decodes one ID3 text field payload using its encoding byte.
    @details Supports latin-1, UTF-16 with BOM, UTF-16BE, and UTF-8 codecs used
    by ID3v2 text frames. Complexity: O(n). Side effects: none.
    @param data {bytes} Encoded text field bytes without terminator.
    @param encoding {bytes} ID3 encoding byte constant.
    @return {str} Decoded text.
    @raises UnicodeDecodeError If bytes are invalid for the codec.
    @satisfies REQ-055
    """
    if encoding == UTF_16_ENCODING:
        return data.decode("utf-16")
    if encoding == UTF_16BE_ENCODING:
        return data.decode("utf-16-be")
    if encoding == UTF_8_ENCODING:
        return data.decode("utf-8")
    return data.decode("latin-1")


def _id3_encoding_for(*values: str) -> tuple[bytes, bytes]:
    """
    @brief Selects the deterministic ID3 encoding for a set of strings.
    @details Chooses latin-1 when every value is latin-1 encodable and UTF-16
    with BOM otherwise; both codecs are valid for ID3v2.3 and ID3v2.4. Encoding
    selection is content-deterministic and independent of stored bytes.
    Complexity: O(total-characters). Side effects: none.
    @param values {str} Strings that share one frame encoding.
    @return {tuple[bytes, bytes]} Encoding byte and string terminator bytes.
    @satisfies REQ-055
    """
    try:
        for value in values:
            value.encode("latin-1")
    except UnicodeEncodeError:
        return UTF_16_ENCODING, b"\x00\x00"
    return LATIN1_ENCODING, b"\x00"


def _encode_id3_string(encoding: bytes, value: str) -> bytes:
    """
    @brief Encodes one string with a previously selected ID3 encoding.
    @details Inverse of _decode_id3_string for the same encoding byte.
    Complexity: O(n). Side effects: none.
    @param encoding {bytes} ID3 encoding byte constant.
    @param value {str} Text to encode.
    @return {bytes} Encoded bytes without terminator.
    @satisfies REQ-055
    """
    if encoding == UTF_16_ENCODING:
        return value.encode("utf-16")
    if encoding == UTF_16BE_ENCODING:
        return value.encode("utf-16-be")
    if encoding == UTF_8_ENCODING:
        return value.encode("utf-8")
    return value.encode("latin-1")


def _split_terminated(data: bytes, delimiter: bytes) -> tuple[bytes, bytes]:
    """
    @brief Splits one ID3 payload at its first string terminator.
    @details Complexity: O(n). Side effects: none.
    @param data {bytes} Payload starting with a terminated string.
    @param delimiter {bytes} One- or two-byte string terminator.
    @return {tuple[bytes, bytes]} Terminated string bytes and remaining payload.
    @raises ValueError If the terminator is absent.
    @satisfies REQ-055
    """
    index = data.find(delimiter)
    if index < 0:
        raise ValueError("missing ID3 string terminator")
    return data[:index], data[index + len(delimiter):]


def _parse_sylt_payload(payload: bytes) -> dict[str, Any]:
    """
    @brief Parses one raw SYLT frame payload into a structured mapping.
    @details Decodes the encoding byte, three-byte language, timestamp format,
    content type, terminated descriptor, and repeated terminated-text plus
    four-byte big-endian timestamp entries. Complexity: O(payload-length).
    Side effects: none.
    @param payload {bytes} Raw SYLT frame payload bytes from an EyeD3 raw frame.
    @return {dict[str, Any]} Keys lang, description, format, type, and lyrics
    list of `[timestamp, text]` pairs.
    @raises ValueError If the payload is truncated or malformed.
    @satisfies REQ-052, REQ-055
    """
    if len(payload) < 6:
        raise ValueError("truncated SYLT payload")
    encoding = payload[0:1]
    lang = payload[1:4].decode("ascii", "replace")
    timestamp_format = payload[4]
    content_type = payload[5]
    delimiter = b"\x00\x00" if encoding in (UTF_16_ENCODING, UTF_16BE_ENCODING) else b"\x00"
    descriptor_bytes, rest = _split_terminated(payload[6:], delimiter)
    description = _decode_id3_string(descriptor_bytes, encoding)
    entries: list[list[Any]] = []
    while rest:
        text_bytes, rest = _split_terminated(rest, delimiter)
        if len(rest) < 4:
            raise ValueError("truncated SYLT timestamp")
        timestamp = int.from_bytes(rest[:4], "big")
        rest = rest[4:]
        entries.append([timestamp, _decode_id3_string(text_bytes, encoding)])
    return {
        "lang": lang,
        "description": description,
        "format": timestamp_format,
        "type": content_type,
        "lyrics": entries,
    }


def _render_sylt_payload(
    lang: bytes, description: str, value: Any
) -> bytes:
    """
    @brief Serializes one SYLT manifest value into raw frame payload bytes.
    @details Selects a deterministic encoding covering the descriptor and every
    lyric text, then emits encoding, language, timestamp format, content type,
    terminated descriptor, and terminated-text plus four-byte big-endian
    timestamp entries. Complexity: O(total-characters). Side effects: none.
    @param lang {bytes} Three-byte ISO-639-2 language code from the manifest key.
    @param description {str} Frame descriptor from the manifest key.
    @param value {Any} Manifest object with integer format, integer type, and
    lyrics list of `[timestamp, text]` pairs.
    @return {bytes} Raw SYLT frame payload.
    @raises ValueError If the manifest value shape is invalid.
    @satisfies REQ-055
    """
    if not isinstance(value, dict):
        raise ValueError("SYLT manifest value must be an object")
    try:
        timestamp_format = int(value["format"])
        content_type = int(value["type"])
        entries = value["lyrics"]
        texts = [str(entry[1]) for entry in entries]
        timestamps = [int(entry[0]) for entry in entries]
    except (KeyError, TypeError, ValueError, IndexError) as error:
        raise ValueError(f"invalid SYLT manifest value: {error}") from error
    encoding, delimiter = _id3_encoding_for(description, *texts)
    payload = (
        encoding
        + lang
        + bytes([timestamp_format, content_type])
        + _encode_id3_string(encoding, description)
        + delimiter
    )
    for text, timestamp in zip(texts, timestamps):
        payload += _encode_id3_string(encoding, text) + delimiter
        payload += timestamp.to_bytes(4, "big")
    return payload


def _frame_key(frame: Any) -> str | None:
    """
    @brief Computes the canonical manifest key for one EyeD3 frame.
    @details Builds description- and language-bearing keys for TXXX, WXXX, COMM,
    USLT, SYLT, and USER frames, plain frame-identifier keys for other text and
    URL frames, and returns null for binary frames requiring preservation.
    Complexity: O(payload-length) for raw SYLT frames, otherwise O(1). Side
    effects: none.
    @param frame {Any} EyeD3 frame object from a tag frame set.
    @return {str | None} Canonical manifest key or null for binary frames.
    @satisfies REQ-052, REQ-053, REQ-054, REQ-056
    """
    fid = _normalise_frame_id(frame.id).decode("ascii", "replace")
    if isinstance(frame, UserTextFrame):
        return f"TXXX:{frame.description}"
    if isinstance(frame, UserUrlFrame):
        return f"WXXX:{frame.description}"
    if isinstance(frame, CommentFrame):
        return f"COMM:{frame.lang.decode('ascii', 'replace')}:{frame.description}"
    if isinstance(frame, LyricsFrame):
        return f"USLT:{frame.lang.decode('ascii', 'replace')}:{frame.description}"
    if isinstance(frame, TermsOfUseFrame):
        return f"USER:{frame.lang.decode('ascii', 'replace')}"
    if isinstance(frame, TextFrame | UrlFrame):
        return fid
    if type(frame) is Frame and fid == "SYLT":
        try:
            parsed = _parse_sylt_payload(frame.data or b"")
        except (ValueError, UnicodeDecodeError):
            return None
        return f"SYLT:{parsed['lang']}:{parsed['description']}"
    return None


def _frame_value(frame: Any) -> Any:
    """
    @brief Computes the JSON value for one EyeD3 frame.
    @details Returns text for description-bearing text frames, URL for URL
    frames, text or text list for generic text frames, and the structured SYLT
    object for raw synchronized-lyrics frames. Complexity: O(payload-length)
    for raw SYLT frames, otherwise O(1). Side effects: none.
    @param frame {Any} EyeD3 frame object from a tag frame set.
    @return {Any} JSON-compatible frame value.
    @raises ValueError If a raw SYLT payload is malformed.
    @satisfies REQ-052, REQ-054, REQ-055
    """
    if isinstance(frame, UserTextFrame | CommentFrame | LyricsFrame | TermsOfUseFrame):
        return frame.text
    if isinstance(frame, UserUrlFrame):
        return frame.url
    if isinstance(frame, TextFrame):
        return frame.text
    if isinstance(frame, UrlFrame):
        return frame.url
    parsed = _parse_sylt_payload(frame.data or b"")
    return {
        "format": parsed["format"],
        "type": parsed["type"],
        "lyrics": parsed["lyrics"],
    }


def _parse_frame_key(field: str) -> dict[str, Any] | None:
    """
    @brief Parses one manifest tag key into a frame construction specification.
    @details Validates `<FRAME>` plain identifiers, `TXXX:` and `WXXX:`
    description keys, `COMM:`, `USLT:`, and `SYLT:` language-description keys,
    and `USER:` language keys; rejects identifiers covered by attribute fields.
    Complexity: O(key-length). Side effects: none.
    @param field {str} Manifest tag key.
    @return {dict[str, Any] | None} Specification with fid bytes and optional
    description or lang, or null when the key is not a settable frame key.
    @satisfies REQ-053, REQ-054
    """
    head, separator, rest = field.partition(":")
    if head in {"TXXX", "WXXX"}:
        if not separator:
            return None
        return {"fid": head.encode("ascii"), "description": rest}
    if head in _LANG_KEY_FRAMES:
        if not separator:
            return None
        lang, lang_separator, description = rest.partition(":")
        if not lang_separator or len(lang) != 3 or not lang.isalnum():
            return None
        return {
            "fid": head.encode("ascii"),
            "lang": lang.encode("ascii"),
            "description": description,
        }
    if head == "USER":
        if not separator or len(rest) != 3 or not rest.isalnum():
            return None
        return {"fid": b"USER", "lang": rest.encode("ascii")}
    if separator or not _FRAME_ID_PATTERN.fullmatch(head):
        return None
    try:
        fid = _normalise_frame_id(head.encode("ascii"))
    except UnicodeEncodeError:
        return None
    if fid in set(ATTRIBUTE_FRAME_IDS.values()):
        return None
    return {"fid": fid}


def _is_settable_key(field: str) -> bool:
    """
    @brief Reports whether one manifest tag key maps to an ID3 attribute or frame.
    @details Complexity: O(key-length). Side effects: none.
    @param field {str} Manifest tag key.
    @return {bool} True for supported attribute fields and valid frame keys.
    @satisfies REQ-042, REQ-043, REQ-044
    """
    return field in SUPPORTED_TAG_FIELDS or _parse_frame_key(field) is not None


def _matching_frames(tag: Any, field: str) -> list[Any]:
    """
    @brief Lists tag frames whose canonical manifest key equals one key.
    @details Complexity: O(F) frames plus raw SYLT payload parsing. Side effects:
    none.
    @param tag {Any} Mutable EyeD3 tag object.
    @param field {str} Canonical manifest frame key.
    @return {list[Any]} Matching EyeD3 frame objects.
    @satisfies REQ-044
    """
    return [
        frame for frame in tag.frame_set.getAllFrames() if _frame_key(frame) == field
    ]


def _text_value(value: Any) -> str:
    """
    @brief Coerces one manifest scalar into a frame text string.
    @details Complexity: O(value-length). Side effects: none.
    @param value {Any} Manifest scalar value.
    @return {str} Frame text.
    @raises ValueError If the value is not a string scalar.
    """
    if not isinstance(value, str):
        raise ValueError("frame text value must be a string")
    return value


def _build_frame(spec: dict[str, Any], value: Any) -> Any:
    """
    @brief Constructs one EyeD3 frame from a key specification and value.
    @details Builds UserTextFrame, UserUrlFrame, CommentFrame, LyricsFrame,
    TermsOfUseFrame, raw SYLT, generic UrlFrame, or generic TextFrame instances
    according to the specification frame identifier. Complexity: O(value-size).
    Side effects: none.
    @param spec {dict[str, Any]} Output of _parse_frame_key for the target key.
    @param value {Any} Manifest value for the frame.
    @return {Any} Unattached EyeD3 frame object.
    @raises ValueError If the value shape is invalid for the frame type.
    @satisfies REQ-043, REQ-055
    """
    fid = spec["fid"]
    description = spec.get("description") or ""
    lang = spec.get("lang") or b"eng"
    if fid == b"TXXX":
        return UserTextFrame(description=description, text=_text_value(value))
    if fid == b"WXXX":
        return UserUrlFrame(description=description, url=_text_value(value))
    if fid == b"COMM":
        return CommentFrame(
            description=description, lang=lang, text=_text_value(value)
        )
    if fid == b"USLT":
        return LyricsFrame(
            description=description, lang=lang, text=_text_value(value)
        )
    if fid == b"USER":
        return TermsOfUseFrame(text=_text_value(value), lang=lang)
    if fid == b"SYLT":
        frame = Frame(b"SYLT")
        frame.data = _render_sylt_payload(lang, description, value)
        return frame
    if fid.startswith(b"W"):
        return UrlFrame(fid, url=_text_value(value))
    text: Any = _text_value(value)
    return TextFrame(fid, text=text)


def _set_frame_field(tag: Any, spec: dict[str, Any], field: str, value: Any) -> None:
    """
    @brief Replaces or removes the frames bound to one manifest frame key.
    @details Removes every existing frame with the canonical key, then attaches
    one newly constructed frame when the value is non-null. Complexity: O(F)
    frames plus value size. Side effects: mutates the tag frame set.
    @param tag {Any} Mutable EyeD3 tag object.
    @param spec {dict[str, Any]} Output of _parse_frame_key for the target key.
    @param field {str} Canonical manifest frame key.
    @param value {Any} Manifest value or null for removal.
    @return {None} No value.
    @raises ValueError If the value shape is invalid for the frame type.
    @satisfies REQ-042, REQ-043, REQ-044
    """
    for frame in _matching_frames(tag, field):
        frames = tag.frame_set[frame.id]
        if frame in frames:
            frames.remove(frame)
        if not frames and frame.id in tag.frame_set:
            del tag.frame_set[frame.id]
    if value is None:
        return
    frame = _build_frame(spec, value)
    tag.frame_set[frame.id] = frame


def _tag_values(tag: Any | None) -> dict[str, Any]:
    """
    @brief Extracts all manifest tag values from one EyeD3 tag object.
    @details Reads each SUPPORTED_TAG_FIELDS attribute once, then scans the tag
    frame set and emits canonical keys for every additional text-bearing frame,
    including TXXX, WXXX, COMM, USLT, USER, and raw SYLT frames; binary frames
    are omitted. Complexity: O(T + F). Side effects: none.
    @param tag {Any | None} EyeD3 tag object or null for an untagged file.
    @return {dict[str, Any]} Tag-key to normalized-value mapping.
    @satisfies DES-011, REQ-025, REQ-049, REQ-052, REQ-053, REQ-054, REQ-056
    """
    if tag is None:
        return {}
    values: dict[str, Any] = {}
    for field in SUPPORTED_TAG_FIELDS:
        value = _normalise_value(getattr(tag, field, None))
        if value is not None:
            values[field] = value
    frame_set = getattr(tag, "frame_set", None)
    if frame_set is None:
        return values
    covered = set(ATTRIBUTE_FRAME_IDS.values())
    for fid, frames in frame_set.items():
        if _normalise_frame_id(fid) in covered:
            continue
        for frame in frames:
            key = _frame_key(frame)
            if key is not None:
                values[key] = _normalise_value(_frame_value(frame))
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
    @brief Lists tag keys with unequal old and new values.
    @details Compares the union of keys in lexical order and omits unchanged
    keys, covering attribute keys and frame keys uniformly. Complexity: O(T log T).
    Side effects: none.
    @param old_tags {dict[str, Any]} Previous key-value mapping.
    @param new_tags {dict[str, Any]} Current key-value mapping.
    @return {list[str]} Lexically ordered differing tag keys.
    @satisfies REQ-037, REQ-046
    """
    return [
        field
        for field in sorted(set(old_tags) | set(new_tags))
        if old_tags.get(field) != new_tags.get(field)
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
    changed existing-tag details plus file-count summary. Complexity: O(F log F).
    @param mp3_root {str | Path} Recursive MP3 directory root.
    @param json_filename {str | Path} JSON destination manifest path.
    @param loader {AudioLoader} Injectable EyeD3-compatible MP3 loader.
    @return {int} Zero on successful reconciliation; two on input/manifest error.
    @satisfies REQ-032, REQ-039, REQ-048, REQ-049, REQ-052, REQ-056
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
    @brief Assigns or clears one manifest tag key on an EyeD3 tag object.
    @details Routes supported attribute fields through EyeD3 attribute setters,
    converting track and disc lists to tuples, and routes canonical frame keys
    through frame replacement or removal. Complexity: O(F) frames. Side effects:
    mutates tag.
    @param tag {Any} Mutable EyeD3 tag object.
    @param field {str} Supported attribute name or canonical frame key.
    @param value {Any} Manifest value or null for removal.
    @return {None} No value.
    @raises ValueError If a frame value shape is invalid.
    @satisfies REQ-042, REQ-043, REQ-044, REQ-053
    """
    if field in SUPPORTED_TAG_FIELDS:
        if field in {"track_num", "disc_num"} and isinstance(value, list):
            setattr(tag, field, tuple(value))
        else:
            setattr(tag, field, value)
        return
    spec = _parse_frame_key(field)
    if spec is not None:
        _set_frame_field(tag, spec, field, value)


def update_tags(
    mp3_root: str | Path,
    json_filename: str | Path,
    *,
    loader: AudioLoader = _load_audio,
) -> int:
    """
    @brief Reconciles MP3 ID3 tags with a JSON manifest.
    @details Resolves every manifest path below root, reports missing files,
    applies changed, added, and removed attribute and frame keys once per changed
    file while preserving binary frames, and summarizes updated, unchanged, and
    error file counts. Complexity: O(E*(T+F)).
    @param mp3_root {str | Path} Base directory for manifest paths.
    @param json_filename {str | Path} JSON source manifest path.
    @param loader {AudioLoader} Injectable EyeD3-compatible MP3 loader.
    @return {int} Zero without errors; one for per-file errors; two for manifest errors.
    @satisfies REQ-040, REQ-042, REQ-043, REQ-044, REQ-049, REQ-056
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
        try:
            current = _tag_values(tag)
            desired = {
                field: value
                for field, value in manifest[relative_path].items()
                if _is_settable_key(field)
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
        except ValueError as error:
            print(f"Error: unable to apply tags to {target}: {error}")
            errors += 1
            continue
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

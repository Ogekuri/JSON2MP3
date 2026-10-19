"""
@brief Defines deterministic manifest command tests using isolated fake EyeD3 audio.
@details Covers manifest reconciliation, update mutations, and bidirectional
round trips without network access or real audio decoding. Filesystem state is
restricted to pytest temporary directories.
@satisfies TST-006, TST-007, TST-008, TST-009
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import eyed3
from eyed3.id3.frames import TextFrame

from json2mp3.tag_manifest import (
    _read_manifest,
    _write_manifest,
    tags_extract,
    update_tags,
)

#/** @brief Defines a genre name absent from the EyeD3 standard genre map.
# * @details Triggers the EyeD3 "Non standard genre name" WARNING log record
# * emitted by eyed3.id3.Genre when tag data is parsed during tags-extract.
# */
NON_STANDARD_GENRE = "Custom Fixture Genre"

#/** @brief Defines a numeric genre string absent from the EyeD3 genre map.
# * @details eyed3.id3.Genre.parse rejects this value with GenreException for
# * both the tag.genre getter and the tag.genre setter, reproducing the
# * tags-extract and update-tags crash fixed by the raw-frame fallback.
# */
NUMERIC_GENRE = "1985"


class FakeTag:
    """
    @brief Models mutable supported EyeD3 tag attributes for isolated tests.
    @details Stores every supported field as a public attribute and counts save
    calls, allowing tests to detect unintended writes. Complexity: O(1).
    @satisfies TST-006, TST-009
    """

    def __init__(self, **values: Any) -> None:
        """
        @brief Initializes supported fields with supplied fake values.
        @details Applies null defaults then overlays test-specific values.
        Complexity: O(T). Side effects: initializes instance attributes.
        @param values {Any} Supported field-name to fake value mapping.
        @return {None} No value.
        """
        self.title = None
        self.artist = None
        self.album = None
        self.album_artist = None
        self.composer = None
        self.publisher = None
        self.copyright = None
        self.genre = None
        self.track_num = None
        self.disc_num = None
        self.recording_date = None
        self.release_date = None
        self.original_release_date = None
        self.save_calls = 0
        for field, value in values.items():
            setattr(self, field, value)

    def save(self) -> None:
        """
        @brief Records a simulated EyeD3 save operation.
        @details Increments save_calls without altering fixture bytes.
        Complexity: O(1). Side effects: mutates save_calls.
        @return {None} No value.
        """
        self.save_calls += 1


class FakeAudio:
    """
    @brief Models an EyeD3 audio object with an optional tag.
    @details Exposes tag and initTag interfaces consumed by update_tags.
    Complexity: O(1). Side effects: initTag can allocate FakeTag.
    @satisfies TST-007, TST-009
    """

    def __init__(self, tag: FakeTag | None) -> None:
        """
        @brief Initializes the fake audio tag state.
        @details Preserves a null tag to exercise update_tags tag creation.
        Complexity: O(1). Side effects: initializes tag.
        @param tag {FakeTag | None} Initial fake tag or null.
        @return {None} No value.
        """
        self.tag = tag

    def initTag(self) -> None:
        """
        @brief Allocates an empty fake tag.
        @details Matches the EyeD3 method used for untagged target files.
        Complexity: O(1). Side effects: replaces tag with FakeTag.
        @return {None} No value.
        """
        self.tag = FakeTag()


def _write_mp3(root: Path, relative_path: str, content: bytes = b"fixture") -> Path:
    """
    @brief Creates a byte-stable MP3-named fixture file.
    @details Creates required parent directories and writes caller-supplied bytes;
    EyeD3 interaction is supplied by FakeAudio. Complexity: O(content-length).
    @param root {Path} Temporary fixture root.
    @param relative_path {str} Relative MP3 fixture path.
    @param content {bytes} Deterministic fixture bytes.
    @return {Path} Created fixture path.
    """
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _loader_for(audios: dict[Path, FakeAudio]):
    """
    @brief Creates an EyeD3-compatible fixture loader.
    @details Resolves the received string path before lookup, isolating tests from
    process working directory state. Complexity: O(1) per call.
    @param audios {dict[Path, FakeAudio]} Resolved path to fake audio mapping.
    @return {callable} Loader accepting one string path.
    """
    def load(path: str) -> FakeAudio | None:
        """
        @brief Returns the fake audio mapped to one path.
        @details Uses resolved paths and returns null for absent mappings.
        Complexity: O(1). Side effects: none.
        @param path {str} Loader input path.
        @return {FakeAudio | None} Mapped fake audio or null.
        """
        return audios.get(Path(path).resolve())

    return load


def _write_real_mp3(root: Path, relative_path: str) -> Path:
    """
    @brief Creates a minimal parseable MP3 fixture carrying real EyeD3 tags.
    @details Writes eight deterministic silent MPEG-1 Layer III frames, loads
    the file through EyeD3, initializes an ID3 tag, assigns a title plus
    NON_STANDARD_GENRE, and saves the tag so parsing re-emits the library
    warning path. Complexity: O(frame-byte-count). Side effects: temporary
    fixture file write.
    @param root {Path} Temporary fixture root.
    @param relative_path {str} Relative MP3 fixture path.
    @return {Path} Created MP3 fixture path.
    """
    mpeg_frame = bytes([0xFF, 0xFB, 0x90, 0x00]) + b"\x00" * 413
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(mpeg_frame * 8)
    audio = eyed3.load(str(path))
    assert audio is not None
    audio.initTag()
    assert audio.tag is not None
    audio.tag.title = "Title"
    audio.tag.genre = NON_STANDARD_GENRE
    audio.tag.save()
    return path


def _write_untagged_mp3(root: Path, relative_path: str) -> Path:
    """
    @brief Creates a parseable MP3 fixture without any ID3 tag.
    @details Writes eight deterministic silent MPEG-1 Layer III frames without
    initializing an ID3 tag so callers control the exact frame set.
    Complexity: O(frame-byte-count). Side effects: temporary fixture file write.
    @param root {Path} Temporary fixture root.
    @param relative_path {str} Relative MP3 fixture path.
    @return {Path} Created MP3 fixture path.
    """
    mpeg_frame = bytes([0xFF, 0xFB, 0x90, 0x00]) + b"\x00" * 413
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(mpeg_frame * 8)
    return path


def test_tags_extract_emits_no_eyed3_warning_log_records(
    tmp_path: Path, capsys: Any, caplog: Any
) -> None:
    """
    @brief Verifies tags-extract suppresses EyeD3 library WARNING log records.
    @details Extracts a real non-standard-genre MP3 through the default EyeD3
    loader and asserts zero eyed3 WARNING-or-higher records and zero library
    noise in the documented CLI output channels. Complexity: O(F*T). Side
    effects: temporary manifest write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest output capture fixture.
    @param caplog {Any} Pytest log capture fixture.
    @return {None} No value.
    @satisfies REQ-037, REQ-038
    """
    root = tmp_path / "music"
    _write_real_mp3(root, "song.mp3")
    manifest = tmp_path / "tags.json"
    caplog.clear()
    capsys.readouterr()

    expected_status = 0
    actual_status = tags_extract(root, manifest)

    assert actual_status == expected_status
    entries = json.loads(manifest.read_text(encoding="utf-8"))
    assert [entry["path"] for entry in entries] == ["song.mp3"]
    assert entries[0]["tags"]["title"] == "Title"
    assert entries[0]["tags"]["genre"] == NON_STANDARD_GENRE
    leaked = [
        record
        for record in caplog.records
        if record.name.startswith("eyed3") and record.levelno >= logging.WARNING
    ]
    assert leaked == []
    output = capsys.readouterr()
    assert "Summary: updated=0 added=1 removed=0" in output.out
    assert output.err == ""


def test_tags_extract_reconciles_added_updated_and_removed_entries(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies recursive extraction reconciles manifest entries and details.
    @details Runs with --delete: exercises changed existing tags, new nested
    files, and stale entries while asserting detail output excludes additions
    and removals.
    Complexity: O(F log F). Side effects: temporary manifest write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies TST-006
    """
    root = tmp_path / "music"
    song = _write_mp3(root, "song.mp3")
    new_song = _write_mp3(root, "nested/new.MP3")
    manifest = tmp_path / "tags.json"
    manifest.write_text(
        json.dumps(
            [
                {"path": "song.mp3", "tags": {"title": "Old", "artist": "Artist"}},
                {"path": "stale.mp3", "tags": {"title": "Stale"}},
            ]
        ),
        encoding="utf-8",
    )
    loader = _loader_for(
        {
            song.resolve(): FakeAudio(FakeTag(title="Current", artist="Artist")),
            new_song.resolve(): FakeAudio(FakeTag(title="New")),
        }
    )

    expected_status = 0
    actual_status = tags_extract(root, manifest, loader=loader, delete=True)

    assert actual_status == expected_status
    assert json.loads(manifest.read_text(encoding="utf-8")) == [
        {"path": "nested/new.MP3", "tags": {"title": "New"}},
        {"path": "song.mp3", "tags": {"artist": "Artist", "title": "Current"}},
    ]
    output = capsys.readouterr().out
    assert "Updated song.mp3: title" in output
    assert "new.MP3" not in output
    assert "stale.mp3" not in output
    assert "Summary: updated=1 added=1 removed=1" in output


def test_update_tags_changes_adds_removes_and_reports_missing_files(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies update-tags applies field reconciliation and error reporting.
    @details Runs with --delete: exercises changed, added, removed, unchanged,
    and missing-file paths against independent fake audio fixtures.
    Complexity: O(E*T).
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies TST-007
    """
    root = tmp_path / "music"
    song = _write_mp3(root, "song.mp3")
    stable = _write_mp3(root, "stable.mp3")
    song_tag = FakeTag(title="Old", artist="Artist", publisher="Remove")
    stable_tag = FakeTag(title="Stable")
    manifest = tmp_path / "tags.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "path": "song.mp3",
                    "tags": {"title": "New", "artist": "Artist", "album": "Added"},
                },
                {"path": "stable.mp3", "tags": {"title": "Stable"}},
                {"path": "missing.mp3", "tags": {"title": "Missing"}},
            ]
        ),
        encoding="utf-8",
    )
    loader = _loader_for(
        {
            song.resolve(): FakeAudio(song_tag),
            stable.resolve(): FakeAudio(stable_tag),
        }
    )

    expected_status = 1
    actual_status = update_tags(root, manifest, loader=loader, delete=True)

    assert actual_status == expected_status
    assert song_tag.title == "New"
    assert song_tag.album == "Added"
    assert song_tag.publisher is None
    assert song_tag.save_calls == 1
    assert stable_tag.save_calls == 0
    output = capsys.readouterr().out
    assert "changed=title" in output
    assert "added=album" in output
    assert "removed=publisher" in output
    assert "artist" not in output
    assert "Error: MP3 file not found:" in output
    assert "Summary: updated=1 unchanged=1 errors=1" in output


def test_tags_extract_without_delete_merges_and_preserves_entries(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies tags-extract merges extracted values without --delete.
    @details Extracts scanned files into an existing manifest while preserving
    tag keys absent from the extraction and entries absent from the scan,
    asserting merged entry state and a zero removed count. Complexity:
    O(F log F). Side effects: temporary manifest write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-035, REQ-060, REQ-061, TST-006
    """
    root = tmp_path / "music"
    song = _write_mp3(root, "song.mp3")
    new_song = _write_mp3(root, "nested/new.MP3")
    manifest = tmp_path / "tags.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "path": "song.mp3",
                    "tags": {"title": "Old", "artist": "Artist", "album": "Preserved"},
                },
                {"path": "stale.mp3", "tags": {"title": "Stale"}},
            ]
        ),
        encoding="utf-8",
    )
    loader = _loader_for(
        {
            song.resolve(): FakeAudio(FakeTag(title="Current", artist="Artist")),
            new_song.resolve(): FakeAudio(FakeTag(title="New")),
        }
    )

    expected_status = 0
    actual_status = tags_extract(root, manifest, loader=loader)

    assert actual_status == expected_status
    assert json.loads(manifest.read_text(encoding="utf-8")) == [
        {"path": "nested/new.MP3", "tags": {"title": "New"}},
        {
            "path": "song.mp3",
            "tags": {"album": "Preserved", "artist": "Artist", "title": "Current"},
        },
        {"path": "stale.mp3", "tags": {"title": "Stale"}},
    ]
    output = capsys.readouterr().out
    assert "Updated song.mp3: title" in output
    assert "stale.mp3" not in output
    assert "Summary: updated=1 added=1 removed=0" in output


def test_update_tags_without_delete_preserves_extra_tags(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies update-tags preserves tags absent from the manifest.
    @details Runs without --delete against a fake audio fixture, applies
    changed and added fields, and asserts the tag absent from the manifest
    keeps its value with exactly one save. Complexity: O(E*T).
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-060, REQ-062, TST-007
    """
    root = tmp_path / "music"
    song = _write_mp3(root, "song.mp3")
    song_tag = FakeTag(title="Old", artist="Artist", publisher="Keep Me")
    manifest = tmp_path / "tags.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "path": "song.mp3",
                    "tags": {"title": "New", "album": "Added"},
                }
            ]
        ),
        encoding="utf-8",
    )
    loader = _loader_for({song.resolve(): FakeAudio(song_tag)})

    expected_status = 0
    actual_status = update_tags(root, manifest, loader=loader)

    assert actual_status == expected_status
    assert song_tag.title == "New"
    assert song_tag.album == "Added"
    assert song_tag.publisher == "Keep Me"
    assert song_tag.save_calls == 1
    output = capsys.readouterr().out
    assert "changed=title" in output
    assert "added=album" in output
    assert "removed=" not in output
    assert "Summary: updated=1 unchanged=0 errors=0" in output


def test_extract_then_update_preserves_already_matching_fixture_bytes(
    tmp_path: Path
) -> None:
    """
    @brief Verifies extraction followed by matching update does not save an MP3.
    @details Uses a stable byte payload and fake save counter to prove the update
    path avoids writes when extracted and current fields are equal.
    Complexity: O(T). Side effects: temporary manifest write only.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @return {None} No value.
    @satisfies TST-008
    """
    root = tmp_path / "music"
    audio_file = _write_mp3(root, "unchanged.mp3", b"original-audio-content")
    original_bytes = audio_file.read_bytes()
    tag = FakeTag(title="Unchanged", track_num=(1, 2))
    loader = _loader_for({audio_file.resolve(): FakeAudio(tag)})
    manifest = tmp_path / "tags.json"

    assert tags_extract(root, manifest, loader=loader) == 0
    assert update_tags(root, manifest, loader=loader) == 0
    assert audio_file.read_bytes() == original_bytes
    assert tag.save_calls == 0


def test_update_then_extract_reproduces_manifest_values(tmp_path: Path) -> None:
    """
    @brief Verifies update then extraction reproduces a supported-field manifest.
    @details Starts with an untagged fake audio object, updates desired values,
    then asserts the extracted array equals the source manifest array.
    Complexity: O(E*T). Side effects: temporary manifest writes.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @return {None} No value.
    @satisfies TST-009
    """
    root = tmp_path / "music"
    audio_file = _write_mp3(root, "nested/song.mp3")
    audio = FakeAudio(None)
    loader = _loader_for({audio_file.resolve(): audio})
    source_manifest = tmp_path / "source.json"
    expected_manifest = [
        {
            "path": "nested/song.mp3",
            "tags": {"artist": "Artist", "title": "Title", "track_num": [1, 3]},
        }
    ]
    source_manifest.write_text(json.dumps(expected_manifest), encoding="utf-8")
    extracted_manifest = tmp_path / "extracted.json"

    assert update_tags(root, source_manifest, loader=loader) == 0
    assert tags_extract(root, extracted_manifest, loader=loader) == 0
    assert json.loads(extracted_manifest.read_text(encoding="utf-8")) == expected_manifest
    assert audio.tag is not None
    assert audio.tag.save_calls == 1


def test_numeric_genre_extract_and_update_round_trip(tmp_path: Path) -> None:
    """
    @brief Verifies numeric non-standard genre values extract and round trip.
    @details Writes a real MP3 whose single TCON frame carries a numeric genre
    string rejected by eyed3.id3.Genre.parse, extracts it through the default
    EyeD3 loader, applies the extracted manifest back without rewriting the
    fixture, applies the same genre to an untagged MP3, and re-extracts.
    Complexity: O(F*T). Side effects: temporary fixture and manifest writes.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @return {None} No value.
    @satisfies REQ-032, REQ-042, REQ-043, REQ-049, REQ-052
    """
    root = tmp_path / "music"
    song = _write_untagged_mp3(root, "song.mp3")
    audio = eyed3.load(str(song))
    assert audio is not None
    tag = audio.initTag()
    assert tag is not None
    tag.title = "Title"
    tag.frame_set[b"TCON"] = TextFrame(b"TCON", text=NUMERIC_GENRE)
    tag.save()
    manifest = tmp_path / "tags.json"
    song_bytes = song.read_bytes()

    expected_status = 0
    extracted_status = tags_extract(root, manifest)

    assert extracted_status == expected_status
    entries = json.loads(manifest.read_text(encoding="utf-8"))
    assert entries[0]["tags"]["genre"] == NUMERIC_GENRE

    applied_status = update_tags(root, manifest)

    assert applied_status == expected_status
    assert song.read_bytes() == song_bytes

    fresh = _write_untagged_mp3(root, "fresh.mp3")
    assert fresh.is_file()
    fresh_manifest = tmp_path / "fresh.json"
    fresh_manifest.write_text(
        json.dumps([{"path": "fresh.mp3", "tags": {"genre": NUMERIC_GENRE}}]),
        encoding="utf-8",
    )

    assert update_tags(root, fresh_manifest) == expected_status
    reproduced = tmp_path / "reproduced.json"
    assert tags_extract(root, reproduced) == expected_status
    reproduced_tags = {
        entry["path"]: entry["tags"]
        for entry in json.loads(reproduced.read_text(encoding="utf-8"))
    }
    assert reproduced_tags["fresh.mp3"]["genre"] == NUMERIC_GENRE


def test_manifest_write_and_read_round_trip_preserves_non_ascii_values(
    tmp_path: Path,
) -> None:
    """
    @brief Verifies tag-manifest writes and reads round-trip non-ASCII values.
    @details Serializes a manifest containing non-ASCII tag values, asserts the
    on-disk bytes decode as UTF-8 with the documented array shape, and asserts
    the loader reproduces the exact path-index mapping.
    Complexity: O(E). Side effects: temporary manifest write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @return {None} No value.
    @satisfies DES-013, DES-014, TST-012
    """
    manifest = tmp_path / "tags.json"
    expected = {"song.mp3": {"title": "Città vecchia", "TXXX:Nota": "Müller ✓"}}

    _write_manifest(manifest, expected)
    decoded = manifest.read_bytes().decode("utf-8")
    actual = _read_manifest(manifest)

    assert json.loads(decoded) == [
        {"path": "song.mp3", "tags": expected["song.mp3"]}
    ]
    assert actual == expected

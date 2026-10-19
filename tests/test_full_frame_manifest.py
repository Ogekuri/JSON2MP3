"""
@brief Defines full-ID3-frame manifest tests using real EyeD3 MP3 fixtures.
@details Covers extraction of every text-bearing frame, canonical frame keys,
synchronized-lyrics round trips, update reconciliation, and binary-frame
preservation on deterministic temporary MP3 files. No network access.
@satisfies TST-010, CTN-006
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import eyed3
from eyed3.id3.frames import (
    CommentFrame,
    Frame,
    LyricsFrame,
    PopularityFrame,
    TermsOfUseFrame,
    TextFrame,
    UrlFrame,
    UserTextFrame,
    UserUrlFrame,
)

from json2mp3.tag_manifest import tags_extract, update_tags

#/** @brief Defines one minimal deterministic MPEG-1 Layer III audio frame.
# * @details Header bytes select 128 kbps, 44.1 kHz, and 417-byte frame size;
# * eight repeated frames make EyeD3 accept the fixture as a valid MP3 file.
# */
_MPEG_FRAME = bytes([0xFF, 0xFB, 0x90, 0x00]) + b"\x00" * 413

#/** @brief Defines the raw synchronized-lyrics payload used by frame fixtures.
# * @details Latin-1 encoding, eng language, millisecond timestamps, content
# * type 1, descriptor LyD, and two timestamped lyric entries.
# */
_SYLT_PAYLOAD = (
    b"\x00"
    + b"eng"
    + bytes([2, 1])
    + b"LyD\x00"
    + b"la la\x00"
    + (1000).to_bytes(4, "big")
    + b"second line\x00"
    + (2500).to_bytes(4, "big")
)


def _write_frame_mp3(
    root: Path,
    relative_path: str,
    *,
    sylt_encoding: bytes = b"\x00",
    sylt_timestamp_format: int = 2,
) -> Path:
    """
    @brief Creates one MP3 fixture carrying attribute, text, and binary frames.
    @details Writes deterministic MPEG frames, then attaches title, TXXX:Keep,
    TXXX:Drop, COMM:eng:cmt, USLT:ita:lr, raw SYLT, and one attached picture
    through the EyeD3 frame set, and saves the tag. Complexity:
    O(frame-byte-count). Side effects: temporary fixture file write.
    @param root {Path} Temporary fixture root.
    @param relative_path {str} Relative MP3 fixture path.
    @param sylt_encoding {bytes} SYLT ID3 text-encoding byte.
    @param sylt_timestamp_format {int} SYLT timestamp format byte.
    @return {Path} Created MP3 fixture path.
    """
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_MPEG_FRAME * 8)
    audio = eyed3.load(str(path))
    assert audio is not None
    tag = audio.initTag()
    assert tag is not None
    tag.title = "Title"
    tag.frame_set[b"TXXX"] = UserTextFrame(description="Keep", text="kept value")
    tag.frame_set[b"TXXX"] = UserTextFrame(description="Drop", text="dropped value")
    tag.frame_set[b"COMM"] = CommentFrame(
        description="cmt", lang=b"eng", text="hello"
    )
    tag.frame_set[b"USLT"] = LyricsFrame(
        description="lr", lang=b"ita", text="testo"
    )
    sylt = Frame(b"SYLT")
    sylt.data = (
        sylt_encoding
        + _SYLT_PAYLOAD[1:4]
        + bytes([sylt_timestamp_format, _SYLT_PAYLOAD[5]])
        + _SYLT_PAYLOAD[6:]
    )
    tag.frame_set[b"SYLT"] = sylt
    tag.images.set(3, b"\x89PNG-fake", "image/png", description="cover")
    tag.save()
    return path


def _write_untagged_mp3(root: Path, relative_path: str) -> Path:
    """
    @brief Creates an MP3 fixture without an ID3 tag.
    @details Writes deterministic MPEG frames without initializing an ID3 tag so
    update_tags creates each manifest field. Complexity: O(frame-byte-count).
    Side effects: temporary fixture file write.
    @param root {Path} Temporary fixture root.
    @param relative_path {str} Relative MP3 fixture path.
    @return {Path} Created untagged MP3 fixture path.
    @satisfies TST-009, TST-010
    """
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_MPEG_FRAME * 8)
    return path


def _load_tag(path: Path) -> Any:
    """
    @brief Loads the EyeD3 tag of one fixture file.
    @details Complexity: external-library bound. Side effects: file read.
    @param path {Path} Existing MP3 fixture path.
    @return {Any} Non-null EyeD3 tag object.
    """
    audio = eyed3.load(str(path))
    assert audio is not None
    assert audio.tag is not None
    return audio.tag


def test_tags_extract_includes_all_text_frames_and_omits_binary(
    tmp_path: Path,
) -> None:
    """
    @brief Verifies extraction covers every text-bearing frame with canonical keys.
    @details Asserts attribute keys, TXXX description keys, COMM and USLT
    language-description keys, the structured SYLT object, and the absence of
    the binary picture frame. Complexity: O(T+F). Side effects: temporary
    manifest write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @return {None} No value.
    @satisfies REQ-052, REQ-053, REQ-054, REQ-055, REQ-056
    """
    root = tmp_path / "music"
    _write_frame_mp3(root, "song.mp3")
    manifest = tmp_path / "tags.json"

    expected_status = 0
    actual_status = tags_extract(root, manifest)

    assert actual_status == expected_status
    entries = json.loads(manifest.read_text(encoding="utf-8"))
    tags = entries[0]["tags"]
    assert tags["title"] == "Title"
    assert tags["TXXX:Keep"] == "kept value"
    assert tags["TXXX:Drop"] == "dropped value"
    assert tags["COMM:eng:cmt"] == "hello"
    assert tags["USLT:ita:lr"] == "testo"
    assert tags["SYLT:eng:LyD"] == {
        "format": 2,
        "type": 1,
        "lyrics": [[1000, "la la"], [2500, "second line"]],
    }
    assert "APIC" not in tags
    assert not any(key.startswith("APIC") for key in tags)


def test_tags_extract_and_update_round_trip_all_sylt_timestamp_formats(
    tmp_path: Path,
) -> None:
    """
    @brief Verifies SYLT timestamp-format round trips across separate MP3 trees.
    @details Extracts two tagged source MP3 fixtures using timestamp formats one
    and two, restores their manifests to untagged same-path targets, and asserts
    byte-stable JSON manifest equivalence after target extraction. Complexity:
    O(F*(T+F)). Side effects: temporary fixture and manifest writes.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @return {None} No value.
    @satisfies REQ-049, REQ-052, REQ-055, TST-009, TST-010
    """
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    format_one_source = _write_frame_mp3(
        source_root,
        "format-one.mp3",
        sylt_encoding=b"\x03",
        sylt_timestamp_format=1,
    )
    source_audio = eyed3.load(str(format_one_source))
    assert source_audio is not None
    assert source_audio.tag is not None
    source_sylt = source_audio.tag.frame_set[b"SYLT"][0]
    source_sylt.data = source_sylt.data.replace(
        b"second line", "\u266a".encode("utf-8")
    )
    source_audio.tag.save()
    _write_frame_mp3(source_root, "nested/format-two.mp3", sylt_timestamp_format=2)
    _write_untagged_mp3(target_root, "format-one.mp3")
    _write_untagged_mp3(target_root, "nested/format-two.mp3")
    source_manifest = tmp_path / "source.json"
    reproduced_manifest = tmp_path / "reproduced.json"

    expected_status = 0
    extracted_status = tags_extract(source_root, source_manifest)
    updated_status = update_tags(target_root, source_manifest)
    reproduced_status = tags_extract(target_root, reproduced_manifest)

    assert extracted_status == expected_status
    assert updated_status == expected_status
    assert reproduced_status == expected_status
    assert (
        reproduced_manifest.read_text(encoding="utf-8")
        == source_manifest.read_text(encoding="utf-8")
    )


def test_update_tags_creates_updates_and_removes_frame_keys(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies update reconciliation over canonical frame keys.
    @details Changes one TXXX value, creates one new TXXX key, removes the
    TXXX:Drop frame and the COMM frame, and asserts resulting frame state and
    detail output. Complexity: O(T+F). Side effects: temporary fixture write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-042, REQ-043, REQ-044
    """
    root = tmp_path / "music"
    song = _write_frame_mp3(root, "song.mp3")
    manifest = tmp_path / "tags.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "path": "song.mp3",
                    "tags": {
                        "title": "Title",
                        "TXXX:Keep": "new kept value",
                        "TXXX:Born": "created value",
                        "USLT:ita:lr": "nuovo testo",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    expected_status = 0
    actual_status = update_tags(root, manifest)

    assert actual_status == expected_status
    tag = _load_tag(song)
    txxx = {
        frame.description: frame.text for frame in tag.frame_set[b"TXXX"]
    }
    assert txxx == {"Keep": "new kept value", "Born": "created value"}
    assert tag.frame_set[b"USLT"][0].text == "nuovo testo"
    assert tag.frame_set[b"COMM"] is None
    assert tag.frame_set[b"SYLT"] is None
    output = capsys.readouterr().out
    assert "changed=TXXX:Keep,USLT:ita:lr" in output
    assert "added=TXXX:Born" in output
    assert (
        "removed=COMM:eng:cmt,SYLT:eng:LyD,TXXX:Drop,disc_num,track_num" in output
    )
    assert "Summary: updated=1 unchanged=0 errors=0" in output


def test_update_tags_removes_sylt_and_preserves_picture_frames(
    tmp_path: Path,
) -> None:
    """
    @brief Verifies SYLT removal and binary-frame preservation.
    @details Applies a manifest without SYLT and asserts the raw frame is gone
    while the attached picture frame survives unchanged. Complexity: O(T+F).
    Side effects: temporary fixture write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @return {None} No value.
    @satisfies REQ-044, REQ-056
    """
    root = tmp_path / "music"
    song = _write_frame_mp3(root, "song.mp3")
    manifest = tmp_path / "tags.json"
    manifest.write_text(
        json.dumps([{"path": "song.mp3", "tags": {"title": "Title"}}]),
        encoding="utf-8",
    )

    expected_status = 0
    actual_status = update_tags(root, manifest)

    assert actual_status == expected_status
    tag = _load_tag(song)
    assert tag.frame_set[b"SYLT"] is None
    pictures = tag.images
    assert len(pictures) == 1
    assert pictures[0].description == "cover"
    assert pictures[0].image_data == b"\x89PNG-fake"


def test_sylt_manifest_round_trip_reproduces_modified_values(
    tmp_path: Path,
) -> None:
    """
    @brief Verifies extraction and update round-trip a modified SYLT manifest.
    @details Extracts the fixture, modifies lyrics entries, applies the manifest,
    and asserts a subsequent extraction equals the modified manifest. Complexity:
    O(T+F). Side effects: temporary manifest writes.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @return {None} No value.
    @satisfies REQ-049, REQ-052, REQ-055
    """
    root = tmp_path / "music"
    _write_frame_mp3(root, "song.mp3")
    extracted = tmp_path / "extracted.json"

    assert tags_extract(root, extracted) == 0
    entries = json.loads(extracted.read_text(encoding="utf-8"))
    sylt_key = "SYLT:eng:LyD"
    entries[0]["tags"][sylt_key]["lyrics"] = [[0, "prima"], [9000, "seconda"]]
    entries[0]["tags"][sylt_key]["type"] = 3
    modified = tmp_path / "modified.json"
    modified.write_text(json.dumps(entries), encoding="utf-8")

    assert update_tags(root, modified) == 0
    reproduced = tmp_path / "reproduced.json"
    assert tags_extract(root, reproduced) == 0
    reproduced_tags = json.loads(reproduced.read_text(encoding="utf-8"))[0][
        "tags"
    ]
    assert reproduced_tags[sylt_key] == {
        "format": 2,
        "type": 3,
        "lyrics": [[0, "prima"], [9000, "seconda"]],
    }


def _write_popm_mp3(root: Path, relative_path: str) -> Path:
    """
    @brief Creates one MP3 fixture carrying two POPM popularimeter frames.
    @details Writes deterministic MPEG frames, then attaches one rated frame
    for user@example.com and one empty-email frame through the EyeD3 frame
    set, and saves the tag. Complexity: O(frame-byte-count). Side effects:
    temporary fixture file write.
    @param root {Path} Temporary fixture root.
    @param relative_path {str} Relative MP3 fixture path.
    @return {Path} Created MP3 fixture path.
    @satisfies TST-011
    """
    path = _write_untagged_mp3(root, relative_path)
    audio = eyed3.load(str(path))
    assert audio is not None
    tag = audio.initTag()
    assert tag is not None
    tag.frame_set[b"POPM"] = PopularityFrame(
        email=b"user@example.com", rating=196, count=42
    )
    tag.frame_set[b"POPM"] = PopularityFrame(email=b"", rating=5, count=0)
    tag.save()
    return path


def test_tags_extract_includes_popularity_frames_with_rating_and_counter(
    tmp_path: Path,
) -> None:
    """
    @brief Verifies extraction keys POPM frames by email with object values.
    @details Extracts a fixture carrying two popularimeter frames and asserts
    one `POPM:<email>` key per frame with integer rating and counter fields.
    Complexity: O(T+F). Side effects: temporary manifest write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @return {None} No value.
    @satisfies REQ-057, TST-011
    """
    root = tmp_path / "music"
    _write_popm_mp3(root, "song.mp3")
    manifest = tmp_path / "tags.json"

    expected_status = 0
    actual_status = tags_extract(root, manifest)

    assert actual_status == expected_status
    entries = json.loads(manifest.read_text(encoding="utf-8"))
    tags = entries[0]["tags"]
    assert tags["POPM:user@example.com"] == {"rating": 196, "counter": 42}
    assert tags["POPM:"] == {"rating": 5, "counter": 0}


def test_popm_round_trip_preserves_fixture_bytes(tmp_path: Path) -> None:
    """
    @brief Verifies POPM extraction and matching update keep fixture bytes stable.
    @details Extracts a popularimeter-tagged fixture, applies the manifest back
    to the same file, and asserts byte identity proving no rewrite occurred.
    Complexity: O(T+F). Side effects: temporary manifest write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @return {None} No value.
    @satisfies REQ-049, REQ-057, REQ-058, TST-011
    """
    root = tmp_path / "music"
    song = _write_popm_mp3(root, "song.mp3")
    original_bytes = song.read_bytes()
    manifest = tmp_path / "tags.json"

    extracted_status = tags_extract(root, manifest)
    updated_status = update_tags(root, manifest)

    assert extracted_status == 0
    assert updated_status == 0
    assert song.read_bytes() == original_bytes


def test_update_tags_creates_updates_and_removes_popularity_frames(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies update reconciliation over POPM keys using both value forms.
    @details Updates one frame through the rating/counter object form, creates
    one frame through the bare integer rating form, and removes the
    empty-email frame absent from the manifest, asserting final frame state and
    detail output. Complexity: O(T+F). Side effects: temporary fixture write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-057, REQ-058
    """
    root = tmp_path / "music"
    song = _write_popm_mp3(root, "song.mp3")
    manifest = tmp_path / "tags.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "path": "song.mp3",
                    "tags": {
                        "POPM:user@example.com": {"rating": 255, "counter": 100},
                        "POPM:other@example.com": 7,
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    expected_status = 0
    actual_status = update_tags(root, manifest)

    assert actual_status == expected_status
    tag = _load_tag(song)
    popularity = {
        frame.email.decode("ascii"): (frame.rating, frame.count)
        for frame in tag.frame_set[b"POPM"]
    }
    assert popularity == {
        "user@example.com": (255, 100),
        "other@example.com": (7, 0),
    }
    output = capsys.readouterr().out
    assert "changed=POPM:user@example.com" in output
    assert "added=POPM:other@example.com" in output
    assert "removed=POPM:" in output
    assert "Summary: updated=1 unchanged=0 errors=0" in output


def test_update_tags_rejects_invalid_popm_values(tmp_path: Path, capsys: Any) -> None:
    """
    @brief Verifies invalid POPM value shapes fail per file without file writes.
    @details Applies one manifest entry with a non-integer rating object and
    one with a boolean rating, asserting per-file error reporting, exit status
    one, and original on-disk frame state for both fixtures.
    Complexity: O(T+F). Side effects: temporary fixture write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-058
    """
    root = tmp_path / "music"
    first = _write_popm_mp3(root, "first.mp3")
    second = _write_popm_mp3(root, "second.mp3")
    manifest = tmp_path / "tags.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "path": "first.mp3",
                    "tags": {"POPM:user@example.com": {"rating": "five"}},
                },
                {"path": "second.mp3", "tags": {"POPM:user@example.com": True}},
            ]
        ),
        encoding="utf-8",
    )

    expected_status = 1
    actual_status = update_tags(root, manifest)

    assert actual_status == expected_status
    for song in (first, second):
        tag = _load_tag(song)
        popularity = {
            frame.email.decode("ascii"): frame.rating
            for frame in tag.frame_set[b"POPM"]
        }
        assert popularity == {"user@example.com": 196, "": 5}
    output = capsys.readouterr().out
    assert output.count("Error: unable to apply tags to") == 2
    assert "Summary: updated=0 unchanged=0 errors=2" in output


def test_update_tags_equivalent_popm_value_shapes_do_not_rewrite(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies update-tags skips equivalent POPM values without saving.
    @details Applies one legacy EyeD3-CLI-shaped object carrying email, rating,
    and count keys equal to the stored frame and one bare integer rating equal
    to the second stored frame, asserting no detail output, an unchanged file
    summary, and byte-identical fixture content. Complexity: O(T+F). Side
    effects: temporary fixture and manifest writes.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-042, REQ-049, REQ-057, REQ-058, TST-011
    """
    root = tmp_path / "music"
    song = _write_popm_mp3(root, "song.mp3")
    original_bytes = song.read_bytes()
    manifest = tmp_path / "tags.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "path": "song.mp3",
                    "tags": {
                        "disc_num": [None, None],
                        "track_num": [None, None],
                        "POPM:user@example.com": {
                            "email": "user@example.com",
                            "rating": 196,
                            "count": 42,
                        },
                        "POPM:": 5,
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    expected_status = 0
    actual_status = update_tags(root, manifest)

    assert actual_status == expected_status
    assert song.read_bytes() == original_bytes
    output = capsys.readouterr().out
    assert "Updated song.mp3" not in output
    assert "Summary: updated=0 unchanged=1 errors=0" in output


def test_update_tags_applies_popm_count_alias_when_counter_differs(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies update-tags applies the legacy count alias play counter.
    @details Applies one minimal rating-only object equal to the stored
    empty-email frame and one legacy count-aliased object whose play counter
    differs, asserting only the differing key is reported and the stored frame
    carries the aliased counter. Complexity: O(T+F). Side effects: temporary
    fixture and manifest writes.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-042, REQ-057, REQ-058, TST-011
    """
    root = tmp_path / "music"
    song = _write_popm_mp3(root, "song.mp3")
    manifest = tmp_path / "tags.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "path": "song.mp3",
                    "tags": {
                        "disc_num": [None, None],
                        "track_num": [None, None],
                        "POPM:user@example.com": {"rating": 196, "count": 99},
                        "POPM:": {"rating": 5},
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    expected_status = 0
    actual_status = update_tags(root, manifest)

    assert actual_status == expected_status
    tag = _load_tag(song)
    popularity = {
        frame.email.decode("ascii"): (frame.rating, frame.count)
        for frame in tag.frame_set[b"POPM"]
    }
    assert popularity == {"user@example.com": (196, 99), "": (5, 0)}
    output = capsys.readouterr().out
    assert "changed=POPM:user@example.com" in output
    assert "POPM:" not in output.replace("changed=POPM:user@example.com", "")
    assert "Summary: updated=1 unchanged=0 errors=0" in output


def _write_extra_frame_mp3(root: Path, relative_path: str) -> Path:
    """
    @brief Creates one MP3 fixture carrying URL, terms-of-use, and generic frames.
    @details Writes deterministic MPEG frames, then attaches WXXX, USER, TIT1,
    TBPM, and WOAR frames through the EyeD3 frame set, and saves the tag.
    Complexity: O(frame-byte-count). Side effects: temporary fixture file
    write.
    @param root {Path} Temporary fixture root.
    @param relative_path {str} Relative MP3 fixture path.
    @return {Path} Created fixture path.
    @satisfies TST-010
    """
    path = _write_untagged_mp3(root, relative_path)
    audio = eyed3.load(str(path))
    assert audio is not None
    tag = audio.initTag()
    assert tag is not None
    tag.frame_set[b"WXXX"] = UserUrlFrame(
        description="site", url="https://example.org"
    )
    tag.frame_set[b"USER"] = TermsOfUseFrame(
        text="All rights reserved", lang=b"eng"
    )
    tag.frame_set[b"TIT1"] = TextFrame(b"TIT1", text="Group")
    tag.frame_set[b"TBPM"] = TextFrame(b"TBPM", text="128")
    tag.frame_set[b"WOAR"] = UrlFrame(b"WOAR", url="https://artist.example")
    tag.save()
    return path


def test_update_tags_round_trips_url_terms_of_use_and_generic_frames(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies update reconciliation over WXXX, USER, and generic frames.
    @details Changes WXXX and USER values and the generic TIT1 text, adds the
    generic TSSE text and WOAF URL frames, keeps TBPM equal, removes WOAR, and
    asserts resulting frame state and detail output. Complexity: O(T+F). Side
    effects: temporary fixture write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-042, REQ-043, REQ-044, REQ-053, REQ-054, TST-010
    """
    root = tmp_path / "music"
    song = _write_extra_frame_mp3(root, "song.mp3")
    manifest = tmp_path / "tags.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "path": "song.mp3",
                    "tags": {
                        "disc_num": [None, None],
                        "track_num": [None, None],
                        "TBPM": "128",
                        "TIT1": "New Group",
                        "TSSE": "Lavf60.16.100",
                        "USER:eng": "Updated terms",
                        "WOAF": "https://file.example",
                        "WXXX:site": "https://changed.example",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    expected_status = 0
    actual_status = update_tags(root, manifest)

    assert actual_status == expected_status
    tag = _load_tag(song)
    assert tag.frame_set[b"WXXX"][0].url == "https://changed.example"
    assert tag.frame_set[b"USER"][0].text == "Updated terms"
    assert tag.frame_set[b"USER"][0].lang == b"eng"
    assert tag.frame_set[b"TIT1"][0].text == "New Group"
    assert tag.frame_set[b"TBPM"][0].text == "128"
    assert tag.frame_set[b"TSSE"][0].text == "Lavf60.16.100"
    assert tag.frame_set[b"WOAF"][0].url == "https://file.example"
    assert tag.frame_set[b"WOAR"] is None
    output = capsys.readouterr().out
    assert "changed=TIT1,USER:eng,WXXX:site" in output
    assert "added=TSSE,WOAF" in output
    assert "removed=WOAR" in output
    assert "TBPM" not in output
    assert "Summary: updated=1 unchanged=0 errors=0" in output


def _write_id3v22_mp3(root: Path, relative_path: str) -> Path:
    """
    @brief Creates one MP3 fixture carrying a hand-rendered ID3v2.2 tag.
    @details EyeD3 cannot write ID3v2.2 tags, so this helper prepends raw tag
    bytes with the v2.2 syncsafe header, a TT2 title frame, and an SLT
    synchronized-lyrics frame to deterministic MPEG frames. Complexity:
    O(frame-byte-count). Side effects: temporary fixture file write.
    @param root {Path} Temporary fixture root.
    @param relative_path {str} Relative MP3 fixture path.
    @return {Path} Created fixture path.
    @satisfies TST-013
    """
    def frame22(fid: bytes, data: bytes) -> bytes:
        return fid + len(data).to_bytes(3, "big") + data

    tag_size = len(frame22(b"TT2", b"\x00Title22")) + len(
        frame22(b"SLT", _SYLT_PAYLOAD)
    )
    syncsafe_size = bytes(
        [
            (tag_size >> 21) & 0x7F,
            (tag_size >> 14) & 0x7F,
            (tag_size >> 7) & 0x7F,
            tag_size & 0x7F,
        ]
    )
    v22_tag = (
        b"ID3\x02\x00\x00"
        + syncsafe_size
        + frame22(b"TT2", b"\x00Title22")
        + frame22(b"SLT", _SYLT_PAYLOAD)
    )
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(v22_tag + _MPEG_FRAME * 8)
    return path


def test_tags_extract_and_update_round_trip_id3v22_sylt(tmp_path: Path) -> None:
    """
    @brief Verifies SYLT and title extraction from ID3v2.2 tags round trips.
    @details EyeD3 normalizes ID3v2.2 frame identifiers on parse and cannot
    write ID3v2.2 tags, so the fixture tag is extracted through tags-extract
    and restored through update-tags onto an untagged ID3v2.4 target, asserting
    byte-stable manifest equivalence. Complexity: O(F*(T+F)). Side effects:
    temporary fixture and manifest writes.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @return {None} No value.
    @satisfies REQ-052, REQ-053, REQ-054, REQ-055, TST-013
    """
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    _write_id3v22_mp3(source_root, "old22.mp3")
    _write_untagged_mp3(target_root, "old22.mp3")
    source_manifest = tmp_path / "source.json"
    reproduced_manifest = tmp_path / "reproduced.json"
    source_audio = eyed3.load(str(source_root / "old22.mp3"))
    assert source_audio is not None
    assert source_audio.tag is not None
    assert source_audio.tag.version == (2, 2, 0)

    expected_status = 0
    extracted_status = tags_extract(source_root, source_manifest)
    updated_status = update_tags(target_root, source_manifest)
    reproduced_status = tags_extract(target_root, reproduced_manifest)

    assert extracted_status == expected_status
    assert updated_status == expected_status
    assert reproduced_status == expected_status
    tags = json.loads(source_manifest.read_text(encoding="utf-8"))[0]["tags"]
    assert tags["title"] == "Title22"
    assert tags["SYLT:eng:LyD"] == {
        "format": 2,
        "type": 1,
        "lyrics": [[1000, "la la"], [2500, "second line"]],
    }
    assert (
        reproduced_manifest.read_text(encoding="utf-8")
        == source_manifest.read_text(encoding="utf-8")
    )


def test_update_tags_reports_error_for_unsaveable_id3v22_file(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies update-tags reports ID3v2.2 save failure as a file error.
    @details EyeD3 raises NotImplementedError for ID3v2.2 writes, so applying a
    changed title to the v2.2 fixture must count one per-file error, leave the
    fixture bytes untouched, still update a writable sibling entry, and still
    print the closing summary. Complexity: O(E*(T+F)). Side effects: temporary
    fixture and manifest writes.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-041, REQ-047, TST-013
    """
    root = tmp_path / "music"
    old22 = _write_id3v22_mp3(root, "old22.mp3")
    _write_untagged_mp3(root, "fresh.mp3")
    original_bytes = old22.read_bytes()
    manifest = tmp_path / "tags.json"
    manifest.write_text(
        json.dumps(
            [
                {"path": "old22.mp3", "tags": {"title": "NewTitle"}},
                {"path": "fresh.mp3", "tags": {"title": "Fresh"}},
            ]
        ),
        encoding="utf-8",
    )

    expected_status = 1
    actual_status = update_tags(root, manifest)

    assert actual_status == expected_status
    assert old22.read_bytes() == original_bytes
    fresh_tag = _load_tag(root / "fresh.mp3")
    assert fresh_tag.title == "Fresh"
    output = capsys.readouterr().out
    assert "Error: unable to save tags to" in output
    assert "Unable to write ID3 v2.2" in output
    assert "Updated fresh.mp3" in output
    assert "Summary: updated=1 unchanged=0 errors=1" in output


def _write_multi_sylt_mp3(root: Path, relative_path: str) -> Path:
    """
    @brief Creates one MP3 fixture carrying two same-language SYLT frames.
    @details Attaches raw SYLT frames with descriptors LyD and Alt under one
    eng language through the EyeD3 frame set, and saves the tag. Complexity:
    O(frame-byte-count). Side effects: temporary fixture file write.
    @param root {Path} Temporary fixture root.
    @param relative_path {str} Relative MP3 fixture path.
    @return {Path} Created fixture path.
    @satisfies TST-013
    """
    path = _write_untagged_mp3(root, relative_path)
    audio = eyed3.load(str(path))
    assert audio is not None
    tag = audio.initTag()
    assert tag is not None
    first = Frame(b"SYLT")
    first.data = _SYLT_PAYLOAD
    second = Frame(b"SYLT")
    second.data = _SYLT_PAYLOAD.replace(b"LyD", b"Alt")
    tag.frame_set[b"SYLT"] = first
    tag.frame_set[b"SYLT"] = second
    tag.save()
    return path


def test_update_tags_round_trips_multiple_same_language_sylt_frames(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies one of multiple same-language SYLT keys changes in place.
    @details Extracts both SYLT:eng:LyD and SYLT:eng:Alt keys, applies a
    manifest that replaces only the Alt lyrics, asserts the LyD frame is
    preserved, and reproduces the applied manifest by re-extraction.
    Complexity: O(T+F). Side effects: temporary fixture and manifest writes.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-042, REQ-043, REQ-044, REQ-052, REQ-053, REQ-055, TST-013
    """
    root = tmp_path / "music"
    song = _write_multi_sylt_mp3(root, "song.mp3")
    extracted = tmp_path / "extracted.json"

    expected_status = 0
    assert tags_extract(root, extracted) == expected_status
    entries = json.loads(extracted.read_text(encoding="utf-8"))
    tags = entries[0]["tags"]
    assert tags["SYLT:eng:LyD"]["lyrics"] == [[1000, "la la"], [2500, "second line"]]
    assert tags["SYLT:eng:Alt"]["lyrics"] == [[1000, "la la"], [2500, "second line"]]
    tags["SYLT:eng:Alt"]["lyrics"] = [[0, "uno"], [9000, "due"]]
    modified = tmp_path / "modified.json"
    modified.write_text(json.dumps(entries), encoding="utf-8")

    actual_status = update_tags(root, modified)

    assert actual_status == expected_status
    tag = _load_tag(song)
    assert len(tag.frame_set[b"SYLT"]) == 2
    output = capsys.readouterr().out
    assert "changed=SYLT:eng:Alt" in output
    assert "SYLT:eng:LyD" not in output
    assert "Summary: updated=1 unchanged=0 errors=0" in output
    reproduced = tmp_path / "reproduced.json"
    assert tags_extract(root, reproduced) == expected_status
    assert json.loads(reproduced.read_text(encoding="utf-8")) == json.loads(
        modified.read_text(encoding="utf-8")
    )


def _write_grouping_mp3(root: Path, relative_path: str) -> Path:
    """
    @brief Creates one MP3 fixture carrying grouping and empty-key frames.
    @details Attaches TIT1 and TKEY generic text frames, an empty-description
    COMM:eng frame, an empty-description USLT:und frame, and one rated POPM
    frame through the EyeD3 frame set, and saves the tag. Complexity:
    O(frame-byte-count). Side effects: temporary fixture file write.
    @param root {Path} Temporary fixture root.
    @param relative_path {str} Relative MP3 fixture path.
    @return {Path} Created fixture path.
    @satisfies TST-014
    """
    path = _write_untagged_mp3(root, relative_path)
    audio = eyed3.load(str(path))
    assert audio is not None
    tag = audio.initTag()
    assert tag is not None
    tag.frame_set[b"TIT1"] = TextFrame(b"TIT1", text="Group")
    tag.frame_set[b"TKEY"] = TextFrame(b"TKEY", text="A")
    tag.frame_set[b"COMM"] = CommentFrame(description="", lang=b"eng", text="c")
    tag.frame_set[b"USLT"] = LyricsFrame(
        description="", lang=b"und", text="l"
    )
    tag.frame_set[b"POPM"] = PopularityFrame(
        email=b"user@example.com", rating=196, count=42
    )
    tag.save()
    return path


def test_update_tags_round_trips_tit1_and_empty_description_frames(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies TIT1 grouping and empty-description keys round trip.
    @details Extracts TIT1, TKEY, COMM:eng:, USLT:und:, and the POPM frame,
    applies a manifest that regroups TIT1, keeps the remaining keys, and binds
    the popularimeter through the legacy EyeD3-CLI object, asserting only TIT1
    changes and a re-extraction reproduces the applied manifest. Complexity:
    O(T+F). Side effects: temporary fixture and manifest writes.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-042, REQ-052, REQ-053, REQ-054, REQ-057, REQ-059, TST-014
    """
    root = tmp_path / "music"
    _write_grouping_mp3(root, "song.mp3")
    extracted = tmp_path / "extracted.json"

    expected_status = 0
    assert tags_extract(root, extracted) == expected_status
    entries = json.loads(extracted.read_text(encoding="utf-8"))
    tags = entries[0]["tags"]
    assert tags["TIT1"] == "Group"
    assert tags["TKEY"] == "A"
    assert tags["COMM:eng:"] == "c"
    assert tags["USLT:und:"] == "l"
    assert tags["POPM:user@example.com"] == {"rating": 196, "counter": 42}
    tags["TIT1"] = "New Group"
    tags["POPM:user@example.com"] = {
        "email": "user@example.com",
        "rating": 196,
        "count": 42,
    }
    modified = tmp_path / "modified.json"
    modified.write_text(json.dumps(entries), encoding="utf-8")

    actual_status = update_tags(root, modified)

    assert actual_status == expected_status
    output = capsys.readouterr().out
    assert "changed=TIT1" in output
    assert "Summary: updated=1 unchanged=0 errors=0" in output
    reproduced = tmp_path / "reproduced.json"
    assert tags_extract(root, reproduced) == expected_status
    reproduced_tags = json.loads(reproduced.read_text(encoding="utf-8"))[0][
        "tags"
    ]
    assert reproduced_tags["TIT1"] == "New Group"
    assert reproduced_tags["POPM:user@example.com"] == {
        "rating": 196,
        "counter": 42,
    }
    assert reproduced_tags == {
        key: value
        for key, value in json.loads(modified.read_text(encoding="utf-8"))[0][
            "tags"
        ].items()
        if key != "POPM:user@example.com"
    } | {"POPM:user@example.com": {"rating": 196, "counter": 42}}


def test_update_tags_ignores_binary_frame_manifest_keys(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies binary-frame manifest keys are ignored and images preserved.
    @details Submits APIC, GEOB, TOC, and MCDI manifest keys together with an
    unchanged title, asserting a zero status with no per-file error, a
    byte-identical attached picture, and absence of bogus frames replacing
    binary frames. Complexity: O(F). Side effects: temporary fixture and
    manifest writes.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-044, REQ-047, REQ-056
    """
    root = tmp_path / "music"
    song = _write_frame_mp3(root, "song.mp3")
    expected_image_data = _load_tag(song).frame_set[b"APIC"][0].image_data
    manifest = tmp_path / "tags.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "path": "song.mp3",
                    "tags": {
                        "title": "Title",
                        "TXXX:Keep": "kept value",
                        "TXXX:Drop": "dropped value",
                        "COMM:eng:cmt": "hello",
                        "USLT:ita:lr": "testo",
                        "SYLT:eng:LyD": {
                            "format": 2,
                            "type": 1,
                            "lyrics": [[1000, "la la"], [2500, "second line"]],
                        },
                        "track_num": [None, None],
                        "disc_num": [None, None],
                        "APIC": "jpeg-data-here",
                        "GEOB": "object-data-here",
                        "TOC": "chapter-one",
                        "MCDI": "toc-id-here",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    expected_status = 0
    actual_status = update_tags(root, manifest)

    assert actual_status == expected_status
    output = capsys.readouterr().out
    assert "Error:" not in output
    assert "Summary: updated=0 unchanged=1 errors=0" in output
    tag = _load_tag(song)
    images = tag.frame_set[b"APIC"]
    assert len(images) == 1
    assert images[0].image_data == expected_image_data
    assert tag.frame_set[b"GEOB"] is None
    assert tag.frame_set[b"TOC"] is None
    assert tag.frame_set[b"MCDI"] is None
    assert tag.title == "Title"


def test_tags_extract_round_trips_every_attribute_field(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies all 13 attribute fields survive extraction and re-application.
    @details Writes one MP3 fixture carrying every SUPPORTED_TAG_FIELDS value,
    extracts it, re-applies the manifest with update_tags asserting an unchanged
    file, and asserts a second extraction reproduces the first manifest exactly.
    Complexity: O(T+F). Side effects: temporary fixture and manifest writes.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-042, REQ-049, REQ-052
    """
    root = tmp_path / "music"
    path = root / "song.mp3"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_MPEG_FRAME * 8)
    audio = eyed3.load(str(path))
    assert audio is not None
    tag = audio.initTag()
    assert tag is not None
    tag.title = "T"
    tag.artist = "AR"
    tag.album = "AL"
    tag.album_artist = "AA"
    tag.composer = "CO"
    tag.publisher = "PU"
    tag.copyright = "CR"
    tag.genre = "Rock"
    tag.track_num = (3, 12)
    tag.disc_num = (1, 2)
    tag.recording_date = "2024-01-02"
    tag.release_date = "2024-02-03"
    tag.original_release_date = "1999-12-31"
    tag.save()

    expected_attributes = {
        "title": "T",
        "artist": "AR",
        "album": "AL",
        "album_artist": "AA",
        "composer": "CO",
        "publisher": "PU",
        "copyright": "CR",
        "genre": "(17)Rock",  # EyeD3 str(Genre) display form; reparse-stable.
        "track_num": [3, 12],
        "disc_num": [1, 2],
        "recording_date": "2024-01-02",
        "release_date": "2024-02-03",
        "original_release_date": "1999-12-31",
    }

    extracted = tmp_path / "extracted.json"
    expected_status = 0
    assert tags_extract(root, extracted) == expected_status
    tags = json.loads(extracted.read_text(encoding="utf-8"))[0]["tags"]
    assert tags == expected_attributes

    actual_status = update_tags(root, extracted)
    assert actual_status == expected_status
    assert "Summary: updated=0 unchanged=1 errors=0" in capsys.readouterr().out

    reproduced = tmp_path / "reproduced.json"
    assert tags_extract(root, reproduced) == expected_status
    reproduced_tags = json.loads(reproduced.read_text(encoding="utf-8"))[0][
        "tags"
    ]
    assert reproduced_tags == expected_attributes


def test_update_tags_tit1_grouping_adds_updates_and_removes(
    tmp_path: Path, capsys: Any
) -> None:
    """
    @brief Verifies the TIT1 grouping frame add, update, and remove lifecycle.
    @details Runs update_tags three times against one untagged fixture: first
    adding TIT1, then changing its value, then removing it through an empty
    tag object, asserting frame state and detail output after each run.
    Complexity: O(F). Side effects: temporary fixture and manifest writes.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param capsys {Any} Pytest stdout capture fixture.
    @return {None} No value.
    @satisfies REQ-042, REQ-043, REQ-044, TST-014
    """
    root = tmp_path / "music"
    song = _write_untagged_mp3(root, "song.mp3")
    expected_status = 0

    added_manifest = tmp_path / "added.json"
    added_manifest.write_text(
        json.dumps([{"path": "song.mp3", "tags": {"TIT1": "Group One"}}]),
        encoding="utf-8",
    )
    assert update_tags(root, added_manifest) == expected_status
    assert _load_tag(song).frame_set[b"TIT1"][0].text == "Group One"
    assert "added=TIT1" in capsys.readouterr().out

    changed_manifest = tmp_path / "changed.json"
    changed_manifest.write_text(
        json.dumps([{"path": "song.mp3", "tags": {"TIT1": "Group Two"}}]),
        encoding="utf-8",
    )
    assert update_tags(root, changed_manifest) == expected_status
    assert _load_tag(song).frame_set[b"TIT1"][0].text == "Group Two"
    assert "changed=TIT1" in capsys.readouterr().out

    removed_manifest = tmp_path / "removed.json"
    removed_manifest.write_text(
        json.dumps([{"path": "song.mp3", "tags": {}}]),
        encoding="utf-8",
    )
    assert update_tags(root, removed_manifest) == expected_status
    assert _load_tag(song).frame_set[b"TIT1"] is None
    assert "removed=TIT1" in capsys.readouterr().out

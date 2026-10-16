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
    UserTextFrame,
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


def _write_frame_mp3(root: Path, relative_path: str) -> Path:
    """
    @brief Creates one MP3 fixture carrying attribute, text, and binary frames.
    @details Writes deterministic MPEG frames, then attaches title, TXXX:Keep,
    TXXX:Drop, COMM:eng:cmt, USLT:ita:lr, raw SYLT, and one attached picture
    through the EyeD3 frame set, and saves the tag. Complexity:
    O(frame-byte-count). Side effects: temporary fixture file write.
    @param root {Path} Temporary fixture root.
    @param relative_path {str} Relative MP3 fixture path.
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
    sylt.data = _SYLT_PAYLOAD
    tag.frame_set[b"SYLT"] = sylt
    tag.images.set(3, b"\x89PNG-fake", "image/png", description="cover")
    tag.save()
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

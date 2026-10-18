"""
@brief Defines UTF-8 file-encoding tests for core JSON manifest and cache I/O.
@details Covers UTF-8 decoding of sync manifests, UTF-8 persistence of the
version-check cache, and cache-reader round trips without network access or
locale dependence. Filesystem state is restricted to pytest temporary
directories and the cache path is injected per test.
@satisfies DES-013, DES-014, TST-012
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import json2mp3.core as core
from json2mp3.core import (
    _cache_is_active,
    _human_timestamp,
    _load_tracks,
    _write_cache,
)


def test_load_tracks_reads_utf8_manifest_with_non_ascii_values(tmp_path: Path) -> None:
    """
    @brief Verifies sync manifest loading decodes explicit UTF-8 file content.
    @details Writes a manifest containing non-ASCII tag values as UTF-8 bytes
    and asserts the loader reproduces the exact track objects.
    Complexity: O(manifest-size). Side effects: temporary manifest write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @return {None} No value.
    @satisfies DES-013, TST-012
    """
    manifest = tmp_path / "tracks.json"
    expected_track = {
        "path": "song.mp3",
        "tags": {"title": "Città vecchia", "artist": "Müller & 東京"},
    }
    manifest.write_text(json.dumps({"files": [expected_track]}), encoding="utf-8")

    expected_output = [expected_track]
    actual_output = _load_tracks(manifest)

    assert actual_output == expected_output


def test_write_cache_persists_utf8_document_and_reader_round_trips(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """
    @brief Verifies cache persistence writes UTF-8 JSON the cache reader accepts.
    @details Redirects the cache path into the temporary directory, persists a
    fixed-epoch cache document, asserts the raw bytes decode as UTF-8 with the
    exact documented fields, and asserts the reader re-loads the same window.
    Complexity: O(1). Side effects: temporary cache file write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param monkeypatch {Any} Pytest monkeypatch fixture redirecting CACHE_FILE.
    @return {None} No value.
    @satisfies DES-013, DES-014, TST-012
    """
    cache_path = tmp_path / "cache" / "check.json"
    monkeypatch.setattr(core, "CACHE_FILE", cache_path)
    fixed_now = 1_000_000.0

    _write_cache(3600, now=fixed_now)

    data = json.loads(cache_path.read_bytes().decode("utf-8"))
    assert data["last_check_epoch"] == fixed_now
    assert data["idle_time_epoch"] == fixed_now + 3600
    assert data["last_check_human"] == _human_timestamp(fixed_now)
    assert data["idle_time_human"] == _human_timestamp(fixed_now + 3600)
    assert _cache_is_active(now=fixed_now + 1) is True


def test_cache_is_active_decodes_utf8_cache_bytes(tmp_path: Path, monkeypatch: Any) -> None:
    """
    @brief Verifies the cache reader decodes explicitly UTF-8 encoded bytes.
    @details Writes a future idle window as raw UTF-8 bytes and asserts the
    reader reports the window active without locale-dependent decoding.
    Complexity: O(1). Side effects: temporary cache file write.
    @param tmp_path {Path} Pytest isolated temporary directory.
    @param monkeypatch {Any} Pytest monkeypatch fixture redirecting CACHE_FILE.
    @return {None} No value.
    @satisfies DES-013, TST-012
    """
    cache_path = tmp_path / "check.json"
    monkeypatch.setattr(core, "CACHE_FILE", cache_path)
    cache_path.write_bytes(json.dumps({"idle_time_epoch": 2_000_000}).encode("utf-8"))

    assert _cache_is_active(now=1_999_999.0) is True

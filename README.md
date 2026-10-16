# json2mp3 / j2m (0.0.0)

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/license-GPL--3.0-491?style=flat-square" alt="License: GPL-3.0">
  <img src="https://img.shields.io/badge/platform-Linux-6A7EC2?style=flat-square&logo=terminal&logoColor=white" alt="Platforms">
  <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
</p>

<p align="center">
<strong>Sync ID3 tags with a JSON file</strong><br>
json2mp3 synchronizes ID3 metadata of MP3 libraries with JSON manifests. It can
extract tags from nested MP3 folders into a JSON file, apply a JSON file to MP3
tags, and write individual Mutagen ID3 frames from a track manifest.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> |
  <a href="#commands">Commands</a> |
  <a href="#json-manifest-formats">JSON Manifest Formats</a> |
  <a href="#install-with-astral-uv">Install</a>
</p>

## Quick Start

```bash
uvx --from git+https://github.com/Ogekuri/JSON2MP3.git json2mp3 --help
```

For a local checkout, use the launcher:

```bash
./scripts/j2m.sh --help
```

## Commands

```text
json2mp3 [command] [options]

Management Commands:
  --upgrade    Reinstall json2mp3 on Linux; print manual command elsewhere.
  --uninstall  Uninstall json2mp3 on Linux; print manual command elsewhere.
  --ver        Print the json2mp3 version (forces an online version check).
  --version    Print the json2mp3 version (forces an online version check).
  --help       Print the full help screen or the help of a specific command.

Commands:
  sync          Write Mutagen ID3 frames from a track manifest to MP3 files.
  tags-extract  Extract EyeD3 tags of nested MP3 files into a JSON manifest.
  update-tags   Apply EyeD3 tag values from a JSON manifest to MP3 files.
```

Command-specific help:

```bash
json2mp3 --help sync
json2mp3 --help tags-extract
json2mp3 --help update-tags
```

### tags-extract

```bash
json2mp3 tags-extract <mp3_root> <json_file>
```

Recursively scans `<mp3_root>` for `.mp3` files (case-insensitive), extracts
their ID3 tags with EyeD3, and reconciles `<json_file>`:

- a missing JSON file is created as a new manifest;
- existing entries are refreshed using the relative file path as the key;
- entries for files that no longer exist are removed;
- files not yet in the manifest are appended;
- changed field names are printed only for entries that were already present;
- a summary with updated, added, and removed file counts is always printed.

### update-tags

```bash
json2mp3 update-tags <mp3_root> <json_file>
```

Reads the JSON manifest and updates the ID3 tags of the referenced MP3 files
with EyeD3. Paths in the manifest are resolved relative to `<mp3_root>`:

- differing tags are updated, missing tags are added, and extra tags are
  removed;
- binary frames such as attached pictures are preserved unchanged;
- unchanged tags are left untouched and never printed;
- changed, added, and removed tag names are printed per updated file;
- missing MP3 files are reported as errors and processing continues;
- a summary with updated, unchanged, and error file counts is always printed.

### sync

```bash
json2mp3 sync <json_file> [--dry-run]
```

Writes selected ID3 frames to MP3 files listed in a track manifest using
Mutagen. Relative paths are resolved against the manifest directory.
`--dry-run` prints the files that would be updated without writing.

## JSON Manifest Formats

### tags-extract / update-tags (EyeD3)

A JSON array sorted by relative path. Every text-bearing ID3 frame is
extracted: scalar attribute fields (`title`, `artist`, `album`,
`album_artist`, `composer`, `publisher`, `copyright`, `genre`, `track_num`,
`disc_num`, `recording_date`, `release_date`, `original_release_date`) plus
canonical frame keys for all remaining frames. Binary frames such as attached
pictures are preserved untouched and never appear in the manifest.

```json
[
  {
    "path": "nested/song.mp3",
    "tags": {
      "title": "Song",
      "artist": "Artist",
      "album": "Album",
      "track_num": [1, 10],
      "recording_date": "2025",
      "TXXX:MOOD": "energetic",
      "COMM:eng:": "a comment",
      "USLT:und:": "plain lyrics",
      "SYLT:und:LRCLIB": {
        "format": 2,
        "type": 1,
        "lyrics": [[0, "first line"], [4200, "second line"]]
      },
      "TBPM": "128"
    }
  }
]
```

Frame key syntax: `TXXX:<description>` and `WXXX:<description>` for
user-defined frames, `COMM:<language>:<description>`,
`USLT:<language>:<description>`, and `SYLT:<language>:<description>` for
language frames, `USER:<language>` for terms of use, and the bare frame
identifier (for example `TBPM`) for other text and URL frames.

### sync (Mutagen)

An object with a `files` array of track entries. Supported fields are `title`,
`artist`, `album`, `albumartist`, `date`, `year`, `genre`, `tracknumber`,
`discnumber`, and `comment`.

```json
{
  "files": [
    {
      "path": "music/example.mp3",
      "tags": {
        "title": "Example",
        "artist": "An Artist",
        "tracknumber": "1/10"
      }
    }
  ]
}
```

## Install with Astral uv

#### Install

```bash
uv tool install json2mp3 --force --from git+https://github.com/Ogekuri/JSON2MP3.git
```

#### Uninstall

```bash
uv tool uninstall json2mp3
```

The installed commands are `json2mp3` and its short alias `j2m`.

## Live execution with uvx

```bash
uvx --from git+https://github.com/Ogekuri/JSON2MP3.git json2mp3 <args>
```

## Version check

Every invocation consults a local cache and, when the cache is expired, checks
the latest GitHub release. Failed checks retry after one day and never prevent
local commands from running.

## Tests

```bash
uv run --group dev pytest
```

The suite covers manifest reconciliation, field additions/updates/removals,
and extraction/update round trips that preserve or reproduce the input data.

## Acknowledgments

Built with [Astral uv](https://docs.astral.sh/uv/), [EyeD3](https://eyed3.readthedocs.io/),
[Mutagen](https://mutagen.readthedocs.io/), and [pytest](https://pytest.org).

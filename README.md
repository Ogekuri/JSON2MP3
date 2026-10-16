# json2mp3 / j2m (0.0.0)

**json2mp3** synchronises ID3 metadata in MP3 files with a JSON manifest. It is
a Python 3.11+ command-line application distributed as an Astral UV tool.

## Install with Astral uv

```bash
uv tool install json2mp3 --force --from git+https://github.com/Ogekuri/JSON2MP3.git
```

The installed commands are `json2mp3` and its short alias, `j2m`.

To run without installing it first:

```bash
uvx --from git+https://github.com/Ogekuri/JSON2MP3.git json2mp3 --help
```

For a local checkout, use the launcher:

```bash
./scripts/j2m.sh --help
```

## Synchronise tags

Use `sync` with a JSON manifest. Paths relative to the manifest are resolved
relative to the manifest's directory.

```json
{
  "files": [
    {
      "path": "music/example.mp3",
      "tags": {
        "title": "Example",
        "artist": "An Artist",
        "album": "An Album",
        "date": "2025",
        "genre": "Electronic",
        "tracknumber": "1/10"
      }
    }
  ]
}
```

Then run:

```bash
json2mp3 sync tags.json
json2mp3 sync tags.json --dry-run
```

Supported tag names are `title`, `artist`, `album`, `albumartist`, `date`
(or `year`), `genre`, `tracknumber`, `discnumber`, and `comment`.

## Management commands

```text
json2mp3 --ver
json2mp3 --upgrade
json2mp3 --uninstall
```

`--ver` and `--version` also force a check for the latest GitHub release.
Other invocations use a one-hour local check cache. Failed checks use a
one-day retry delay and never prevent local commands from running.

## Uninstall

```bash
uv tool uninstall json2mp3
```

## License

GPL-3.0-only. Copyright © Francesco Rolando.

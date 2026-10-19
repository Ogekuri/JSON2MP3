# json2mp3 Workflow Model

## Execution Units Index

| ID | Type | Parent | Role | Entrypoint(s) | Defining File(s) |
|---|---|---|---|---|---|
| PROC:main | process | - | Single-process CLI runtime performing update checks, management commands, Mutagen sync, and EyeD3 manifest extraction/update. | `main` (console scripts `json2mp3` and `j2m`; `python -m json2mp3`; `python -m j2m`) | `src/json2mp3/core.py`, `src/json2mp3/tag_manifest.py`, `src/json2mp3/__main__.py`, `src/j2m/__main__.py`, `src/j2m/core.py` |
| PROC:uv-tool | process | PROC:main | Short-lived child process executing the external `uv` tool manager. | external `uv` executable; no internal entrypoint | (no internal definitions under `src/`) |

- PROC:main: no explicit threads detected.
- PROC:uv-tool: no explicit threads detected; implementation entirely outside `src/`.

## Execution Units

### PROC:main

- Entrypoints:
  - `main` — console-script target for `json2mp3` and `j2m` commands; default argument source is `sys.argv[1:]`.
  - module guard in `src/json2mp3/__main__.py` — invokes `main` and raises `SystemExit` for `python -m json2mp3`.
  - module guard in `src/j2m/__main__.py` — invokes `main` re-exported by `src/j2m/core.py` for `python -m j2m`.
- Lifecycle/trigger: starts at interpreter invocation of any entrypoint; blocks synchronously on HTTPS I/O during the update check and on child-process completion for upgrade/uninstall; terminates after returning an integer status to the interpreter (`SystemExit`).
- Internal Call-Trace Tree:
  - `main(...)`: dispatch the CLI argument sequence to management or synchronisation flows [`src/json2mp3/core.py`]
    - external: `sys.argv` read when no argument sequence is supplied
    - `check_for_update(...)`: run the cached or forced release check and print update/error notices [`src/json2mp3/core.py`]
      - forced when arguments contain `--ver` or `--version`; skipped when the cache idle window is active
      - `_cache_is_active(...)`: report whether the cached idle window is still active [`src/json2mp3/core.py`]
        - `_cache_path(...)`: return the canonical cache file path [`src/json2mp3/core.py`]
        - external: UTF-8 cache file read and JSON parse, epoch clock read
      - `_fetch_latest_version(...)`: fetch and validate the latest release tag [`src/json2mp3/core.py`]
        - external: HTTPS GET with 2-second timeout, response body read, JSON parse
      - on success: `_write_cache(...)`: persist check and idle timestamps with the 3600-second delay [`src/json2mp3/core.py`]
        - `_cache_path(...)`: return the canonical cache file path [`src/json2mp3/core.py`]
        - `_human_timestamp(...)`: format an epoch value as local timezone-aware ISO 8601 [`src/json2mp3/core.py`]
        - external: cache directory creation, UTF-8 cache file write
      - on success: `_is_newer_version(...)`: compare candidate and installed releases [`src/json2mp3/core.py`]
        - `_version_key(...)`: normalise a release tag into a numeric tuple [`src/json2mp3/core.py`]
        - `_print_coloured(...)`: print the bright-green update notice when newer [`src/json2mp3/core.py`]
          - external: stdout write
      - on failure: `_print_coloured(...)`: print the bright-red failure notice [`src/json2mp3/core.py`]
        - external: stdout write
      - on failure: `_write_cache(...)`: persist check and idle timestamps with the 86400-second delay [`src/json2mp3/core.py`]
        - `_cache_path(...)`: return the canonical cache file path [`src/json2mp3/core.py`]
        - `_human_timestamp(...)`: format an epoch value as local timezone-aware ISO 8601 [`src/json2mp3/core.py`]
        - external: cache directory creation, UTF-8 cache file write
      - on cache write failure: `_print_coloured(...)`: print the bright-red cache-error notice [`src/json2mp3/core.py`]
        - external: stdout write
    - `_sync_parser(...)`: build the argparse parser for the `sync` command [`src/json2mp3/core.py`]
      - external: argparse help rendering or argument parsing (`--help sync` and `sync` branches)
    - `_tag_command_parser(...)`: build positional parsers plus the shared `--delete` switch for `tags-extract` and `update-tags` [`src/json2mp3/core.py`]
      - external: argparse help rendering and argument parsing
    - `tags_extract(...)`: recursively reconcile all EyeD3 text-bearing and popularimeter MP3 frames into a JSON array, merging into and preserving entries absent from the scan without `--delete`, and replacing plus removing them with `--delete` [`src/json2mp3/tag_manifest.py`]
      - without `--delete`: extracted values update differing keys and add missing keys while existing keys absent from the extraction are preserved; entries absent from the scan are carried into the written manifest and the removed count stays zero
      - `_read_manifest(...)`: load existing JSON array entries into a normalized path index [`src/json2mp3/tag_manifest.py`]
      - `_scan_mp3_files(...)`: recursively discover sorted `.mp3` paths [`src/json2mp3/tag_manifest.py`]
        - `_normalise_relative_path(...)`: create a POSIX-relative path key [`src/json2mp3/tag_manifest.py`]
      - `_load_audio(...)`: load one MP3 through EyeD3 [`src/json2mp3/tag_manifest.py`]
        - external: EyeD3 MP3 parse; module import sets the stdlib `eyed3` logger level to ERROR, filtering WARNING-level EyeD3 records (unsupported frames, non-standard genres) before stderr emission
      - `_tag_values(...)`: extract attribute fields plus every text-bearing and popularimeter ID3 frame [`src/json2mp3/tag_manifest.py`]
        - `_attribute_value(...)`: read one attribute field, falling back to the covering ATTRIBUTE_FRAME_IDS frame when EyeD3 raises GenreException [`src/json2mp3/tag_manifest.py`]
        - `_normalise_value(...)`: convert EyeD3 values to JSON-compatible values [`src/json2mp3/tag_manifest.py`]
        - `_normalise_frame_id(...)`: normalize ID3v2.2 frame identifiers to four characters [`src/json2mp3/tag_manifest.py`]
        - `_frame_key(...)`: compute the canonical manifest key for one frame [`src/json2mp3/tag_manifest.py`]
          - `_parse_sylt_payload(...)`: decode a raw SYLT frame payload into lang, description, format, type, and timestamped entries [`src/json2mp3/tag_manifest.py`]
            - `_split_terminated(...)`: split a payload at its ID3 string terminator [`src/json2mp3/tag_manifest.py`]
            - `_decode_id3_string(...)`: decode one ID3 text field by its encoding byte [`src/json2mp3/tag_manifest.py`]
        - `_frame_value(...)`: compute the JSON value for one text-bearing or POPM popularity frame [`src/json2mp3/tag_manifest.py`]
          - `_parse_sylt_payload(...)`: decode a raw SYLT frame payload into lang, description, format, type, and timestamped entries [`src/json2mp3/tag_manifest.py`]
      - `_changed_fields(...)`: identify changed tag keys [`src/json2mp3/tag_manifest.py`]
      - `_write_manifest(...)`: serialize the reconciled sorted JSON array [`src/json2mp3/tag_manifest.py`]
        - external: JSON file write
    - `update_tags(...)`: reconcile EyeD3 MP3 tags of every manifest key from a JSON array [`src/json2mp3/tag_manifest.py`]
      - without `--delete`: settable tags present in the target and absent from the manifest are preserved instead of removed; with `--delete` they are removed while binary frames stay preserved
      - `_read_manifest(...)`: load source JSON array entries into a normalized path index [`src/json2mp3/tag_manifest.py`]
      - `_load_audio(...)`: load one target MP3 through EyeD3 [`src/json2mp3/tag_manifest.py`]
        - external: EyeD3 MP3 parse and optional tag initialization; WARNING-level EyeD3 records filtered by the `eyed3` logger ERROR threshold configured at module import
      - `_tag_values(...)`: read current attribute and frame tag values [`src/json2mp3/tag_manifest.py`]
        - `_attribute_value(...)`: read one attribute field, falling back to the covering ATTRIBUTE_FRAME_IDS frame when EyeD3 raises GenreException [`src/json2mp3/tag_manifest.py`]
        - `_normalise_value(...)`: convert EyeD3 values to JSON-compatible values [`src/json2mp3/tag_manifest.py`]
        - `_normalise_frame_id(...)`: normalize ID3v2.2 frame identifiers to four characters [`src/json2mp3/tag_manifest.py`]
        - `_frame_key(...)`: compute the canonical manifest key for one frame [`src/json2mp3/tag_manifest.py`]
          - `_parse_sylt_payload(...)`: decode a raw SYLT frame payload into lang, description, format, type, and timestamped entries [`src/json2mp3/tag_manifest.py`]
            - `_split_terminated(...)`: split a payload at its ID3 string terminator [`src/json2mp3/tag_manifest.py`]
            - `_decode_id3_string(...)`: decode one ID3 text field by its encoding byte [`src/json2mp3/tag_manifest.py`]
        - `_frame_value(...)`: compute the JSON value for one text-bearing or POPM popularity frame [`src/json2mp3/tag_manifest.py`]
          - `_parse_sylt_payload(...)`: decode a raw SYLT frame payload into lang, description, format, type, and timestamped entries [`src/json2mp3/tag_manifest.py`]
      - `_canonical_value(...)`: map one compared tag value onto its canonical rating-counter form so equivalent POPM manifest shapes compare equal [`src/json2mp3/tag_manifest.py`]
        - `_popularity_values(...)`: normalize one POPM manifest value into rating and counter integers with the legacy count alias [`src/json2mp3/tag_manifest.py`]
      - `_is_settable_key(...)`: validate one manifest key as an attribute or canonical frame key, rejecting binary frame identifiers for preservation [`src/json2mp3/tag_manifest.py`]
        - `_parse_frame_key(...)`: parse one manifest key into a frame construction specification, restricting generic identifiers to the EyeD3 text/URL frame tables [`src/json2mp3/tag_manifest.py`]
      - `_set_tag_field(...)`: assign or clear one attribute or frame tag key [`src/json2mp3/tag_manifest.py`]
        - GenreException raised by EyeD3 attribute setters for non-standard numeric genre strings falls back to covering-frame replacement through `_set_frame_field`
        - `_parse_frame_key(...)`: parse one manifest key into a frame construction specification, restricting generic identifiers to the EyeD3 text/URL frame tables [`src/json2mp3/tag_manifest.py`]
        - `_set_frame_field(...)`: replace or remove the frames bound to one canonical key [`src/json2mp3/tag_manifest.py`]
          - `_matching_frames(...)`: list frames whose canonical key equals one key [`src/json2mp3/tag_manifest.py`]
            - `_frame_key(...)`: compute the canonical manifest key for one frame [`src/json2mp3/tag_manifest.py`]
          - `_build_frame(...)`: construct one EyeD3 frame from a key specification and value [`src/json2mp3/tag_manifest.py`]
            - `_text_value(...)`: coerce one manifest scalar into a frame text string [`src/json2mp3/tag_manifest.py`]
            - `_popularity_values(...)`: normalize one POPM manifest value into rating and counter integers with the legacy count alias [`src/json2mp3/tag_manifest.py`]
            - `_render_sylt_payload(...)`: serialize one SYLT manifest value into raw payload bytes [`src/json2mp3/tag_manifest.py`]
              - `_id3_encoding_for(...)`: select Latin-1 or UTF-8 with a one-byte terminator for deterministic SYLT serialization [`src/json2mp3/tag_manifest.py`]
              - `_encode_id3_string(...)`: encode one string with a selected ID3 encoding [`src/json2mp3/tag_manifest.py`]
        - external: EyeD3 tag save when a file has differences; binary frames such as attached pictures are never removed; save failures such as the ID3v2.2 `NotImplementedError` and OS errors are reported as per-file errors without aborting the run
    - `_run_tool_command(...)`: execute or print the `uv` tool install/uninstall command [`src/json2mp3/core.py`]
      - external: platform detection; child-process spawn (`subprocess.run`) into PROC:uv-tool with inherited stdio
      - `_print_coloured(...)`: print the bright-red message when the child cannot be spawned [`src/json2mp3/core.py`]
        - external: stdout write
    - `sync_from_json(...)`: synchronise ID3 tags from a manifest to MP3 files [`src/json2mp3/core.py`]
      - external: manifest path expansion and resolution
      - `_load_tracks(...)`: parse and validate the manifest structure [`src/json2mp3/core.py`]
        - external: UTF-8 manifest file read, JSON parse
      - per track: external: target path expansion, relative-path join with the manifest parent, existence check
      - per track under `--dry-run`: external: stdout `Would update` write
      - per track: `_write_id3_tags(...)`: write supported ID3 frames to one target file [`src/json2mp3/core.py`]
        - external: mutagen ID3 load, empty-tag creation on missing ID3 header, frame delete/add, file save
      - per track failure: `_print_coloured(...)`: print the bright-red track error [`src/json2mp3/core.py`]
        - external: stdout write
      - per track success: external: stdout `Updated` write
    - `_print_coloured(...)`: print the bright-red unknown-command message [`src/json2mp3/core.py`]
      - external: stdout write
    - external: stdout writes for full help text and the version string
- External Boundaries:
  - network: HTTPS GET to the GitHub latest-release endpoint with a 2-second timeout.
  - filesystem: version-check cache read/write as UTF-8 JSON under `$HOME/.cache/json2mp3/`.
  - filesystem: UTF-8 JSON manifest read/write; target MP3 read/write through Mutagen and EyeD3.
  - logging: EyeD3 WARNING-level library records filtered at the stdlib `eyed3` logger (level `EYED3_LOG_LEVEL = ERROR`) configured once at module import of `src/json2mp3/tag_manifest.py`; ERROR-or-higher records still propagate to configured root handlers.
  - OS: platform detection, child-process spawn of `uv`, directory traversal, and stdout writes.

### PROC:uv-tool

- Entrypoints: external `uv` executable invoked as `uv tool install json2mp3 --force --from git+https://github.com/Ogekuri/JSON2MP3.git` or `uv tool uninstall json2mp3`; no symbols defined under `src/`.
- Lifecycle/trigger: spawned synchronously by PROC:main in `_run_tool_command` on Linux only; runs the requested tool operation to completion; parent resumes with the child exit code.
- Internal Call-Trace Tree: none — no internal functions under `src/`; implementation is external.
- External Boundaries: network access to PyPI/Git and tool-store file I/O performed entirely by the external `uv` implementation.

## Communication Edges

- PROC:main -> PROC:uv-tool: mechanism `subprocess.run` child-process spawn with inherited stdin/stdout/stderr; endpoint `uv` executable argv (`tool install json2mp3 --force --from git+https://github.com/Ogekuri/JSON2MP3.git` or `tool uninstall json2mp3`); payload argv tokens; return payload integer exit code consumed as the `_run_tool_command` result; declaration `src/json2mp3/core.py`.
- No thread-based, queue-based, socket-based, or signal-based edges exist between execution units; no explicit threads are detected in `src/`.

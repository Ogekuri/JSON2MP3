# json2mp3 Requirements

## 1. Introduction

### 1.1 Document Rules

- **DES-001**: MUST maintain this SRS in English using RFC 2119 keywords and stable unique requirement identifiers.
- **DES-002**: MUST express each requirement as one atomic, testable sentence using the canonical requirement-line format.

### 1.2 Project Scope

json2mp3 0.0.0 is a Python CLI that writes selected ID3 metadata to files described by a JSON manifest. The documented scope is the implemented `src/` behavior; no unit-test source exists in `tests/`.

### 1.3 Repository Structure

```text
.
├── pyproject.toml
├── uv.lock
├── src/
│   ├── j2m/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   └── core.py
│   └── json2mp3/
│       ├── __init__.py
│       ├── __main__.py
│       └── core.py
└── pi-usereq/
    └── docs/
        └── REQUIREMENTS.md
```

## 2. Project Requirements

### 2.1 Project Functions

- **PRJ-001**: MUST expose `json2mp3` and `j2m` console commands that invoke `json2mp3.core:main`.
- **PRJ-002**: MUST synchronize selected ID3 tag frames from a JSON manifest to existing filesystem files.
- **PRJ-003**: MUST provide CLI management commands for help, version display, upgrade, and uninstall.
- **PRJ-004**: MUST check the GitHub latest-release endpoint before command dispatch unless an active version-check cache suppresses it.
- **PRJ-005**: MUST retain `j2m` as a compatibility package that delegates its entry point to `json2mp3.core.main`.

### 2.2 Project Constraints

- **CTN-001**: MUST require Python version 3.11 or later.
- **CTN-002**: MUST declare `mutagen>=1.47` as the runtime dependency for ID3 frame operations.
- **CTN-003**: MUST use setuptools package discovery rooted at `src` for the `json2mp3` and `j2m` packages.
- **CTN-004**: MUST treat missing `tests/` as absent unit-test coverage evidence, not as evidence of tested behavior.

## 3. Requirements

### 3.1 Design and Implementation

- **DES-003**: MUST expose package version `0.0.0` from `json2mp3.__version__`.
- **DES-004**: MUST terminate `python -m json2mp3` with the integer returned by `json2mp3.core.main`.
- **DES-005**: MUST centralize command dispatch, release checks, manifest loading, and ID3 writes in `json2mp3.core`.
- **DES-006**: MUST store version-check cache data at `$HOME/.cache/json2mp3/check_version_idle-time.json`.
- **DES-007**: MUST serialize cache fields `last_check_epoch`, `last_check_human`, `idle_time_epoch`, and `idle_time_human`.
- **DES-008**: MUST render cache human timestamps as timezone-aware local ISO 8601 values with second precision.
- **DES-009**: MUST emit ANSI bright-green update messages and ANSI bright-red error messages through the CLI output path.
- **DES-010**: MUST record no explicit performance optimizations identified because source contains no optimization-specific implementation evidence.

### 3.2 Functions

- **REQ-001**: MUST invoke `check_for_update` before dispatching every CLI argument sequence.
- **REQ-002**: MUST force the update check when CLI arguments contain `--ver` or `--version`.
- **REQ-003**: MUST skip a non-forced update request when cached `idle_time_epoch` is greater than the current epoch.
- **REQ-004**: MUST request `https://api.github.com/repos/Ogekuri/JSON2MP3/releases/latest` with a two-second timeout.
- **REQ-005**: MUST cache a valid latest-release response for 3600 seconds, including when no newer version exists.
- **REQ-006**: MUST cache HTTP, URL, parsing, runtime, or filesystem update-check failures for 86400 seconds and continue CLI dispatch.
- **REQ-007**: MUST report an available update only when a numeric release tuple exceeds the installed numeric version tuple.
- **REQ-008**: MUST treat unequal nonnumeric normalized release strings as available updates without determining their ordering.
- **REQ-009**: MUST print the predefined full help text and return zero when invoked without arguments or only with `--help`.
- **REQ-010**: MUST print the `sync` argparse help when invoked as `--help sync`.
- **REQ-011**: MUST print an ANSI red unknown-command message, then full help, and return two for unsupported command sequences.
- **REQ-012**: MUST print `0.0.0` and return zero for exactly `--ver` or exactly `--version`.
- **REQ-013**: MUST execute `uv tool install json2mp3 --force --from git+https://github.com/Ogekuri/JSON2MP3.git` for exactly `--upgrade` on Linux.
- **REQ-014**: MUST execute `uv tool uninstall json2mp3` for exactly `--uninstall` on Linux.
- **REQ-015**: MUST print the applicable manual UV command and return zero instead of executing upgrade or uninstall on non-Linux platforms.
- **REQ-016**: MUST load a manifest only when its root JSON value is an object.
- **REQ-017**: MUST accept manifest tracks from an object `files` list, an object `tracks` list, or an object mapping paths to tag objects.
- **REQ-018**: MUST reject a manifest list containing a non-object track with a manifest-load error.
- **REQ-019**: MUST require each processed track to contain a string `path` or `file` and an object `tags`.
- **REQ-020**: MUST resolve a relative track path against the manifest file parent directory.
- **REQ-021**: MUST report a missing target path as a per-track failure without attempting an ID3 write.
- **REQ-022**: MUST print `Would update: <path>` without writing tags when `sync` receives `--dry-run`.
- **REQ-023**: MUST continue processing subsequent tracks after an individual track validation or ID3-write failure.
- **REQ-024**: MUST return one when any track fails and zero when every track succeeds or is dry-run eligible.
- **REQ-025**: MUST write only provided non-null `title`, `artist`, `album`, `albumartist`, `date`, `year`, `genre`, `tracknumber`, and `discnumber` fields.
- **REQ-026**: MUST replace existing ID3 frames for each supplied supported non-comment tag field before adding its new frame.
- **REQ-027**: MUST map both `date` and `year` to `TDRC`, with `year` overwriting `date` when both fields are present.
- **REQ-028**: MUST replace all `COMM` frames with one UTF-8 English empty-description comment when a non-null `comment` field is supplied.
- **REQ-029**: MUST silently ignore manifest tag keys outside the supported fields.
- **REQ-030**: MUST create an empty ID3 tag when Mutagen reports that an existing target file lacks an ID3 header.
- **REQ-031**: MUST return two after reporting a manifest read, filesystem, JSON-parse, or root-shape error.

## 4. Test Requirements

- **TST-001**: MUST verify REQ-009 by invoking `main([])` and `main(["--help"])` and asserting return zero plus full-help output.
- **TST-002**: MUST verify REQ-003 by writing a future `idle_time_epoch`, injecting a failing opener, and asserting no opener invocation.
- **TST-003**: MUST verify REQ-005 and REQ-006 by injecting successful and failing release openers and asserting respective cache durations.
- **TST-004**: MUST verify REQ-017 through REQ-024 using valid, invalid, missing, relative, and dry-run manifest track fixtures.
- **TST-005**: MUST verify REQ-025 through REQ-030 using a temporary ID3-capable file and assertions for resulting Mutagen frames.

### 4.1 Test Coverage Evidence

No `tests/` directory exists. No automated implementation test coverage or failing-test evidence is available for the inferred functionality.

## 5. Evidence Matrix

| Requirement IDs | Evidence |
|---|---|
| DES-001, DES-002 | `Requirements_Template.md` — document-rule and canonical requirement-line guidance. |
| PRJ-001, CTN-003 | `pyproject.toml` `[project.scripts]` — `json2mp3 = "json2mp3.core:main"`; `[tool.setuptools.packages.find]`. |
| PRJ-002, PRJ-003, PRJ-004 | `src/json2mp3/core.py` — `sync_from_json`, `main`, `check_for_update`. |
| PRJ-005, DES-005 | `src/j2m/core.py` — `from json2mp3.core import main`; `src/json2mp3/core.py` module implementation. |
| CTN-001, CTN-002 | `pyproject.toml` — `requires-python = ">=3.11"`; `mutagen>=1.47`. |
| CTN-004 | Repository evidence — `find tests` reports no such directory. |
| DES-003, DES-004 | `src/json2mp3/__init__.py` — `__version__ = "0.0.0"`; `src/json2mp3/__main__.py` — `raise SystemExit(main())`. |
| DES-006, DES-007, DES-008 | `src/json2mp3/core.py` `CACHE_FILE`, `_write_cache`, `_human_timestamp`. |
| DES-009 | `src/json2mp3/core.py` `GREEN`, `RED`, `_print_coloured`. |
| DES-010 | `src/json2mp3/` source — no benchmark, profiling, optimization annotation, or specialized algorithm evidence. |
| REQ-001, REQ-002, REQ-009 through REQ-015 | `src/json2mp3/core.py` `main`, `_sync_parser`, `_run_tool_command`. |
| REQ-003 through REQ-008 | `src/json2mp3/core.py` `_cache_is_active`, `_fetch_latest_version`, `check_for_update`, `_is_newer_version`. |
| REQ-016 through REQ-018, REQ-031 | `src/json2mp3/core.py` `_load_tracks` — object-root validation and `ValueError` conversion. |
| REQ-019 through REQ-024 | `src/json2mp3/core.py` `sync_from_json` — track validation, relative path resolution, failure counting, and dry run. |
| REQ-025 through REQ-030 | `src/json2mp3/core.py` `_write_id3_tags` — `frames` map, `COMM`, `ID3NoHeaderError`, and `ID3.save`. |
| TST-001 through TST-005 | Derived verification procedures traceable to the cited executable functions; no existing test source is present. |

# Changelog

## [0.1.0](https://github.com/Ogekuri/JSON2MP3/releases/tag/v0.1.0) - 2026-10-20
### ⛰️  Features
- support ID3 POPM popularimeter frames in tag manifests [useReq] *(tag_manifest)*
  - Extend REQUIREMENTS.md with REQ-057, REQ-058, and TST-011 for POPM support.
  - Extract POPM frames as POPM:<email> keys with rating/counter object values.
  - Build PopularityFrame updates from integer rating or rating/counter objects.
  - Reject boolean and non-integer POPM values as per-file update errors.
  - Add POPM extraction, round-trip, reconciliation, and error tests (TST-011).
  - Update WORKFLOW.md call traces and regenerate REFERENCES.md.
- add EyeD3 extraction and update commands [useReq] *(tag-manifest)*
  - Add recursive JSON manifest extraction and ID3 reconciliation commands.
  - Add deterministic round-trip and field mutation coverage.
  - Update SRS, runtime workflow, and generated references.
- Initial commit.

### 🐛  Bug Fixes
- reject binary frame keys and harden tag coverage [useReq] *(tag_manifest)*
  - Restrict generic manifest frame keys to EyeD3 text/URL frame tables
  - (_SETTABLE_FRAME_FIDS) so APIC/GEOB/TOC/MCDI keys are silently ignored
  - and binary frames such as attached pictures stay preserved (REQ-056).
  - Add regression tests: binary-frame manifest keys ignored with
  - byte-identical image, all 13 attribute fields round trip, TIT1
  - grouping add/update/remove lifecycle (TST-009, TST-010, TST-014).
  - Update WORKFLOW.md call-trace roles and regenerate REFERENCES.md.
- skip equivalent POPM rewrites and honor count alias [useReq] *(tag_manifest)*
  - Normalize POPM manifest values to canonical rating-counter pairs before
  - equality so REQ-058-accepted shapes (bare int, rating-only object, legacy
  - eyeD3-CLI email/rating/count object) no longer rewrite unchanged files
  - (REQ-042, REQ-049, REQ-057, REQ-058)
  - Accept legacy count key as play-counter alias when counter is absent,
  - preventing play-counter resets from count-bearing manifests
  - Add failing-first unit tests for equivalent-shape no-rewrite and alias
  - application, plus coverage for WXXX, USER, generic text, and URL frames
  - (TST-010, TST-011)
  - Update WORKFLOW.md call traces and regenerate REFERENCES.md
- preserve Unicode SYLT round trips [useReq] *(tag_manifest)*
  - Preserve SYLT manifests with Unicode lyrics.\nAdd a two-file extraction/update/extraction regression test.\nUpdate runtime and reference documentation.
- recover numeric genre extraction via raw-frame fallback [useReq] *(tag_manifest)*
  - tags-extract aborted with eyed3.id3.GenreException when a stored TCON
  - genre held a numeric string outside the standard genre map (e.g. 1985);
  - the exception bypassed eyed3's ValueError guard and the manifest write.
  - _tag_values reads attribute fields through new _attribute_value(),
  - falling back to the covering ATTRIBUTE_FRAME_IDS frame text on
  - GenreException (REQ-049, REQ-052)
  - _set_tag_field falls back to covering-frame replacement when the
  - eyed3 genre setter rejects the value (REQ-042, REQ-043)
  - add failing-first reproducer test for the extract/update round trip
  - of genre "1985" (TST-006, TST-007, TST-009 scope)
  - update WORKFLOW.md call traces and regenerate REFERENCES.md
- suppress eyed3 warning noise in CLI output [useReq] *(tag_manifest)*
  - Set stdlib eyed3 logger level to ERROR at module import so WARNING
  - records (unsupported frames like SYLT, non-standard genre names) no
  - longer leak to stderr via the logging last-resort handler.
  - tags-extract/update-tags output now matches REQ-037/REQ-038/REQ-039
  - contract: changed-field details plus summary only.
  - Add failing-first reproducer unit test with a real EyeD3 MP3 fixture.
  - Update WORKFLOW.md runtime model and regenerate REFERENCES.md.
- Update .gitignore file.

### 🚜  Changes
- gate tag deletion behind --delete option [useReq] *(tag_manifest)*
  - Add boolean --delete option to tags-extract and update-tags parsers (REQ-060).
  - tags-extract without --delete merges extracted values into existing entries
  - and preserves entries absent from the scan (REQ-034, REQ-035, REQ-061).
  - update-tags without --delete preserves target tags absent from the
  - manifest; removal happens only with --delete (REQ-044, REQ-062).
  - Update TST-006/TST-007 plus removal suites to cover both modes and add
  - merge/preserve coverage tests.
- formalize legacy POPM shape and v2.2 SYLT coverage [useReq] *(tag_manifest)*
  - REQ-059: document the legacy EyeD3-CLI POPM object with ignored email
  - member and count play-counter alias applied when counter is absent
  - TST-013/TST-014: round-trip SYLT from hand-rendered ID3v2.2 tags,
  - multiple same-language SYLT keys, TIT1 grouping, empty-description
  - COMM/USLT keys, and legacy POPM objects through both manifest commands
  - update_tags reports EyeD3 save failures (ID3v2.2 NotImplementedError,
  - OS errors) as per-file errors so the REQ-047 summary always prints
  - Update WORKFLOW.md save boundary and regenerate REFERENCES.md
- enforce UTF-8 contract for JSON file save and load [useReq] *(core)*
  - Add DES-013 and DES-014 mandating explicit UTF-8 for manifest and cache file I/O.
  - Add TST-012 with regression tests for non-ASCII manifest and cache round trips.
  - Annotate WORKFLOW.md cache and manifest filesystem boundaries as UTF-8.
  - No source changes required: existing reads and writes already pass UTF-8 explicitly.
- extract and reconcile all ID3 frames [useReq] *(tag_manifest)*
  - Add REQ-052..REQ-056 and TST-010; generalize REQ-044 and REQ-049.
  - tags-extract now emits every text-bearing frame: TXXX/WXXX description
  - keys, COMM/USLT/SYLT language keys, USER, and plain frame IDs.
  - SYLT parsed and rendered by a dedicated codec (eyed3 lacks support).
  - update-tags creates, updates, and removes all manifest tag keys while
  - preserving binary frames such as attached pictures.
  - Add tests/test_full_frame_manifest.py (TST-010); update README,
  - WORKFLOW, and REFERENCES.
- document tag commands in inline help and README [useReq] *(docs)*
  - List sync, tags-extract, and update-tags in the full help screen.
  - Add command-specific parser descriptions.
  - Rewrite README with commands and both manifest formats.
  - Extend SRS with REQ-050 and REQ-051.


# History

- \[0.1.0\]: https://github.com/Ogekuri/JSON2MP3/releases/tag/v0.1.0

[0.1.0]: https://github.com/Ogekuri/JSON2MP3/releases/tag/v0.1.0

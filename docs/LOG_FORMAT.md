# Standalone log format: cartverity-native/1

Native reports are ASCII key/value lines saved under:

```text
SD:/gm9/out/dscheck/native_YYMMDD_hhmmss_0000.txt
```

The decimal suffix selects an unused filename. Timestamps come from the console
RTC and can be wrong. No report is created when discovery/reference checks fail;
log setup must succeed before the scan starts.

Split each line at the first `=`. Ignore unknown future keys. Repeated keys use
their last value, **except `changed_region_offset` is a list**: retain every
occurrence. `state=INCOMPLETE` is written before scanning and `state=COMPLETE`
after the outcome is recorded. A complete report can describe a cancelled or
failed scan. Missing completion means the report may be interrupted or partial.

| Field | Meaning |
| --- | --- |
| `format` | `cartverity-native/1` |
| `state` | Initial INCOMPLETE; final COMPLETE if report writing reaches the end |
| `version` | Native app version, such as `0.2.0-alpha.4` |
| `godmode9_base` | Pinned upstream base, `2.2.3` |
| `display_refresh_ms` | Configured display update interval |
| `reference_policy` | AUTO, REQUIRE or IGNORE |
| `rom_view` | `full_standard_nds` |
| `game_code_hex`, `revision_hex` | Raw header identifiers encoded in hexadecimal |
| `rom_bytes` | Full normalized ROM length |
| `reference_path` | Candidate reference path; present even if none was loaded |
| `reference_state` | NOT_PROVIDED, SUPPLIED_UNAUTHENTICATED or DATABASE_LOADED |
| `reference_sha1` | Supplied digest if loaded; not proof that comparison completed |
| `database_path`, `database_entries` | Validated offline database path and entry count, if used |
| `reference_source`, `reference_version` | Imported source label (No-Intro and DAT name) and version |
| `reference_source_url`, `reference_dat_sha256` | Official source URL and SHA-256 of the original XML DAT |
| `database_result` | NOT_USED, NOT_COMPARED, MATCH or NO_MATCH |
| `reference_title` | Matched database title, only on an exact SHA-1 and size match |
| `region_size` | Logical comparison size, 1048576 bytes |
| `scope` | Normalized view, per-pass initialization and bus-reporting limitation |
| `result` | Outcome described in [usage](USAGE.md#understand-the-result) |
| `pass1_bytes`, `pass2_bytes` | Successfully processed bytes per pass |
| `sha1_pass1`, `sha1_pass2` | Digests only for completed passes |
| `elapsed_ms` | Scan elapsed time, including per-pass initialization |
| `regions_compared`, `regions_changed` | Region comparisons completed and differences found |
| `changed_region_offset` | Repeated decimal start offsets of differing 1 MiB regions |
| `read_detail` | Context such as two-pass operation, removal or identity failure |

The native format has no `rom=`, `script_version=`, `read_result=` or
`reference_result=` fields. Use `reference_path` for the exact sidecar filename.
Ignore policy records NOT_PROVIDED because no reference was loaded; check
`reference_policy` to distinguish intentional skipping. DATABASE_LOADED does
not mean a match: check `database_result` and final `result`. MATCH produces
MATCHES_DATABASE. NO_MATCH retains CONSISTENT_UNVERIFIED; it is not a damage
verdict. Cancelled/failed/differing reads leave NOT_COMPARED. No source metadata
authenticates the input. [Attribution](REFERENCE_SOURCES.md).

Logs are flushed before scanning and synced/closed afterward, with write results
checked. A storage fault may still truncate or corrupt them. The screen only
reports a saved log after a completed report and successful sync/close. A final
marker is not a transaction or a cartridge pass verdict.

Logs contain game identifiers, reference paths/hashes, results and a timestamp
in their filename. They contain no ROM payload, save or console serial. Review
them before sharing.

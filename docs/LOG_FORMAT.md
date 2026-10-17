# Log format: ds-cart-check/1

Logs are UTF-8-compatible ASCII key/value lines. Split each line at its first `=`. The order is useful to humans but readers should use keys. Repeated keys take their last value; `state=INCOMPLETE` is replaced by `state=COMPLETE` only at a normal finish. An empty value is allowed. Unknown future keys should be ignored.

Path: `/gm9/out/dscheck/YYMMDD_hhmmss_????.txt`. GodMode9 chooses unused suffix characters with `findnot`; clients must not assume the suffix is decimal. Console timestamps come from its RTC and can be wrong. No log is written when the initial prompt is declined or if log setup cannot start.

| Field | Meaning |
| --- | --- |
| `format` | Always `ds-cart-check/1` for this release. |
| `state` | `INCOMPLETE` followed by `COMPLETE` at the normal end. |
| `script_version` | Project version. |
| `gm9_version`, `console_type` | GodMode9 version and its `ONTYPE` value. |
| `started`, `finished` | Console RTC date/time. |
| `view`, `algorithm`, `scope` | Full standard NDS view, SHA1, virtual view including caches. |
| `rom` | Full cartridge path; absent if discovery fails. |
| `game_code_hex`, `revision_hex` | NDS header bytes at 0x0C and 0x1E, logged as hex. |
| `reference_path` | Candidate reference sidecar; its presence does not mean it was loaded. |
| `reference_sha1` | Reference digest if its structure was accepted. |
| `sha1_pass1`, `sha1_pass2` | Digests only for successfully completed hash commands. |
| `read_result` | `NOT_STARTED`, `CONSISTENT`, `INCONSISTENT`, `PASS1_FAILED_OR_CANCELLED`, or `PASS2_FAILED_OR_CANCELLED`. |
| `reference_result` | `NOT_PROVIDED`, `INVALID_OR_UNREADABLE`, `LOADED`, `MATCH`, or `MISMATCH`. |
| `result` | Overall outcome listed in the README. |

`LOADED` means the reference was readable but not compared because two consistent passes were not obtained. `INVALID_OR_UNREADABLE` and `NOT_PROVIDED` never produce a reference mismatch verdict. A consistent run with either is still `CONSISTENT_UNVERIFIED`.

Discovery and read failures can end with `state=COMPLETE`: it means the script recorded its outcome, not that the cartridge passed. SD write failures stop execution, so final outcome fields can be absent. The marker is not an atomic storage guarantee.

The file in `examples/` is synthetic documentation. Its hashes are not references for any game.

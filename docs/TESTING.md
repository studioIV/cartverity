# Testing and release readiness

## Current evidence

- Official GodMode9 v2.2.3 source was reviewed for every used command, cartridge view construction, hash calls, and unsupported verification behavior.
- Static validation and modeled scenario tests run offline with the Python standard library.
- `tools/check_upstream.py` verifies source hashes and command signatures against `upstream-lock.json`.
- No physical console or cartridge was available during initial development.

There is no claim of physical New 3DS XL validation. Keep the initial release marked as awaiting hardware testing until reports demonstrate that it runs on the target.

## Run automated checks

From the project root, with Python 3.10 or later:

```text
python tools/gm9check.py gm9/scripts/CartVerity.gm9
python -m unittest discover -s tests -v
python tools/check_upstream.py
```

The last command needs network access and reads only the pinned official source files. To use a previously downloaded source cache, pass `--source-dir PATH`; files there use their basename, such as `scripting.c`.

The modeled runner evaluates the actual script text with fake files, hash outcomes, prompts and failures. This is useful for branch coverage and write-scope checks. It is not the real interpreter or a cartridge emulator. In particular, EOF versus I/O ambiguity, timings, card initialization and partial storage writes are subject to the documented upstream limits.

## Hardware checklist

Record results in an issue using the hardware report template. Use original cartridges and keep the cart inserted throughout each run. Never deliberately interrupt power or alter game data for testing.

| Check | Expected evidence | Initial status |
| --- | --- | --- |
| New 3DS XL, official GM9 2.2.3 | Script starts and creates a readable log | Pending |
| One known readable original NDS cart | Two digests agree; no reference gives `CONSISTENT_UNVERIFIED` | Pending |
| Full-view PC comparison | A separately dumped full standard `.nds` has the same SHA-1 as the log | Pending |
| Trustworthy matching reference | `MATCHES_SUPPLIED_REFERENCE`; record reference provenance | Pending |
| Deliberately different synthetic reference | `REFERENCE_MISMATCH`; do not alter the cartridge | Pending |
| Short/text/oversized reference file | `INVALID_OR_UNREADABLE`; hashes can still be saved | Pending |
| B at initial start prompt | No new log or script writes | Pending |
| Cancel a hash progress operation | `READ_INCOMPLETE` with the appropriate pass, if GM9 returns control | Pending |
| No cartridge; 3DS cartridge | Discovery outcome; no ROM hashing | Pending |
| Repeated runs in the same RTC second | Distinct logs; earlier logs unchanged | Pending |
| Title containing a period | Correct full filename retained | Pending |

A PC comparison of one's own dump checks agreement between methods. It is not independently a trustworthy preservation reference. Run on additional cart sizes and revisions before broadening compatibility claims. DSi-enhanced or special-storage cartridges should be reported separately.

## Updating the upstream target

Do not update only the version label. Review the command parser, `vcart.c`, `gamecart.c`, `fsutil.c`, and verification dispatch at the new commit. Regenerate the source hashes intentionally, run checks, and repeat hardware validation. Do not silently switch to a moving `master` branch.

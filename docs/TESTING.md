# Testing and release readiness

## Current evidence

- Official GodMode9 v2.2.3 source was reviewed for every used command, cartridge view construction, hash calls, and unsupported verification behavior.
- Static validation and modeled scenario tests run offline with the Python standard library.
- `tools/check_upstream.py` verifies source hashes and command signatures against `upstream-lock.json`.
- No physical console or cartridge was available during initial development.

After initial development, the user supplied photos of one New 3DS XL script
run. Both SHA-1 values agreed, no reference was supplied, and the log ended with
`CONSISTENT_UNVERIFIED` and `state=COMPLETE`. This is limited evidence for one
cartridge; the exact GodMode9 version and broader compatibility remain unverified.
It does not validate the separate native payload.

## Native dashboard

The compiled portable C core is exercised by `native/tests/test_native.py` with
real hashlib SHA-1 callbacks, changed regions, partial blocks, cancellation at
pass/block boundaries, read/initialization failures, references, metric bounds
and drawing bounds. Build it as a shared library and supply its path:

```sh
cc -shared -fPIC -O2 -std=c11 -Wall -Wextra -Werror native/source/cartverity_scan.c native/source/cartverity_ui.c native/source/cartverity_display.c -o /tmp/cartverity.so
python3 native/tests/test_native.py /tmp/cartverity.so
```

The native workflow additionally compiles and packages the ARM `.firm`. Physical
tests remain pending for native boot, both read passes, SHA-1 agreement with the
script/PC, cancellation, reference match/mismatch, rejection of unsupported carts,
rescan, log creation and power/reboot controls. Do not infer physical validation
from a host-rendered preview or a successful ARM build.

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

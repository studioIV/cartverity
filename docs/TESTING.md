# Standalone testing and hardware reports

## Database tests in alpha.4

The Python importer tests use synthetic No-Intro-shaped XML only. Native tests
consume the actual Python-generated binary in C and check lookup, exact size,
boundary records, truncation, CRC corruption and malformed fields even with a
recomputed checksum. No real No-Intro data is present in the fixtures.
Real-DAT representation agreement on a known cartridge remains a hardware check.

## Earlier release evidence

Alpha.3 passed its [native CI run](https://github.com/studioIV/cartverity/actions/runs/39075916959): compiled C host tests, ARM firmware build, packaging and active initializer save-access audit. The 11 native tests cover synthetic changes/faults, references, cancellation, settings, metrics, drawing bounds and unchanged-pixel preservation. They do not emulate a cartridge or execute firmware on a console.

The user reported native display flicker; alpha.2 introduced incremental presentation. A structured report confirming the visual improvement and exercising all native controls, references and SD cases is still needed.

A separate user-supplied legacy script log confirms one N3DS run with GodMode9 v2.2.3, equal SHA-1 values, no reference and a complete report. This does not validate native scanning or broad compatibility. [Validation records](VALIDATION.md).

## Native host checks

From the repository root, with a C compiler and Python 3.10+:

```sh
cc -shared -fPIC -O2 -std=c11 -Wall -Wextra -Werror native/source/cartverity_scan.c native/source/cartverity_ui.c native/source/cartverity_display.c native/source/cartverity_database.c -o /tmp/cartverity.so
python3 native/tests/test_native.py /tmp/cartverity.so
```

The path is a Linux/macOS example; Windows needs a suitable compiler and DLL path. The optional `native/tests/render_preview.py` requires Pillow and the upstream font and renders simulated state, not a hardware screenshot.

## Firmware integration

Follow [native build instructions](../native/README.md#build). CI compiles the actual ARM firmware, packages complete corresponding source, and preprocesses `gamecart.c` with CARTVERITY_APP enabled. The initializer audit rejects active save-probing/access calls. Do not silently change the pinned GodMode9 base.

Preparation verifies the official ZIP's SHA-256 before extraction and requires a new output directory. CI checksums the firmware, source, README, license and build-environment assets. Every firmware distribution needs its matching GPL corresponding source.

## Helper and legacy checks

```text
python tools/gm9check.py gm9/scripts/CartVerity.gm9
python -m unittest discover -s tests -v
python tools/check_upstream.py
```

The last command downloads pinned source files; `--source-dir PATH` enables an existing cache. The 103-test Python suite covers the old script model, sidecar helper and DAT importer, not native hardware. Platform permissions may skip its symlink edge case.

## Native hardware checklist

Keep cartridge and SD inserted during scanning. Do not alter cartridge data or deliberately interrupt power to simulate faults. Use [the report template](../.github/ISSUE_TEMPLATE/hardware_report.md).

| Test | Evidence to record |
| --- | --- |
| Boot alpha.3 | Exact version, console model, dashboard and by studioIV header |
| Two full passes | Native report, byte counts and both hashes |
| Separate dump comparison | Same full normalized representation; distinguish agreement from trusted provenance |
| Known-good reference | MATCHES_SUPPLIED_REFERENCE; provenance, revision and format |
| Different synthetic reference | REFERENCE_MISMATCH without modifying cartridge data |
| Auto/Require/Ignore | Missing, valid and malformed file behavior |
| Cancel | CANCELLED with progress and report if SD writes succeed |
| Absent/unsupported cart | CANNOT START; no ROM scan |
| Rescan | A returns to ready, a further A starts; previous logs preserved |
| Settings | Navigation, brightness, defaults, initial page, reset after reboot |
| Display | Refresh interval, flashing versus text/bar tearing, alpha.2+ comparison |
| Reports | Unique filename, native fields, completion meaning, path page |
| Exit | B power-off and START reboot on the main dashboard |

Include a redacted log and deviations. Do not upload ROMs, saves, keys, personal console identifiers or databases you cannot redistribute. Broaden compatibility claims only as evidence accumulates.

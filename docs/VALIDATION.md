# Validation records

## Standalone alpha.3 — 2026-10-18

Firmware revision: `28bf45c680ec2c99a965fa329aa2ef64265e6293`.
[Native CI](https://github.com/studioIV/cartverity/actions/runs/39075916959)
passed compiled C host tests (11 tests, with multiple synthetic cases), the ARM
build, packaging and active initializer save-access audit. The script/helper
matrix also passed. [Release](https://github.com/studioIV/cartverity/releases/tag/v0.2.0-alpha.3).

Native assets were downloaded and checked against their SHA-256 manifest. The
corresponding-source package included the upstream license, build files and
matching native adapter. Each release records its build environment. Docs may
advance after a binary tag; use its attached source to identify the exact build.

The user reported native UI flicker; alpha.2 introduced RAM rendering and
changed-pixel presentation. Host/build checks do not prove the visual fix on
hardware. Formal native scan/reference/control cases remain to be reported
using [TESTING.md](TESTING.md).

## Legacy hardware observation

A user-supplied ds-cart-check/1 log records script 0.1.0, GodMode9 v2.2.3,
console type N3DS, identical pass hashes, NOT_PROVIDED reference state,
CONSISTENT_UNVERIFIED and final state COMPLETE. This is one completed legacy
run, not an independent known-good comparison or native validation.

## Initial legacy local checks

Version: 0.1.0. Date: 2026-10-18.

Local environment: Windows, Python 3.11. Checks were run from the project root.

| Check | Observed result |
| --- | --- |
| `python tools/gm9check.py gm9/scripts/CartVerity.gm9` | Passed: 101 command lines and 2 labels |
| `python -m unittest discover -s tests -q` | 98 tests: 97 passed, 1 skipped |
| `python tools/check_upstream.py --source-dir <reviewed-source-cache>` | Passed: 5 source hashes and 15 command signatures |

The skipped test needs Windows symlink creation privileges. It is a desktop-helper edge-case test, not a skipped cartridge test. The full suite comprises 78 script static/scenario tests and 20 desktop-helper tests. Some tests contain multiple failure-injection cases.

The reviewed source bytes also matched their official Git blob identities at commit `0ee81b7738401b3e9f0b92b3b11159936222e542`. The initial script package did not bundle upstream firmware/source; later native releases include complete GPL corresponding source.

These initial entries record legacy local validation. Current workflow results are in [Actions](https://github.com/studioIV/cartverity/actions). Automated checks do not substitute for physical runs; see the evidence and pending native checklist above.

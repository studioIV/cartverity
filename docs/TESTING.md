# Testing

## Python reference tools

Python 3.10+, standard library only:

```sh
python -m unittest discover -s tests -v
```

The 26 tests cover sidecar creation, safe output handling and synthetic DAT
import. Windows may skip the symlink privilege edge case. Fixtures contain no
real game references. CI runs Python 3.10/3.13 on Linux and Windows.

## Native host tests

With a C compiler and Python, from the repository root:

```sh
cc -shared -fPIC -O2 -std=c11 -Wall -Wextra -Werror native/source/cartverity_scan.c native/source/cartverity_ui.c native/source/cartverity_display.c native/source/cartverity_database.c -o /tmp/cartverity.so
python3 native/tests/test_native.py /tmp/cartverity.so
```

This is a Linux/macOS path example; Windows needs a suitable compiler and DLL.
The 17 compiled-C tests cover scan faults, cancellation, hashes, reference
lookup, metrics, settings, screen bounds and unchanged-pixel presentation.
Cross-language cases load Python-generated databases in C, including missing
hashes, wrong sizes, truncation, corrupted fields and valid-CRC duplicate/unsorted
keys. The source page is exercised with maximum-length values.

## Firmware checks

Follow [build instructions](../native/README.md#build). CI builds the real ARM
payload, audits the preprocessed initializer for save-access calls, and packages
complete source and checksums. Preparation verifies the upstream ZIP's digest.
The build environment is retained inside the corresponding-source archive.
See [Actions](https://github.com/studioIV/cartverity/actions) for run results.

Host tests and build success do not certify cartridge electronics or physical UI
behavior. Real-DAT representation agreement and alpha.2+'s display improvement
need hardware confirmation. Earlier script observations are not native validation.

## Hardware report checklist

Use [the issue template](../.github/ISSUE_TEMPLATE/hardware_report.md). Keep the
cartridge and SD inserted during scans; do not alter ROM/save data or deliberately
interrupt power to simulate faults.

| Test | Evidence |
| --- | --- |
| Boot current alpha.5 | Exact version, model, dashboard and by studioIV header |
| Two complete reads | Native log, both byte counts and SHA-1 values |
| Independent comparison | Same full normalized view; source and provenance |
| Database | Compatible DAT match, missing entry stays unverified, correct source page/log |
| Sidecar | Known match and intentionally different synthetic reference |
| Policies | Auto/Require/Ignore with valid, absent and malformed sources |
| Cancel/failure | Outcome and partial progress; no false reference verdict |
| Settings | Navigation, brightness, defaults, initial page and reboot reset |
| Display | Refresh interval, full-screen flash versus text/bar tearing |
| Result layout | Outcome/reference visible, stats correct, all four detail pages legible |
| Controls | Footer badges distinct from content; physical buttons match their labels |
| Rescan/logs | A returns to ready, another A starts, unique reports preserved |
| Unsupported/no cart | CANNOT START, no scan |
| Exit | Dashboard B powers off; START reboots |

Attach a redacted native report. Do not share ROMs, saves, keys, personal console
identifiers or reference catalogs you cannot redistribute.

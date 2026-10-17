# CartVerity for GodMode9

by **studioIV**

[![Checks](https://github.com/studioIV/cartverity/actions/workflows/check.yml/badge.svg)](https://github.com/studioIV/cartverity/actions/workflows/check.yml)

Read-only Nintendo DS cartridge integrity checking on the Nintendo 3DS family, intended for a New Nintendo 3DS XL running **official GodMode9 2.2.3**. CartVerity records repeated SHA-1 checks, optional trusted-reference comparisons, and SD logs.

**Read-only scope correction:** the script issues no cartridge/save write
commands, but stock GodMode9's NDS initialization can write and restore an
EEPROM save byte while detecting capacity. A `.gm9` script cannot prevent that
internal probe. Use the **native payload** for the implementation that explicitly
bypasses save detection. This is independent of the reported matching ROM hashes.

**Script v0.1.0:** one user-reported New 3DS XL run completed both passes with matching SHA-1 values and an SD log (`CONSISTENT_UNVERIFIED`, no reference). This is limited hardware evidence, not a compatibility certification. The automated suite also exercises a simulated filesystem. See [testing](docs/TESTING.md).

**Standalone dashboard:** the experimental [native 3DS payload](native/README.md)
starts directly in a dual-screen checker, with overall/pass progress bars, read
speed, elapsed time, ETA, changed logical regions and hash/log details. It is a
custom GodMode9-based `.firm`, separate from the script. Native console testing
is still required. [Native build and tests](https://github.com/studioIV/cartverity/actions/workflows/native.yml).

The combined native firmware uses GodMode9's GPL licensing; its complete
corresponding source accompanies binary builds. See [native build and licensing](native/README.md).

Download the [CartVerity.gm9 script](https://github.com/studioIV/cartverity/releases/download/v0.1.0/CartVerity.gm9) or the [complete v0.1.0 package](https://github.com/studioIV/cartverity/releases/download/v0.1.0/cartverity-v0.1.0.zip). Release notes and checksums are on the [pre-release page](https://github.com/studioIV/cartverity/releases/tag/v0.1.0).

## What it does

- Finds the inserted cartridge's full standard `.nds` ROM view.
- Calculates SHA-1 twice and compares the results.
- Optionally compares consistent reads with a reference supplied by you.
- Saves a separate text log for every run on the SD card.

The script writes only under `0:/gm9/out/dscheck/`, apart from creating `0:/gm9/out/` if necessary. It issues no cartridge, save-memory, or NAND writes, unlock commands, repairs, or game installations. No ROM dump is saved. No ROMs or reference database are included.

**Consistent reads are not proof of correctness.** Some regions are cached by GodMode9. A trustworthy reference for the identical game revision and dump representation is needed to establish a match. This tool does not diagnose cartridge lifespan or repair hardware. See [supported limits](docs/LIMITATIONS.md).

## Install and run

1. Use [official GodMode9 2.2.3](https://github.com/d0k3/GodMode9/releases/tag/v2.2.3) on your already configured console. This project does not install custom firmware.
2. Copy `gm9/scripts/CartVerity.gm9` from this project to `/gm9/scripts/CartVerity.gm9` on the SD card.
3. Power off, insert the original Nintendo DS cartridge, then boot GodMode9 using your configured boot method.
4. Navigate to `0:/gm9/scripts/CartVerity.gm9`, press **A**, and choose **Execute GM9 Script**. Accept GodMode9's script prompt if shown, then the script's start prompt. Pressing **B** at the start cancels without writing a log.
5. Leave the cartridge inserted during both passes. Large cartridges can take several minutes per pass; keep the console powered.
6. Read the result in the log viewer. The log is saved under `/gm9/out/dscheck/` on the SD card even if you close the viewer.

Power off before exchanging cartridges and boot again for each cartridge. A reboot provides a new initialization; this script cannot force an independent cartridge initialization between passes.

The script uses the cartridge-info filename to derive the exact full `.nds` path. This preserves periods in game titles and avoids accidentally hashing `.trim.nds` or `.nds.enc`.

## Read the result

| Log result | Meaning |
| --- | --- |
| `CONSISTENT_UNVERIFIED` | Both SHA-1 calculations agree; no usable reference was compared. Check `reference_result` as well. |
| `MATCHES_SUPPLIED_REFERENCE` | Both calculations agree with your supplied reference. The tool does not authenticate its source. |
| `REFERENCE_MISMATCH` | Reads agree with each other but differ from the reference. Confirm revision, region, length and secure-area format before drawing a hardware conclusion. |
| `INCONSISTENT_READS` | The two calculated digests differ. Investigate the cartridge, contacts and reader; the result does not isolate the cause. |
| `READ_INCOMPLETE` | A hash operation failed or was cancelled. `read_result` identifies the pass. |
| `NO_DS_ROM` | No cartridge-info view was available. Check the inserted cartridge and reboot. |
| `FULL_ROM_UNAVAILABLE` | Cartridge info exists but the full standard `.nds` view does not. A 3DS cartridge also produces this result. |
| `HEADER_READ_FAILED` | Required identification bytes could not be read. |

The script's generic completion message is **not** a pass verdict. The final `result` field and `reference_result` describe the outcome. Missing final `state=COMPLETE` means the run did not reach its normal end. SD writes are not transactional; that marker is not a guarantee against storage faults.

## Optional trusted reference

Without references, installation requires only the `.gm9` file. To supply a reference, use Python 3.10 or later on your computer; no packages are required.

First note the exact `rom=` filename in a log, for example `EXAMPLE_ABCD_00.nds`. Obtain a trusted SHA-1 for the **full standard GodMode9 NDS representation**, with the same region/revision. GodMode9's standard NDS view has a decrypted secure area; trimmed or encrypted-secure-area hashes are not interchangeable.

Run the helper, replacing all example values and the SD drive letter:

```text
python tools/make_reference.py --name EXAMPLE_ABCD_00.nds --sha1 YOUR_TRUSTED_40_HEX_DIGITS --out E:/gm9/support/dscheck
```

The helper validates the filename and digest, then creates exactly 20 binary bytes at:

```text
SD:/gm9/support/dscheck/EXAMPLE_ABCD_00.nds.sha1
```

Do not save a text digest in that file. The helper refuses conflicting existing references. It cannot verify whether your digest is authoritative. Do not promote a hash from a potentially faulty cartridge to a trusted reference just because repeated reads match.

When a sidecar exists, the script reads it automatically. A malformed or unreadable sidecar is reported as `INVALID_OR_UNREADABLE`; the script still records the cartridge hashes and does not report a reference mismatch for that sidecar. If reads fail or differ, a readable reference remains `LOADED`, meaning it was not compared. See [the log format](docs/LOG_FORMAT.md).

## Development and checks

```text
python tools/gm9check.py gm9/scripts/CartVerity.gm9
python -m unittest discover -s tests -v
python tools/check_upstream.py
```

The last command downloads selected official source files at the commit recorded in `upstream-lock.json`, checks their SHA-256 digests, and checks the script's command signatures. It needs internet access. The other checks run offline. GitHub Actions runs these checks on Linux and Windows.

The scenario tests execute the actual script text in a small model of the commands it uses. They check control flow, results, reference handling, and write boundaries. They do not emulate cartridge electronics, GodMode9 timing, the complete interpreter, or a physical console.

Contributions and hardware test reports are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [hardware checklist](docs/TESTING.md). Please include the observed result and version; do not attach ROMs, save files, or personal console identifiers.

## Sources and license

Behavior was reviewed against GodMode9 **v2.2.3**, commit `0ee81b7738401b3e9f0b92b3b11159936222e542`, rather than relying on an unpinned wiki. [Source notes](docs/SOURCES.md) explain the supported commands and cartridge behavior.

This project's original files are released under the [MIT license](LICENSE). GodMode9 is a separate project under its own license; its firmware and source are not included here. This project is not affiliated with Nintendo or the GodMode9 maintainers.

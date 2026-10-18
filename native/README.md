# Build CartVerity

by **studioIV**

For installation, controls and references, use the [main README](../README.md#guides).
This directory contains the standalone app and portable C components.

## Build

Requires Python 3.10+, devkitARM and firmtool. The
[native workflow](../.github/workflows/native.yml) documents the build environment
and pinned firmtool revision. GodMode9 2.2.3 is pinned to commit
`0ee81b7738401b3e9f0b92b3b11159936222e542`.

From the repository root:

```sh
python3 tools/prepare_native.py --out build/godmode9
cd build/godmode9
make firm CARTVERITY_APP=1 VERSION=CartVerity-v0.2.0-alpha.5
```

Copy `output/GodMode9.firm` as `CartVerity-v0.2.0-alpha.5.firm`. Preparation requires a new
output directory and checks the official archive's SHA-256. `--source-zip PATH`
accepts the matching archive offline. No script-mode build is required.

The dedicated entrypoint bypasses the browser. Conditional integration removes
save-detection blocks from cartridge initialization, avoiding the EEPROM
write/restore capacity probe. CI audits the active preprocessed initializer.
The adapter uses RAM rendering and updates only changed screen pixels.
The result view replaces progress bars with the outcome, reference and final
stats; a separate footer identifies physical-button controls. It has no touch
input.

## Corresponding source and licensing

Original CartVerity code is MIT licensed. The combined GodMode9-derived firmware
is **GPL-3.0-or-later**, with component notices retained. Every binary distribution
must provide its complete matching modified source, not just this small folder.

CI packages `CartVerity-corresponding-source.zip` before compiling. It includes
the complete upstream tree, applied integration, native sources, build files,
resources, `license.txt`, CartVerity's license and build environment. Extract it
and use the same make command to rebuild with the recorded toolchain.

Reference tools are a separate MIT package; their license does not relicense
imported No-Intro data. [Data attribution](../docs/REFERENCE_SOURCES.md).

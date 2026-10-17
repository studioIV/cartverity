# CartVerity standalone: build and source

by **studioIV**

The current app is **v0.2.0-alpha.4**, built from GodMode9 2.2.3 at commit
`0ee81b7738401b3e9f0b92b3b11159936222e542` plus this directory's sources.

## User guides

Start with the [standalone tutorials](../docs/TUTORIALS.md):
[install/update](../docs/INSTALL.md), [controls/settings](../docs/USAGE.md),
[references](../docs/REFERENCES.md), [reference data sources](../docs/REFERENCE_SOURCES.md), [troubleshooting](../docs/TROUBLESHOOTING.md),
[logs](../docs/LOG_FORMAT.md) and [limits](../docs/LIMITATIONS.md).

Download the [current experimental release](https://github.com/studioIV/cartverity/releases/tag/v0.2.0-alpha.4).
The old `.gm9` script has [separate documentation](../docs/LEGACY_SCRIPT.md).
Native physical validation remains separate from build/host tests.

## Dashboard preview

![Earlier dashboard host preview with simulated scan data](dashboard-preview.png)

This is an earlier alpha.1 host rendering of the C dashboard with GodMode9's
bundled font, not a console screenshot. It predates the settings menu, revised
version footer and `by studioIV` header. Current behavior is documented above.
Upstream font/source notices are preserved in corresponding-source packages.

## Build

Requires Python 3.10+, devkitARM and firmtool. The GitHub workflow documents the
build environment. From the repository root:

```sh
python3 tools/prepare_native.py --out build/godmode9
cd build/godmode9
make firm CARTVERITY_APP=1 VERSION=CartVerity-v0.2.0-alpha.4
```

`--source-zip` allows an offline official archive; its SHA-256 must match the
pinned digest in the preparation tool. Output must be a new directory.
Copy `output/GodMode9.firm` as `CartVerity.firm`.

New CartVerity sources are MIT licensed. The **combined GodMode9-derived
firmware is GPL-3.0-or-later**, with upstream component notices retained.
Every distributed native firmware must be accompanied by its complete modified
GodMode9 source (including `license.txt`, build files, resources and CartVerity
sources). CI packages that tree **before compiling** as
`CartVerity-corresponding-source.zip`. Extract it and run the same make command
to rebuild with the documented toolchain. Do not distribute only the MIT helper
sources as corresponding source for the firmware.

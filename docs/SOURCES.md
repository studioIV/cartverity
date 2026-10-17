# Official source notes

Target: [GodMode9 v2.2.3](https://github.com/d0k3/GodMode9/releases/tag/v2.2.3), commit `0ee81b7738401b3e9f0b92b3b11159936222e542`. Reviewed 2026-10-18. Each native binary release includes complete modified corresponding source. `upstream-lock.json` separately pins selected files for legacy command checks.

## Standalone integration

- `tools/prepare_native.py` verifies the complete upstream ZIP SHA-256, adds a dedicated entrypoint and CARTVERITY_APP build flag, copies native sources, and conditionally removes the initializer's save-detection blocks.
- [card_spi.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/gamecart/card_spi.c): `_SPIIsDataMirrored` writes/restores a save byte during some EEPROM capacity probes. Native initialization must bypass it; the stock script cannot.
- [ui.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/common/ui.c) and its header define framebuffer drawing and the bundled font. The native adapter renders glyphs in RAM before incremental presentation.
- [power.h](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/common/power.h): brightness bounds and automatic setting.
- `native/source/cartverity_scan.c` implements two SHA-1 passes with callback reads and 1 MiB CRC32 comparisons. Hardware bus-status boundaries remain documented in [LIMITATIONS.md](LIMITATIONS.md).
- `.github/workflows/native.yml` records the ARM build, pinned firmtool, complete source packaging and preprocessed initializer audit. Release BUILD-ENVIRONMENT.txt records compiler/package versions.

## Legacy script interfaces

- [scripting.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/utils/scripting.c): command arities and flags; variables; conditional `not`; top-level labels/goto; `shaget --sha1`; `fget` offsets/sizes; and `dumptxt -p`. SHA-1 variable results are hex strings, while file destinations store binary digests. Text dumping appends a newline.
- [vcart.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/virtual/vcart.c): full `.nds`, `.trim.nds`, `.nds.enc`, and `.txt` info views; full-size versus trimmed-size values; ROM reads through `ReadCartBytes` and the secure-area flag. Only save views are handled by its write path. The script never calls that path.
- [gamecart.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/gamecart/gamecart.c): `GetCartName` preserves title periods; cached header and secure-area handling; ordinary NTR reads; additional DSi normalization/caching. This is why two hashes are described as two virtual-view calculations.
- [fsutil.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/filesys/fsutil.c): `FileGetData` byte-count results and `FileGetSha` read/progress behavior. Hash failure does not distinguish read failure from cancellation, and this function lacks an independent requested-versus-returned byte-count assertion.
- [gameutil.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/utils/gameutil.c): `VerifyGameFile` dispatch has no standalone NDS verification branch.
- [README](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/README.md): `C:` cartridge drive, `G:` mounted game images, and retained legacy `.gm9` support. `.gm9` is deprecated upstream but remains supported in this target release.

The script/helper source files use these interfaces. The native firmware is a separate combined GPL derivative distributed with complete corresponding source; its licensing must not be inferred from the MIT helper license alone.

# Source and attribution notes

## GodMode9

The native firmware is derived from
[GodMode9 2.2.3](https://github.com/d0k3/GodMode9/releases/tag/v2.2.3), commit
`0ee81b7738401b3e9f0b92b3b11159936222e542`.
`tools/prepare_native.py` pins the complete official ZIP's SHA-256, adds the
dedicated entrypoint/build flag and removes initialization save-probing blocks.

- [gamecart.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/gamecart/gamecart.c): cartridge initialization, full size, secure-area normalization and cached reads.
- [card_spi.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/gamecart/card_spi.c): EEPROM detection's write/restore probe, which CartVerity initialization bypasses.
- [ui.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/common/ui.c): RGB565 framebuffers, glyph drawing and font APIs.
- [power.h](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/common/power.h): brightness bounds and automatic mode.
- [sha.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/crypto/sha.c): native hardware SHA initialization, update and finalization.

Complete modified GodMode9 source and upstream notices accompany every native
release. [Build/licensing](../native/README.md) and
[CI configuration](../.github/workflows/native.yml) describe packaging and audit.

## Reference catalog

Reference metadata and hashes are user-imported from [No-Intro](https://no-intro.org/)
via [official DAT-o-MATIC](https://datomatic.no-intro.org/).
[DS DAT notes](https://wiki.no-intro.org/index.php?title=Nintendo_-_Nintendo_DS_dat_notes)
provide representation context. No real catalog or ROMs are bundled.

CartVerity's importer records source/version/original DAT SHA-256; its C reader
validates the [database format](REFERENCE_DATABASE_FORMAT.md) and looks up exact
SHA-1/size keys. Recorded provenance is not authenticated. See
[reference source details](REFERENCE_SOURCES.md) and [setup](REFERENCES.md).

CartVerity's original integration, UI, scanner and tools are by studioIV and
contributors. Upstream authors retain their copyright/license notices.

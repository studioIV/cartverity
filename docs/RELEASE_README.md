# CartVerity alpha.5

by **studioIV**

Experimental standalone Nintendo DS cartridge checker for 3DS, developed for
New 3DS XL. The app checks repeated reads and optional references; it does not
repair cartridges. Real hardware/database validation is still needed.

## Install

Copy `CartVerity.firm` to `SD:/luma/payloads/` on an already configured Luma3DS
console. Keep your existing GodMode9 payload. Power off, insert a standard DS
cartridge, then hold START at boot and choose CartVerity. Do not replace
`boot.firm` or flash NAND.

A starts; B cancels a scan. At the result X cycles details, including reference
source. Y opens session settings outside scanning. Dashboard B powers off;
START reboots. The SD reports are under `gm9/out/dscheck/`.

The result screen leads with the outcome, reference and final stats. Summary,
hashes, report and source details remain on the lower screen. Its high-contrast
footer badges label physical buttons; there is no touch input.

## References

Unzip `CartVerity-reference-tools.zip` on a PC with Python 3.10+. Obtain a full
decrypted/normalized Nintendo DS XML DAT from https://datomatic.no-intro.org/.
Run the importer with your actual paths:

```text
python tools/import_dat.py --dat "Nintendo DS Decrypted.dat" --representation full-standard-nds --out E:/gm9/support/cartverity/nds.cvdb
```

No-Intro supplies catalog data; no real DAT/database or ROMs are bundled here.
Exact SHA-1 and size are required for a database match. Missing entries remain
unverified. Recorded source metadata is not authenticated. Per-game sidecars
take priority.

## Files and source

- `CartVerity.firm`: console payload.
- `CartVerity-reference-tools.zip`: PC helpers, reference setup and attribution.
- `CartVerity-corresponding-source.zip`: complete matching GPL source, licenses,
  build files and build environment.
- `SHA256SUMS.txt`: checksums of the files above and this README.

Original CartVerity code/tools use MIT. The combined firmware is GPL-3.0-or-later
with upstream notices retained. Keep matching corresponding source when sharing
the firmware.

Guides: https://github.com/studioIV/cartverity#guides
Reference data sources: https://github.com/studioIV/cartverity/blob/main/docs/REFERENCE_SOURCES.md
Issues: https://github.com/studioIV/cartverity/issues

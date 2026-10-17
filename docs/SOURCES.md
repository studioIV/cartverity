# Official source notes

Target: [GodMode9 v2.2.3](https://github.com/d0k3/GodMode9/releases/tag/v2.2.3), commit `0ee81b7738401b3e9f0b92b3b11159936222e542`. Reviewed 2026-10-18. `upstream-lock.json` records SHA-256 values for the selected source files; they are not distributed with this project.

- [scripting.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/utils/scripting.c): command arities and flags; variables; conditional `not`; top-level labels/goto; `shaget --sha1`; `fget` offsets/sizes; and `dumptxt -p`. SHA-1 variable results are hex strings, while file destinations store binary digests. Text dumping appends a newline.
- [vcart.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/virtual/vcart.c): full `.nds`, `.trim.nds`, `.nds.enc`, and `.txt` info views; full-size versus trimmed-size values; ROM reads through `ReadCartBytes` and the secure-area flag. Only save views are handled by its write path. The script never calls that path.
- [gamecart.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/gamecart/gamecart.c): `GetCartName` preserves title periods; cached header and secure-area handling; ordinary NTR reads; additional DSi normalization/caching. This is why two hashes are described as two virtual-view calculations.
- [fsutil.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/filesys/fsutil.c): `FileGetData` byte-count results and `FileGetSha` read/progress behavior. Hash failure does not distinguish read failure from cancellation, and this function lacks an independent requested-versus-returned byte-count assertion.
- [gameutil.c](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/arm9/source/utils/gameutil.c): `VerifyGameFile` dispatch has no standalone NDS verification branch.
- [README](https://github.com/d0k3/GodMode9/blob/0ee81b7738401b3e9f0b92b3b11159936222e542/README.md): `C:` cartridge drive, `G:` mounted game images, and retained legacy `.gm9` support. `.gm9` is deprecated upstream but remains supported in this target release.

This project implements an original script and tools using those interfaces. It includes neither the upstream firmware nor copied upstream source.

# Add a reference to the standalone app

References are optional. Without one, matching reads produce
`CONSISTENT_UNVERIFIED`. With one, CartVerity can check agreement with the
supplied expected SHA-1. It cannot authenticate where that hash came from.

## Current support

The current app supports a per-game **20-byte binary SHA-1 sidecar** on the SD.
It does not import DAT files, download hashes, or search a bundled reference
database. Those features have been discussed but are not implemented.

Use a trustworthy digest for the exact region/revision and **full normalized
GodMode9 DS representation**. Its secure area is decrypted. Trimmed ROMs,
encrypted-secure-area dumps and different padding/length can have different
digests. A database entry must be checked for compatibility before use.

## Find the exact filename

1. Run a scan with **Reference: Auto** and no reference file.
2. On the result, press X until the SD report path appears.
3. Power off and open that `native_*.txt` report on your computer.
4. Find its `reference_path=` line. It specifies the exact file to create.

For example, a candidate path could be:

```text
0:/gm9/support/dscheck/YU-GI-OH!WC7_AY7PA4_00.nds.sha1
```

`0:/` means the console SD root. Preserve the exact basename and extension.
Do not derive the filename from the short title displayed on the dashboard.

## Create the reference

Download the repository source for its `tools/make_reference.py` helper. On a
computer with Python 3.10+, run the following after replacing the filename,
SHA-1 placeholder and SD drive letter with your actual values:

```text
python tools/make_reference.py --name EXAMPLE_ABCD_00.nds --sha1 YOUR_TRUSTED_40_HEX_DIGITS --out E:/gm9/support/dscheck
```

The placeholder is not a valid hash. Supply exactly 40 hexadecimal characters;
the helper converts them to 20 binary bytes. It refuses conflicting existing
files instead of overwriting them. The example output is:

```text
E:/gm9/support/dscheck/EXAMPLE_ABCD_00.nds.sha1
```

If you create the file elsewhere, copy it to that exact directory on the SD.
Do not rename a text file of 40 hexadecimal characters to `.sha1`; the app
requires 20 binary bytes. Safely eject the SD and boot CartVerity again.

## Choose a reference policy

Press **Y**, select Reference, change it with Left/Right, then B to return.

| Policy | No file | Valid 20-byte file | Invalid/unreadable file |
| --- | --- | --- | --- |
| Auto | Scan without comparison | Load and compare | Block scan |
| Require | Block scan | Load and compare | Block scan |
| Ignore | Scan without comparison | Skip file | Skip file |

The choice lasts until reboot. A loaded reference is only meaningfully compared
after both reads complete consistently; failed or differing reads take priority.

## Interpret the comparison

- **Match:** both whole-ROM SHA-1 values agree with the supplied reference.
- **Mismatch:** first confirm revision, region, full size and secure-area format.
  A mismatch alone does not establish a damaged cartridge.
- **Unverified:** no reference was compared, including when Ignore was selected.

A hash taken from your own cartridge is a **personal baseline**. It can help
detect future changes, but agreement with that same observation is not independent
proof of correctness. Never treat repeated reads alone as known-good provenance.

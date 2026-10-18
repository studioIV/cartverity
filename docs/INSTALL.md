# Install, update and remove the standalone app

## Before you start

Use a 3DS-family console already configured to boot Luma3DS payloads. Development
targets New Nintendo 3DS XL; other models require their own testing. CartVerity
does not install custom firmware. Keep your existing working GodMode9 payload.

## Install

1. Download `CartVerity.firm` from the
   [v0.2.0-alpha.4 release](https://github.com/studioIV/cartverity/releases/tag/v0.2.0-alpha.4).
   The release also contains checksums, build information, licenses and complete
   corresponding source. You only need the `.firm` on the console to scan.
2. Power off the console. Connect its SD card to your computer.
3. Create `luma/payloads` if needed and copy `CartVerity.firm` into it.
4. Safely eject the SD, put it back in the console, and insert a standard DS cart.
5. Hold **START** while powering on. Choose **CartVerity** in Luma's payload menu.
   Depending on your configuration, a single available payload may launch directly.
6. Follow [your first scan](USAGE.md#run-a-scan).

```text
SD:/
  luma/payloads/CartVerity.firm
  gm9/support/cartverity/nds.cvdb              (optional imported database)
  gm9/support/dscheck/<exact-ROM-name>.nds.sha1  (optional per-game reference)
  gm9/out/dscheck/native_*.txt                   (created by scans)
```

`SD:/` means the card's root, not a folder literally named `SD:`. On Windows it
will appear as a drive letter. Do not replace `boot.firm`, install CartVerity to
NAND, or copy this payload into `gm9/scripts`. No Lua or `.gm9` script is needed.

## Optional checksum check

Download `SHA256SUMS.txt` beside the firmware. In PowerShell, run:

```powershell
Get-FileHash -LiteralPath '.\CartVerity.firm' -Algorithm SHA256
```

Compare the full value with the `CartVerity.firm` line in the release's checksum
file. This checks agreement with the downloaded release, not cartridge integrity.

## Update

1. Power off, remove the SD and back up the old payload if you want a rollback.
2. Replace only `luma/payloads/CartVerity.firm` with the new release's file.
3. Keep existing `gm9/out/dscheck` logs, `gm9/support/dscheck` references and
   `gm9/support/cartverity/nds.cvdb` if you already imported one.
4. Boot CartVerity and check its displayed version. The header shows `by studioIV`;
   Y opens settings outside scanning.

Session settings reset when the app restarts. There is no saved settings file
to migrate. Avoid keeping several versions with similar `.firm` names unless
you label them clearly and deliberately select the intended one.

## Remove

With the console powered off, remove `luma/payloads/CartVerity.firm` from the SD.
Keep or archive logs/references as you prefer. This does not uninstall GodMode9
or Luma3DS. [Troubleshooting](TROUBLESHOOTING.md) covers boot problems.

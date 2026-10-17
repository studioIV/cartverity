# Standalone tutorials

These tutorials cover **CartVerity v0.2.0-alpha.4** and its `.firm` app.
The `.gm9` script has [separate legacy instructions](LEGACY_SCRIPT.md).

## First time

1. [Install and boot CartVerity](INSTALL.md#install).
2. [Run a two-pass scan](USAGE.md#run-a-scan).
3. [Understand the result](USAGE.md#understand-the-result).
4. [Find your saved report](LOG_FORMAT.md).

No reference is needed to check repeated-read consistency. To check agreement
with known-good data, [add a trusted reference](REFERENCES.md).

## Common tasks

| Task | Tutorial |
| --- | --- |
| Install a newer `.firm` | [Update](INSTALL.md#update) |
| Reduce visible redraws or change brightness | [Settings](USAGE.md#session-settings) |
| Require a reference before scanning | [Reference policies](REFERENCES.md#choose-a-reference-policy) |
| Create the binary reference on a computer | [Reference file](REFERENCES.md#create-the-reference) |
| Check a second cartridge | [Another scan](USAGE.md#scan-again-or-check-another-cartridge) |
| Explain a mismatch or missing reference | [Troubleshooting](TROUBLESHOOTING.md) |
| Report display or read behavior | [Hardware testing](TESTING.md) |
| Build your own payload | [Native build](../native/README.md#build) |

## Current boundaries

The app is an experimental read-only checker. It supports offline database
lookup after importing a compatible No-Intro XML DAT on a PC. It does not repair
DS cartridges, download hashes on-console or bundle real catalog data. [Reference support](REFERENCES.md) describes what is
implemented today. [Limits](LIMITATIONS.md) explains how to interpret results.

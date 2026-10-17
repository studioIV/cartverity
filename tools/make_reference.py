#!/usr/bin/env python3
"""Encode a supplied SHA-1 as a CartVerity binary reference.

This tool does not verify where the digest came from. Supply a trusted digest
for the exact full, standard GodMode9 .nds ROM view, revision and region.
Python 3.10+; standard library only. No ROM data is read or distributed.
"""

# SPDX-License-Identifier: MIT

import argparse
import os
from pathlib import Path
import re
import sys
from typing import BinaryIO, Sequence, Tuple


_SHA1_HEX = re.compile(r"[0-9a-fA-F]{40}\Z", re.ASCII)
_WINDOWS_INVALID = set('\\/:*?"<>|')
_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {
    "{}{}".format(prefix, number)
    for prefix in ("COM", "LPT")
    for number in range(1, 10)
}


def validate_rom_name(value: str) -> str:
    """Accept one safe, exact full-ROM basename, never a path or trimmed view."""
    if not isinstance(value, str) or not value or not value.isascii():
        raise ValueError("ROM name must be a nonempty ASCII basename")
    if len(value) > 31:
        raise ValueError("ROM name must be at most 31 ASCII characters")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("ROM name must not contain control characters")
    if any(char in _WINDOWS_INVALID for char in value):
        raise ValueError("ROM name must not contain paths or invalid filename characters")
    if not value.endswith(".nds") or len(value) == 4:
        raise ValueError("use the exact full ROM basename ending in lowercase .nds")
    if value.lower().endswith(".trim.nds"):
        raise ValueError("trimmed ROM names are not supported; use the full .nds view")
    if value.split(".", 1)[0].upper() in _WINDOWS_RESERVED:
        raise ValueError("ROM name must not be a reserved Windows filename")
    return value


def parse_sha1(value: str) -> bytes:
    """Decode exactly 40 ASCII hexadecimal characters to exactly 20 bytes."""
    if not isinstance(value, str) or _SHA1_HEX.fullmatch(value) is None:
        raise ValueError("SHA-1 must be exactly 40 ASCII hexadecimal characters")
    return bytes.fromhex(value)


def _write_digest(stream: BinaryIO, digest: bytes) -> None:
    """Write and flush exactly one digest to a newly created output file."""
    if stream.write(digest) != len(digest):
        raise OSError("incomplete reference write")
    stream.flush()
    os.fsync(stream.fileno())


def write_reference(out_dir: Path, name: str, digest: bytes) -> Tuple[Path, bool]:
    """Return (path, created); preserve every existing differing reference.

    An identical regular reference is an idempotent success. A symlink or any
    different existing content is refused. Exclusive creation works directly on
    FAT32/exFAT SD cards without hardlinks or replacement renames. A handled I/O
    failure removes the newly created output. A crash or power loss can leave a
    partial reference; GodMode9 rejects a reference that is not exactly 20 bytes.
    """
    validate_rom_name(name)
    if not isinstance(digest, bytes) or len(digest) != 20:
        raise ValueError("reference digest must contain exactly 20 binary bytes")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / (name + ".sha1")
    try:
        stream = target.open("xb")
    except FileExistsError:
        if target.is_symlink() or not target.is_file():
            raise FileExistsError("reference path already exists and is not a regular file") from None
        if target.read_bytes() != digest:
            raise FileExistsError(
                "reference already exists with different content; review it and "
                "remove it manually before creating a replacement"
            ) from None
        return target, False
    try:
        with stream:
            _write_digest(stream, digest)
    except BaseException:
        # Reached only after this invocation exclusively created the output;
        # the FileExistsError branch above never deletes an existing reference.
        try:
            target.unlink()
        except FileNotFoundError:
            pass
        raise
    return target, True


def _argparse_name(value: str) -> str:
    try:
        return validate_rom_name(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from None


def _argparse_sha1(value: str) -> bytes:
    try:
        return parse_sha1(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from None


def main(argv: Sequence[str] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a 20-byte reference from a supplied trusted SHA-1. "
        "This does not verify the digest's provenance or the cartridge."
    )
    parser.add_argument(
        "--name", required=True, type=_argparse_name,
        help="exact full ROM filename displayed by GodMode9, e.g. GAME_AAAA_00.nds",
    )
    parser.add_argument(
        "--sha1", required=True, type=_argparse_sha1, metavar="HEX",
        help="40 trusted hexadecimal characters for that exact full ROM view",
    )
    parser.add_argument(
        "--out", required=True, type=Path, metavar="DIRECTORY",
        help="explicit destination, e.g. E:/gm9/support/dscheck (no SD is assumed)",
    )
    args = parser.parse_args(argv)
    try:
        target, created = write_reference(args.out, args.name, args.sha1)
    except (OSError, ValueError) as error:
        print("Error: {}".format(error), file=sys.stderr)
        return 1
    print("{}: {}".format("Created" if created else "Already identical", target))
    print("Reference contains exactly 20 binary bytes.")
    print("Trust reminder: the supplied SHA-1's provenance has not been verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

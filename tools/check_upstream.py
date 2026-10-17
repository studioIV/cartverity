#!/usr/bin/env python3
"""Check pinned source hashes and the project's GM9 command signatures.

This does not execute GodMode9. No upstream files are modified or bundled.
"""
# SPDX-License-Identifier: MIT

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.request

from gm9check import COMMANDS, LONG_FLAGS


ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "upstream-lock.json"


def check_signatures(source: str) -> None:
    rows = re.findall(
        r'\{\s*CMD_ID_\w+\s*,\s*"([^"]+)"\s*,\s*(\d+)\s*,\s*([^}\n]+)\}',
        source,
    )
    registry = {
        name: (int(arity), set(re.findall(r"_FLG\('([^']+)'\)", flags)))
        for name, arity, flags in rows
    }
    for name, (arity, flags) in COMMANDS.items():
        if name not in registry:
            raise ValueError(f"Upstream command missing: {name}")
        actual_arity, actual_flags = registry[name]
        if actual_arity != arity or actual_flags != set(flags):
            raise ValueError(f"Upstream command signature differs: {name}")
    if not re.search(r"allowed_flags\|_FLG\('o'\)\|_FLG\('s'\)", source):
        raise ValueError("Universal optional/silent flags not found")
    for long_flag, short_flag in LONG_FLAGS.items():
        pattern = (
            r'strncmp\(str, "' + re.escape(long_flag)
            + r'", len\) == 0\) flag_char = '
            + re.escape(repr(short_flag))
        )
        if not re.search(pattern, source):
            raise ValueError(f"Upstream flag alias differs: {long_flag}")


def check(source_dir: Path | None = None) -> int:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    commit = lock["commit"]
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError("Lock commit must be a full SHA")
    source = None
    for entry in lock["files"]:
        path = entry["path"]
        if source_dir is not None:
            data = (source_dir / Path(path).name).read_bytes()
        else:
            url = f"https://raw.githubusercontent.com/d0k3/GodMode9/{commit}/{path}"
            request = urllib.request.Request(url, headers={"User-Agent": "ds-cart-check/0.1.0"})
            with urllib.request.urlopen(request, timeout=25) as response:
                data = response.read(2_000_001)
            if len(data) > 2_000_000:
                raise ValueError(f"Unexpected source size: {path}")
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"SHA-256 differs: {path}")
        blob = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        if hashlib.sha1(blob).hexdigest() != entry["git_blob_sha1"]:
            raise ValueError(f"Git blob identity differs: {path}")
        if path.endswith("/scripting.c"):
            source = data.decode("utf-8")
    if source is None:
        raise ValueError("Lock omits scripting.c")
    check_signatures(source)
    return len(lock["files"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, help="offline cache with source basenames")
    args = parser.parse_args(argv)
    try:
        count = check(args.source_dir)
    except (OSError, ValueError, KeyError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"PASS: {count} pinned source hashes and {len(COMMANDS)} command signatures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

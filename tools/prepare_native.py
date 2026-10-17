"""Prepare the complete, pinned GPL GodMode9 tree for the native dashboard.

Run from any directory; requires Python 3.10+. Never replaces an output folder.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "0ee81b7738401b3e9f0b92b3b11159936222e542"
URL = f"https://codeload.github.com/d0k3/GodMode9/zip/{COMMIT}"
SHA256 = "b40448ff75b2e5b8e099d1e334648dfc6b867fc66ddfebb2b4a404c27bbd4959"


def prepare(data, out):
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("Upstream archive SHA-256 mismatch")
    if out.exists():
        raise ValueError("Output must be a new directory")
    prefix = f"GodMode9-{COMMIT}"
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.infolist()
        seen = set()
        if sum(i.file_size for i in members) > 100_000_000:
            raise ValueError("Archive too large")
        for item in members:
            path = PurePosixPath(item.filename)
            if (path.is_absolute() or ".." in path.parts or "\\" in item.filename
                    or not path.parts or path.parts[0] != prefix
                    or (item.external_attr >> 16) & 0o170000 == 0o120000
                    or item.filename.casefold() in seen):
                raise ValueError("Unsafe archive member")
            seen.add(item.filename.casefold())
        out.mkdir(parents=True)
        for item in members:
            parts = PurePosixPath(item.filename).parts[1:]
            if not parts:
                continue
            target = out.joinpath(*parts)
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(item))

    # Exact anchors fail closed if the pinned upstream layout changes.
    main = out / "arm9/source/main.c"
    source = main.read_text(encoding="utf-8")
    anchor = "    #ifdef SCRIPT_RUNNER\n"
    if source.count(anchor) != 1:
        raise ValueError("Unexpected main entrypoint")
    source = '#include "cartverity_app.h"\n' + source.replace(
        anchor, "    #ifdef CARTVERITY_APP\n"
        "    if (CartVerityMain(entrypoint) == GODMODE_EXIT_REBOOT)\n"
        "    #elif defined(SCRIPT_RUNNER)\n")
    main.write_text(source, encoding="utf-8", newline="\n")
    common = out / "Makefile.common"
    with common.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write("\nifeq ($(CARTVERITY_APP),1)\n    CFLAGS += -DCARTVERITY_APP\nendif\n")
    for path in sorted((ROOT / "native/source").iterdir()):
        if path.suffix in {".c", ".h"}:
            shutil.copyfile(path, out / "arm9/source" / path.name)
    shutil.copyfile(ROOT / "LICENSE", out / "LICENSE.CartVerity")
    shutil.copyfile(ROOT / "native/README.md", out / "BUILD.CartVerity.md")
    manifest = {"godmode9_commit": COMMIT, "upstream_zip_sha256": SHA256,
                "build": "make firm CARTVERITY_APP=1 VERSION=CartVerity-v0.2.0-alpha.1",
                "files": {str(p.relative_to(out)).replace("\\", "/"):
                          hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(out.rglob("*")) if p.is_file()}}
    (out / "cartverity-source-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.source_zip:
        data = args.source_zip.read_bytes()
    else:
        with urllib.request.urlopen(URL, timeout=60) as response:
            data = response.read(20_000_001)
        if len(data) > 20_000_000:
            parser.error("Upstream download too large")
    prepare(data, args.out.resolve())
    print(f"Prepared pinned GodMode9 + CartVerity: {args.out}")


if __name__ == "__main__":
    main()

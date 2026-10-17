#!/usr/bin/env python3
"""Import a user-downloaded No-Intro Nintendo DS XML DAT for offline CartVerity.

Only metadata and hashes are read; no ROMs are needed. Provenance is recorded,
not authenticated. The caller must confirm the full normalized dump format.
"""
# SPDX-License-Identifier: MIT
import argparse
import hashlib
import os
from pathlib import Path
import re
import struct
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zlib

HEADER = 256
RECORD = 160
MAX_RECORDS = 30000
SOURCE_URL = 'https://datomatic.no-intro.org/'


def ascii_text(value, limit):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode()
    value = ' '.join(value.split())
    value = ''.join(c for c in value if 32 <= ord(c) < 127)
    if not value:
        raise ValueError('Missing printable metadata')
    return value.encode('ascii')[:limit-1].ljust(limit, b'\0')


def convert(data):
    if len(data) > 50_000_000:
        raise ValueError('DAT exceeds 50 MB')
    text = data.decode('utf-8-sig')
    if '\0' in text or re.search(r'<!ENTITY\b|<!DOCTYPE[^>]*\[', text, re.I):
        raise ValueError('XML entities/internal DTDs are not supported')
    root = ET.fromstring(text)
    if root.tag != 'datafile':
        raise ValueError('Use a Logiqx XML datafile DAT, not a ZIP or text DAT')
    name = root.findtext('header/name', '')
    version = root.findtext('header/version', '')
    author = root.findtext('header/author', '')
    if (not re.match(r'^Nintendo - Nintendo DS(?:\s|\(|$)', name)
            or re.search(r'\bEncrypted\b|Download Play|Digital', name, re.I)):
        raise ValueError('Use a full Nintendo DS DAT compatible with the decrypted standard view')
    if 'no-intro' not in author.lower() or not version.strip():
        raise ValueError('DAT must identify No-Intro as author and include its version')
    records = {}
    skipped = 0
    for game in list(root.findall('game')) + list(root.findall('machine')):
        for rom in game.findall('rom'):
            if rom.get('status', '').lower() in {'nodump', 'baddump'} or '[b]' in game.get('name', ''):
                skipped += 1
                continue
            sha1, size = rom.get('sha1', ''), rom.get('size', '')
            if not re.fullmatch(r'[0-9a-fA-F]{40}', sha1) or not size.isdecimal():
                raise ValueError('Dumped ROM entry has invalid SHA-1 or size')
            size = int(size)
            if size < 512 or size > 536870912 or size & (size-1):
                skipped += 1  # Unsupported length or a trimmed representation.
                continue
            if not rom.get('name', '').lower().endswith('.nds'):
                skipped += 1
                continue
            key = (bytes.fromhex(sha1), size)
            title = ascii_text(game.get('name') or rom.get('name'), 128)
            # Identical hashes/sizes are aliases, not conflicting expectations.
            records[key] = min(title, records.get(key, title))
            if len(records) > MAX_RECORDS:
                raise ValueError('Too many unique records (maximum 30000)')
    if not records:
        raise ValueError('DAT has no supported full-ROM SHA-1 entries')
    body = b''.join(digest + struct.pack('<I', size) + title + b'\0'*8
                    for (digest, size), title in sorted(records.items()))
    header = (b'CVDB0001' + struct.pack('<IIII', len(records), RECORD, 0, 0)
              + ascii_text('No-Intro / ' + name, 80) + ascii_text(version, 48)
              + hashlib.sha256(data).digest() + ascii_text(SOURCE_URL, 72))
    output = bytearray(header + body)
    struct.pack_into('<I', output, 16, zlib.crc32(output))
    return bytes(output), {'entries': len(records), 'skipped': skipped,
                           'dat_name': name, 'dat_version': version,
                           'dat_sha256': hashlib.sha256(data).hexdigest(), 'source': SOURCE_URL}


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        stream = path.open('xb')
    except FileExistsError:
        if not path.is_symlink() and path.is_file() and path.read_bytes() == data:
            return False
        raise FileExistsError('Output exists and differs; back it up before importing a replacement') from None
    try:
        with stream:
            if stream.write(data) != len(data):
                raise OSError('Short database write')
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dat', required=True, type=Path, help='Downloaded, extracted No-Intro XML DAT')
    parser.add_argument('--out', required=True, type=Path, help='e.g. E:/gm9/support/cartverity/nds.cvdb')
    parser.add_argument('--representation', required=True, choices=['full-standard-nds'],
                        help='Confirm the DAT hashes match full normalized/decrypted DS ROM bytes')
    args = parser.parse_args()
    try:
        with args.dat.open('rb') as stream:
            data = stream.read(50_000_001)
        database, info = convert(data)
        created = write_new(args.out, database)
    except (OSError, ValueError, ET.ParseError, UnicodeError) as error:
        parser.exit(1, f'Import failed: {error}\n')
    print(('Created: ' if created else 'Already identical: ') + str(args.out))
    for key, value in info.items():
        print(f'{key}={value}')
    print('Source attribution is recorded, not authenticated. No ROM data was read.')


if __name__ == '__main__':
    main()

"""Synthetic DAT fixtures; these are not real game references."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

spec = importlib.util.spec_from_file_location('import_dat', Path(__file__).resolve().parents[1]/'tools/import_dat.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(roms=None, name='Nintendo - Nintendo DS (Decrypted)', version='SYNTHETIC-TEST'):
    if roms is None:
        roms = '<game name="Synthetic Game (World)"><rom name="test.nds" size="512" sha1="'+'11'*20+'"/></game>'
    return ('<?xml version="1.0"?><!DOCTYPE datafile SYSTEM "https://example.invalid/logiqx.dtd">'
            '<datafile><header><name>'+name+'</name><version>'+version+
            '</version><author>No-Intro</author></header>'+roms+'</datafile>').encode()


class DatTests(unittest.TestCase):
    def test_official_export_with_contributor_authors_and_homepage(self):
        data = fixture().replace(b'<author>No-Intro</author>',
            b'<author>Contributor One, Contributor Two</author>'
            b'<homepage>No-Intro</homepage><url>https://www.no-intro.org</url>')
        _, info = module.convert(data)
        self.assertEqual(info['dat_authors'], 'Contributor One, Contributor Two')
        self.assertEqual(info['dat_url'], 'https://www.no-intro.org')
        with self.assertRaises(ValueError):
            module.convert(data.replace(b'https://www.no-intro.org', b'https://example.invalid'))

    def test_metadata_checksum_and_record(self):
        data, info = module.convert(fixture())
        self.assertEqual(data[:8], b'CVDB0001')
        self.assertEqual(len(data), 416)
        self.assertEqual(info['entries'], 1)
        self.assertEqual(data[256:276], b'\x11'*20)
        self.assertEqual(struct.unpack_from('<I', data, 276)[0], 512)
        zeroed = bytearray(data)
        checksum = struct.unpack_from('<I', data, 16)[0]
        struct.pack_into('<I', zeroed, 16, 0)
        self.assertEqual(checksum, zlib.crc32(zeroed))
        self.assertIn(b'https://datomatic.no-intro.org/', data[:256])
        self.assertEqual(info['dat_version'], 'SYNTHETIC-TEST')

    def test_bad_system_format_entities_and_missing_version(self):
        for value in (fixture(name='Nintendo - Nintendo DS (Encrypted)'),
                      fixture(name='Nintendo - Nintendo DSi'), fixture(version=''),
                      fixture().replace(b'<datafile>', b'<!ENTITY x "bad"><datafile>')):
            with self.subTest(value=value[:80]), self.assertRaises((ValueError, module.ET.ParseError)):
                module.convert(value)

    def test_sort_aliases_and_unsupported_entries(self):
        xml = ''.join('<game name="'+title+'"><rom name="test.nds" size="'+size+'" sha1="'+digest*20+'"/></game>'
                      for title, size, digest in [('Z Alias','512','22'),('A Alias','512','22'),
                                                   ('First','1024','11'),('Trimmed','513','33')])
        data, info = module.convert(fixture(xml))
        self.assertEqual((info['entries'], info['skipped']), (2,1))
        self.assertEqual(data[256:276], b'\x11'*20)
        self.assertTrue(data[256+160+24:].startswith(b'A Alias\0'))

    def test_missing_sha1_or_no_supported_records_rejected(self):
        for roms in ('', '<game><rom name="test.nds" size="512"/></game>',
                     '<game><rom name="test.nds" status="nodump"/></game>'):
            with self.assertRaises(ValueError):
                module.convert(fixture(roms))

    def test_exclusive_output_and_idempotence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'nds.cvdb'
            self.assertTrue(module.write_new(path, b'original'))
            self.assertFalse(module.write_new(path, b'original'))
            with self.assertRaises(FileExistsError):
                module.write_new(path, b'changed')
            self.assertEqual(path.read_bytes(), b'original')


if __name__ == '__main__':
    unittest.main()

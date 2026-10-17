"""Tests the compiled C implementation, with hashlib and synthetic read faults.

Usage: python native/tests/test_native.py /path/to/cartverity.so
"""
import ctypes as C
import hashlib
from pathlib import Path
import sys
import unittest
import zlib
import struct
import importlib.util

LIBRARY = C.CDLL(str(Path(sys.argv.pop(1)).resolve()))
U8 = C.c_uint8
U32 = C.c_uint32
U64 = C.c_uint64
PTR = C.POINTER(U8)


class Result(C.Structure):
    _fields_ = [('status', C.c_int), ('bytes', U32 * 2), ('complete', U8 * 2),
                ('digest', (U8 * 20) * 2), ('compared', U32), ('changed_count', U32),
                ('changed', U8 * 512)]


BEGIN = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_uint)
READ = C.CFUNCTYPE(C.c_int, C.c_void_p, U32, PTR, U32)
HBEGIN = C.CFUNCTYPE(None, C.c_void_p)
UPDATE = C.CFUNCTYPE(None, C.c_void_p, PTR, U32)
END = C.CFUNCTYPE(None, C.c_void_p, PTR)
PROGRESS = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_uint, U32, C.POINTER(Result))


class Callbacks(C.Structure):
    _fields_ = [('context', C.c_void_p), ('begin', BEGIN), ('read', READ),
                ('hash_begin', HBEGIN), ('update', UPDATE), ('end', END),
                ('progress', PROGRESS)]


class Metrics(C.Structure):
    _fields_ = [('pass_percent', C.c_uint), ('overall_percent', C.c_uint),
                ('bytes', U32), ('speed', U64), ('eta', U64), ('known', C.c_int)]


class Settings(C.Structure):
    _fields_ = [('refresh', C.c_uint), ('brightness', C.c_uint),
                ('reference', C.c_uint), ('result_page', C.c_uint)]


class View(C.Structure):
    _fields_ = [('name', C.c_char * 40), ('code', C.c_char * 5), ('revision', C.c_uint),
                ('total', U32), ('pass_number', C.c_uint), ('done', U32), ('ms', U64),
                ('stage', C.c_uint), ('page', C.c_uint), ('reference', C.c_int),
                ('saved', C.c_int), ('detail', C.c_char * 80), ('path', C.c_char * 192),
                ('result', C.POINTER(Result)), ('settings', C.POINTER(Settings)),
                ('selected_setting', C.c_uint), ('reference_database', C.c_int),
                ('reference_source', C.c_char * 80), ('reference_version', C.c_char * 48),
                ('reference_title', C.c_char * 128), ('reference_url', C.c_char * 72),
                ('reference_dat_sha256', C.c_char * 65)]


class Database(C.Structure):
    _fields_ = [('data', PTR), ('count', U32), ('source', C.c_char_p),
                ('version', C.c_char_p), ('url', C.c_char_p), ('dat_sha256', PTR)]


RECT = C.CFUNCTYPE(None, C.c_void_p, C.c_int, C.c_int, C.c_int, C.c_int, C.c_int, U32)
TEXT = C.CFUNCTYPE(None, C.c_void_p, C.c_int, C.c_int, C.c_int, U32, C.c_char_p)


class Painter(C.Structure):
    _fields_ = [('context', C.c_void_p), ('rect', RECT), ('text', TEXT)]


LIBRARY.cv_scan.argtypes = [U32, PTR, PTR, C.POINTER(Callbacks), C.POINTER(Result)]
LIBRARY.cv_crc32.argtypes = [U32, PTR, U32]
LIBRARY.cv_crc32.restype = U32
LIBRARY.cv_metrics.argtypes = [U32, C.c_uint, U32, U64]
LIBRARY.cv_metrics.restype = Metrics
LIBRARY.cv_draw.argtypes = [C.POINTER(Painter), C.POINTER(View)]
LIBRARY.cv_present.argtypes = [C.POINTER(C.c_uint16)] * 3 + [C.c_size_t, C.c_int]
LIBRARY.cv_present.restype = C.c_size_t
LIBRARY.cv_refresh_ms.argtypes = [C.POINTER(Settings)]
LIBRARY.cv_refresh_ms.restype = C.c_uint
LIBRARY.cv_brightness.argtypes = [C.POINTER(Settings)]
LIBRARY.cv_brightness.restype = C.c_int
LIBRARY.cv_setting_change.argtypes = [C.POINTER(Settings), C.c_uint, C.c_int]
LIBRARY.cv_db_validate.argtypes = [PTR, C.c_size_t, C.POINTER(Database)]
LIBRARY.cv_db_validate.restype = C.c_int
LIBRARY.cv_db_find.argtypes = [C.POINTER(Database), PTR, U32]
LIBRARY.cv_db_find.restype = C.c_char_p


def run_scan(data, second=None, reference=None, fault=None, cancel=None, fail_begin=0):
    state = {'pass': 0, 'reads': [], 'progress': []}
    def begin(_, number):
        state['pass'] = number
        return number != fail_begin
    def read(_, offset, output, size):
        state['reads'].append((state['pass'], offset, size))
        source = data if state['pass'] == 1 or second is None else second
        C.memmove(output, source[offset:offset+size], size)
        return fault(state['pass'], offset, size) if fault else size
    def hb(_):
        state['hash'] = hashlib.sha1()
    def update(_, value, size):
        state['hash'].update(C.string_at(value, size))
    def end(_, value):
        C.memmove(value, state['hash'].digest(), 20)
    def progress(_, number, done, result):
        state['progress'].append((number, done))
        return not (cancel and cancel(number, done))
    cb = Callbacks(None, BEGIN(begin), READ(read), HBEGIN(hb), UPDATE(update), END(end), PROGRESS(progress))
    out = Result()
    ref = (U8 * 20).from_buffer_copy(reference) if reference is not None else None
    LIBRARY.cv_scan(len(data), (U8 * 32768)(), ref, C.byref(cb), C.byref(out))
    return out, state


class NativeTests(unittest.TestCase):
    def test_python_imported_database_is_readable_by_c_and_exact_lookup(self):
        spec = importlib.util.spec_from_file_location('dat_tool', Path(__file__).resolve().parents[2]/'tools/import_dat.py')
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        xml = (b'<datafile><header><name>Nintendo - Nintendo DS (Decrypted)</name>'
               b'<author>No-Intro</author><version>SYNTHETIC</version></header>'
               b'<game name="Synthetic test"><rom name="test.nds" size="512" sha1="'+b'11'*20+b'"/></game>'
               b'<game name="Last record"><rom name="last.nds" size="1024" sha1="'+b'22'*20+b'"/></game></datafile>')
        data, _ = tool.convert(xml)
        buffer = (U8*len(data)).from_buffer_copy(data)
        db = Database()
        self.assertTrue(LIBRARY.cv_db_validate(buffer, len(data), C.byref(db)))
        self.assertEqual(db.count, 2)
        self.assertIn(b'No-Intro', db.source)
        digest = (U8*20).from_buffer_copy(b'\x11'*20)
        self.assertEqual(LIBRARY.cv_db_find(C.byref(db), digest, 512), b'Synthetic test')
        last = (U8*20).from_buffer_copy(b'\x22'*20)
        self.assertEqual(LIBRARY.cv_db_find(C.byref(db), last, 1024), b'Last record')
        self.assertIsNone(LIBRARY.cv_db_find(C.byref(db), digest, 1024))
        digest[0] ^= 1
        self.assertIsNone(LIBRARY.cv_db_find(C.byref(db), digest, 512))
        for length in (0, 8, 255, len(data)-1):
            self.assertFalse(LIBRARY.cv_db_validate(buffer, length, C.byref(db)))
        for offset in (0, 8, 12, 16, 24, 104, 152, 184, 256, 280, len(data)-1):
            broken = bytearray(data); broken[offset] ^= 1
            value = (U8*len(broken)).from_buffer_copy(broken)
            self.assertFalse(LIBRARY.cv_db_validate(value, len(broken), C.byref(db)))

    def test_database_rejects_semantic_corruption_even_with_valid_crc(self):
        spec = importlib.util.spec_from_file_location('dat_tool', Path(__file__).resolve().parents[2]/'tools/import_dat.py')
        tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)
        xml = (b'<datafile><header><name>Nintendo - Nintendo DS (Decrypted)</name><author>No-Intro</author>'
               b'<version>SYNTHETIC</version></header><game name="Test"><rom name="t.nds" size="512" sha1="'
               +b'11'*20+b'"/></game></datafile>')
        data, _ = tool.convert(xml)
        for offset, replacement in ((20,b'\1'), (24,b'\n'), (256+20,struct.pack('<I',513)),
                                    (256+24,b'\x01'), (256+152,b'\1')):
            broken = bytearray(data); broken[offset:offset+len(replacement)] = replacement
            struct.pack_into('<I',broken,16,0)
            struct.pack_into('<I',broken,16,zlib.crc32(broken))
            value=(U8*len(broken)).from_buffer_copy(broken)
            self.assertFalse(LIBRARY.cv_db_validate(value,len(broken),C.byref(Database())))
    def test_present_does_not_clear_or_rewrite_unchanged_pixels(self):
        target = (C.c_uint16 * 12)(*[65535]*12)
        previous = (C.c_uint16 * 12)()
        frame = (C.c_uint16 * 12)(*range(12))
        self.assertEqual(LIBRARY.cv_present(target, previous, frame, 12, 1), 12)
        self.assertEqual(list(target), list(frame))
        self.assertEqual(LIBRARY.cv_present(target, previous, frame, 12, 0), 0)
        frame[3], frame[7] = 123, 0
        # An unchanged pixel must not be touched by presentation.
        target[5] = 54321
        self.assertEqual(LIBRARY.cv_present(target, previous, frame, 12, 0), 2)
        self.assertEqual((target[3], target[7], target[5]), (123, 0, 54321))
        self.assertEqual(list(previous), list(frame))

    def test_settings_values_wrap_and_invalid_inputs(self):
        s = Settings(1, 2, 0, 0)
        self.assertEqual(LIBRARY.cv_refresh_ms(C.byref(s)), 250)
        self.assertEqual(LIBRARY.cv_brightness(C.byref(s)), 110)
        for row, count, field in ((0, 4, 'refresh'), (1, 5, 'brightness'),
                                  (2, 3, 'reference'), (3, 3, 'result_page')):
            setattr(s, field, 0)
            LIBRARY.cv_setting_change(C.byref(s), row, -1)
            self.assertEqual(getattr(s, field), count-1)
            LIBRARY.cv_setting_change(C.byref(s), row, 1)
            self.assertEqual(getattr(s, field), 0)
        s.refresh = s.brightness = 999
        self.assertEqual(LIBRARY.cv_refresh_ms(C.byref(s)), 250)
        self.assertEqual(LIBRARY.cv_brightness(C.byref(s)), 110)

    def test_crc_known_vector_and_streaming(self):
        data = b'123456789'
        crc = 0xffffffff
        for part in (data[:3], data[3:]):
            crc = LIBRARY.cv_crc32(crc, (U8 * len(part)).from_buffer_copy(part), len(part))
        self.assertEqual(crc ^ 0xffffffff, zlib.crc32(data))

    def test_complete_hashes_and_region_edges(self):
        for size in (512, 32768, 33280, 1048576, 1049088, 2097152):
            with self.subTest(size=size):
                data = (bytes(range(256)) * (size // 256))
                out, state = run_scan(data)
                self.assertEqual(out.status, 2)
                self.assertEqual(list(out.bytes), [size, size])
                self.assertEqual(list(out.complete), [1, 1])
                self.assertEqual(bytes(out.digest[0]), hashlib.sha1(data).digest())
                self.assertEqual(bytes(out.digest[1]), hashlib.sha1(data).digest())
                self.assertEqual(out.compared, (size + 1048575) // 1048576)
                self.assertEqual(out.changed_count, 0)
                self.assertEqual(sum(x[2] for x in state['reads']), size * 2)

    def test_reference_match_and_mismatch(self):
        data = b'A' * 512
        self.assertEqual(run_scan(data, reference=hashlib.sha1(data).digest())[0].status, 3)
        self.assertEqual(run_scan(data, reference=b'\x00' * 20)[0].status, 4)

    def test_changed_regions_override_matching_reference(self):
        data = b'A' * (2097152 + 512)
        other = bytearray(data)
        other[0] ^= 1
        other[-1] ^= 1
        out, _ = run_scan(data, bytes(other), hashlib.sha1(data).digest())
        self.assertEqual(out.status, 5)
        self.assertEqual(out.changed_count, 2)
        self.assertEqual(list(out.changed[:3]), [1, 0, 1])

    def test_cancel_each_pass_and_block_boundary(self):
        for number in (1, 2):
            for done in (0, 32768, 65536):
                out, state = run_scan(b'x' * 65536, cancel=lambda p, d: (p, d) == (number, done))
                self.assertEqual(out.status, 6)
                self.assertEqual(out.bytes[number-1], done)
                self.assertEqual(state['progress'][-1], (number, done))

    def test_initialization_and_read_faults(self):
        for number in (1, 2):
            self.assertEqual(run_scan(b'x' * 65536, fail_begin=number)[0].status, 7)
            for got, expected in ((-1, 7), (0, 8), (511, 8), (40000, 8)):
                out, _ = run_scan(b'x' * 65536,
                    fault=lambda p, o, n: got if p == number else n)
                self.assertEqual(out.status, expected)
                self.assertEqual(out.bytes[number-1], 0)

    def test_invalid_sizes_do_not_call_callbacks(self):
        for size in (0, 1, 513):
            out, state = run_scan(b'x' * size)
            self.assertEqual(out.status, 9)
            self.assertEqual(state['reads'], [])

    def test_metrics(self):
        m = LIBRARY.cv_metrics(1048576, 2, 524288, 3000)
        self.assertEqual((m.pass_percent, m.overall_percent, m.bytes), (50, 75, 1572864))
        self.assertEqual((m.speed, m.eta, m.known), (524288, 1, 1))
        self.assertFalse(LIBRARY.cv_metrics(1048576, 1, 0, 0).known)
        self.assertEqual(LIBRARY.cv_metrics(536870912, 2, 536870912, 1000).overall_percent, 100)
        for total, number in ((0, 1), (536870913, 1), (512, 0), (512, 3)):
            self.assertEqual(LIBRARY.cv_metrics(total, number, 512, 1000).overall_percent, 0)

    def test_dashboard_bounds_and_all_result_pages(self):
        failures = []
        def rect(_, screen, x, y, w, h, color):
            if not (screen in (0, 1) and x >= 0 and y >= 0 and w > 0 and h > 0
                    and x+w <= (400 if screen == 0 else 320) and y+h <= 240):
                failures.append(('rect', screen, x, y, w, h))
        def text(_, screen, x, y, color, value):
            if x + len(value) * 8 > (400 if screen == 0 else 320) or y+10 > 240:
                failures.append(('text', screen, x, y, value))
        paint = Painter(None, RECT(rect), TEXT(text))
        out = Result()
        view = View(name=b'YU-GI-OH! WC7', code=b'AY7P', revision=255,
                    total=536870912, pass_number=2, done=536870912, ms=3600000,
                    reference=1, saved=1, detail=b'Both reads match the supplied SHA-1.',
                    path=b'0:/gm9/out/dscheck/native_261018_010134_0000.txt', result=C.pointer(out))
        options = Settings(3, 4, 2, 2)
        view.settings = C.pointer(options)
        for stage in range(5):
            for status in range(11):
                for page in range(4):
                    view.stage, view.page, out.status = stage, page, status
                    LIBRARY.cv_draw(C.byref(paint), C.byref(view))
        self.assertEqual(failures, [])


if __name__ == '__main__':
    unittest.main()

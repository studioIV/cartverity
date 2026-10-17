"""Tests the compiled C implementation, with hashlib and synthetic read faults.

Usage: python native/tests/test_native.py /path/to/cartverity.so
"""
import ctypes as C
import hashlib
from pathlib import Path
import sys
import unittest
import zlib

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


class View(C.Structure):
    _fields_ = [('name', C.c_char * 40), ('code', C.c_char * 5), ('revision', C.c_uint),
                ('total', U32), ('pass_number', C.c_uint), ('done', U32), ('ms', U64),
                ('stage', C.c_uint), ('page', C.c_uint), ('reference', C.c_int),
                ('saved', C.c_int), ('detail', C.c_char * 80), ('path', C.c_char * 192),
                ('result', C.POINTER(Result))]


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
        for stage in range(4):
            for status in range(10):
                for page in range(3):
                    view.stage, view.page, out.status = stage, page, status
                    LIBRARY.cv_draw(C.byref(paint), C.byref(view))
        self.assertEqual(failures, [])


if __name__ == '__main__':
    unittest.main()

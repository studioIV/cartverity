"""Safety and CLI tests for the reference encoder; no game data is included."""

# SPDX-License-Identifier: MIT

import contextlib
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock


_HELPER_PATH = Path(__file__).resolve().parents[1] / "tools" / "make_reference.py"
_SPEC = importlib.util.spec_from_file_location("make_reference", _HELPER_PATH)
helper = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(helper)

# Synthetic test fixture, not a digest of any game ROM.
_DIGEST = hashlib.sha1(b"CartVerity synthetic unit-test fixture").digest()
_NAME = "GAME_AAAA_00.nds"


class ValidationTests(unittest.TestCase):
    def test_sha1_is_exact_binary(self):
        self.assertEqual(helper.parse_sha1(_DIGEST.hex()), _DIGEST)
        self.assertEqual(helper.parse_sha1(_DIGEST.hex().upper()), _DIGEST)
        self.assertEqual(len(helper.parse_sha1(_DIGEST.hex())), 20)

    def test_malformed_sha1_is_rejected(self):
        for value in (
            "", "0" * 39, "0" * 41, "g" * 40,
            " " + "0" * 40, "0" * 40 + " ", "0" * 40 + "\n",
            "0" * 19 + " " + "0" * 20, "０" * 40, None,
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                helper.parse_sha1(value)

    def test_ordinary_punctuation_and_internal_dots_are_supported(self):
        for name in (_NAME, "GAME.2_AAAA_00.nds", "A #&'()+-_AAAA_00.nds", " GAME_AAAA_00.nds"):
            with self.subTest(name=name):
                self.assertEqual(helper.validate_rom_name(name), name)

    def test_invalid_rom_names_are_rejected(self):
        for name in (
            "", None, ".nds", "../GAME.nds", "..\\GAME.nds", "C:GAME.nds",
            "dir/GAME.nds", "dir\\GAME.nds", "GAME.trim.nds", "GAME.TRIM.nds",
            "GAME.nds.enc", "GAME.NDS", "GAME.txt", "G\x00AME.nds",
            "GAME\n.nds", "GAME\x7f.nds", "GΑME.nds", "GAME?.nds", "GAME*.nds",
            "GAME<.nds", "GAME>.nds", "GAME|.nds", 'GAME".nds',
            "GAME.nds ", "CON.nds", "nul.extra.nds",
            "COM1.nds", "lpt9.nds", "X" * 28 + ".nds",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                helper.validate_rom_name(name)


class ReferenceFileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.out = self.root / "gm9" / "support" / "dscheck"

    def test_creates_exact_twenty_byte_sidecar_and_no_temp_files(self):
        path, created = helper.write_reference(self.out, _NAME, _DIGEST)
        self.assertTrue(created)
        self.assertEqual(path, self.out / (_NAME + ".sha1"))
        self.assertEqual(path.read_bytes(), _DIGEST)
        self.assertEqual(path.stat().st_size, 20)
        self.assertEqual(list(self.out.iterdir()), [path])

    def test_same_reference_is_idempotent(self):
        first, _ = helper.write_reference(self.out, _NAME, _DIGEST)
        before = first.stat().st_mtime_ns
        second, created = helper.write_reference(self.out, _NAME, _DIGEST)
        self.assertFalse(created)
        self.assertEqual(first, second)
        self.assertEqual(first.stat().st_mtime_ns, before)
        self.assertEqual(list(self.out.iterdir()), [first])

    def test_concurrent_differing_writers_do_not_replace_each_other(self):
        ready = threading.Barrier(2)
        alternate = hashlib.sha1(b"another synthetic fixture").digest()

        def create(digest):
            ready.wait(timeout=10)
            try:
                return helper.write_reference(self.out, _NAME, digest)[1]
            except FileExistsError:
                return False

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(create, (_DIGEST, alternate)))
        self.assertEqual(sorted(results), [False, True])
        target = self.out / (_NAME + ".sha1")
        self.assertIn(target.read_bytes(), (_DIGEST, alternate))
        self.assertEqual(list(self.out.iterdir()), [target])

    def test_existing_different_content_is_never_replaced(self):
        path, _ = helper.write_reference(self.out, _NAME, _DIGEST)
        for previous in (b"", b"short", b"0" * 40, bytes(20)):
            path.write_bytes(previous)
            with self.subTest(previous=previous), self.assertRaises(FileExistsError):
                helper.write_reference(self.out, _NAME, _DIGEST)
            self.assertEqual(path.read_bytes(), previous)
            self.assertEqual(list(self.out.iterdir()), [path])

    def test_incorrect_binary_size_is_rejected_before_directory_creation(self):
        for digest in (b"", b"a" * 19, b"a" * 21, _DIGEST.hex(), bytearray(_DIGEST)):
            with self.subTest(digest=digest), self.assertRaises(ValueError):
                helper.write_reference(self.out, _NAME, digest)
        self.assertFalse(self.out.exists())

    def test_destination_directory_failure(self):
        self.out.parent.mkdir(parents=True)
        self.out.write_bytes(b"existing file")
        with self.assertRaises(OSError):
            helper.write_reference(self.out, _NAME, _DIGEST)
        self.assertEqual(self.out.read_bytes(), b"existing file")

    def test_exclusive_create_failure_preserves_other_files(self):
        self.out.mkdir(parents=True)
        other = self.out / "other.sha1"
        other.write_bytes(b"preserve")
        with mock.patch.object(Path, "open", side_effect=PermissionError("read-only SD")):
            with self.assertRaises(OSError):
                helper.write_reference(self.out, _NAME, _DIGEST)
        self.assertEqual(list(self.out.iterdir()), [other])
        self.assertEqual(other.read_bytes(), b"preserve")

    def test_partial_write_failure_removes_only_new_reference(self):
        self.out.mkdir(parents=True)
        other = self.out / "other.sha1"
        other.write_bytes(b"preserve")

        def partial_failure(stream, digest):
            stream.write(digest[:7])
            stream.flush()
            raise OSError("SD removed during write")

        with mock.patch.object(helper, "_write_digest", side_effect=partial_failure):
            with self.assertRaises(OSError):
                helper.write_reference(self.out, _NAME, _DIGEST)
        self.assertEqual(list(self.out.iterdir()), [other])
        self.assertEqual(other.read_bytes(), b"preserve")

    def test_partial_reference_from_interrupted_process_is_preserved(self):
        self.out.mkdir(parents=True)
        target = self.out / (_NAME + ".sha1")
        target.write_bytes(_DIGEST[:7])
        with self.assertRaises(FileExistsError):
            helper.write_reference(self.out, _NAME, _DIGEST)
        self.assertEqual(target.read_bytes(), _DIGEST[:7])

    def test_flush_failure_leaves_no_reference_or_temp_file(self):
        with mock.patch.object(helper.os, "fsync", side_effect=OSError("I/O failure")):
            with self.assertRaises(OSError):
                helper.write_reference(self.out, _NAME, _DIGEST)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_creation_requires_no_hardlinks_or_rename_support(self):
        with mock.patch.object(helper.os, "link", side_effect=OSError("unsupported")):
            with mock.patch.object(helper.os, "rename", side_effect=OSError("unsupported")):
                path, created = helper.write_reference(self.out, _NAME, _DIGEST)
        self.assertTrue(created)
        self.assertEqual(path.read_bytes(), _DIGEST)

    def test_symlink_is_refused_when_available(self):
        self.out.mkdir(parents=True)
        original = self.root / "original"
        original.write_bytes(_DIGEST)
        target = self.out / (_NAME + ".sha1")
        try:
            target.symlink_to(original)
        except (OSError, NotImplementedError):
            self.skipTest("creating symlinks is unavailable for this account/filesystem")
        with self.assertRaises(FileExistsError):
            helper.write_reference(self.out, _NAME, _DIGEST)
        self.assertEqual(original.read_bytes(), _DIGEST)
        self.assertTrue(target.is_symlink())


class CommandLineTests(unittest.TestCase):
    def test_main_success_and_idempotent_result(self):
        with tempfile.TemporaryDirectory() as directory:
            argv = ["--name", _NAME, "--sha1", _DIGEST.hex(), "--out", directory]
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(helper.main(argv), 0)
                self.assertEqual(helper.main(argv), 0)
            self.assertIn("Created:", output.getvalue())
            self.assertIn("Already identical:", output.getvalue())
            self.assertIn("provenance has not been verified", output.getvalue())

    def test_main_conflict_returns_one_and_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / (_NAME + ".sha1")
            target.write_bytes(b"existing reference")
            errors = io.StringIO()
            with contextlib.redirect_stderr(errors):
                code = helper.main([
                    "--name", _NAME, "--sha1", _DIGEST.hex(), "--out", directory
                ])
            self.assertEqual(code, 1)
            self.assertIn("different content", errors.getvalue())
            self.assertEqual(target.read_bytes(), b"existing reference")

    def test_argparse_rejects_bad_arguments(self):
        for argv in (
            [], ["--name", _NAME, "--sha1", _DIGEST.hex()],
            ["--name", "../bad.nds", "--sha1", _DIGEST.hex(), "--out", "unused"],
            ["--name", _NAME, "--sha1", "bad", "--out", "unused"],
        ):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as result:
                    helper.main(argv)
                self.assertEqual(result.exception.code, 2)

    def test_real_cli_exit_codes_and_output(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [
                sys.executable, str(_HELPER_PATH), "--name", _NAME,
                "--sha1", _DIGEST.hex(), "--out", directory,
            ]
            success = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertIn("Created:", success.stdout)
            self.assertEqual((Path(directory) / (_NAME + ".sha1")).read_bytes(), _DIGEST)
            malformed = subprocess.run(
                [sys.executable, str(_HELPER_PATH), "--sha1", "bad"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(malformed.returncode, 2)
            (Path(directory) / (_NAME + ".sha1")).write_bytes(b"different")
            conflict = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(conflict.returncode, 1)
            self.assertIn("different content", conflict.stderr)


if __name__ == "__main__":
    unittest.main()

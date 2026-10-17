"""Exercise the shipped script using a limited, test-only GM9 command model.

These tests do not invoke GodMode9 or demonstrate physical cartridge integrity.
They cover project syntax, write scope, branches and modeled command failures.
"""

import hashlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from gm9check import (CheckError, DEFAULT_SCRIPT, FakeFS, ModelRunner, OUTPUT_DIR,
                      Program, decode, parse_command, tokens)


ROM_STEM = "TEST_GAME_ABCD_00"
ROM = "C:/" + ROM_STEM + ".nds"
REFERENCE = "0:/gm9/support/dscheck/" + ROM_STEM + ".nds.sha1"
DATA = bytearray((i % 256 for i in range(0x400)))
DATA[0x0C:0x10] = b"ABCD"
DATA[0x1E] = 2
DATA = bytes(DATA)
DIGEST = hashlib.sha1(DATA).hexdigest().upper()
OTHER_DIGEST = "A" * 40 if DIGEST != "A" * 40 else "B" * 40


def fixture(stem=ROM_STEM):
    return FakeFS(files={"C:/" + stem + ".nds": DATA,
                         "C:/" + stem + ".trim.nds": DATA[:0x200],
                         "C:/" + stem + ".txt": b"Synthetic cartridge info\n"})


def log_fields(run):
    path = run.variables.get("LOG")
    if path is None or path not in run.fs.files:
        return {}
    result = {}
    for line in run.fs.files[path].decode("ascii").splitlines():
        if "=" in line:
            name, value = line.split("=", 1)
            result[name] = value
    return result


class ScriptModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = Program.from_path()

    def run_script(self, fs=None, **kwargs):
        result = ModelRunner(self.program, fs if fs is not None else fixture(), **kwargs).run()
        # Every modeled write must remain on SD in the exact log subtree.
        for command, path in result.fs.writes:
            if command == "mkdir":
                self.assertIn(path, {"0:/gm9/out", OUTPUT_DIR})
            else:
                self.assertTrue(path.startswith(OUTPUT_DIR + "/"), path)
        return result

    def assert_finished(self, run, outcome):
        self.assertTrue(run.succeeded, run.failed_command)
        self.assertEqual(log_fields(run)["state"], "COMPLETE")
        self.assertEqual(log_fields(run)["result"], outcome)
        lines = run.fs.files[run.variables["LOG"]].splitlines()
        self.assertEqual(lines[-1], b"state=COMPLETE")

    def test_stable_without_reference_is_unverified(self):
        run = self.run_script()
        self.assert_finished(run, "CONSISTENT_UNVERIFIED")
        fields = log_fields(run)
        self.assertEqual(fields["read_result"], "CONSISTENT")
        self.assertEqual(fields["reference_result"], "NOT_PROVIDED")
        self.assertEqual(fields["sha1_pass1"], DIGEST)
        self.assertEqual(fields["sha1_pass2"], DIGEST)
        self.assertEqual(fields["rom"], ROM)
        self.assertEqual(bytes.fromhex(fields["game_code_hex"]), b"ABCD")
        self.assertEqual(fields["revision_hex"], "02")

    def test_matching_binary_reference(self):
        fs = fixture()
        fs.files[REFERENCE] = bytes.fromhex(DIGEST)
        run = self.run_script(fs)
        self.assert_finished(run, "MATCHES_SUPPLIED_REFERENCE")
        self.assertEqual(log_fields(run)["reference_result"], "MATCH")

    def test_lowercase_fget_reference_matches_uppercase_shaget(self):
        fs = fixture()
        fs.files[REFERENCE] = bytes.fromhex(DIGEST)
        run = self.run_script(fs)
        self.assert_finished(run, "MATCHES_SUPPLIED_REFERENCE")
        self.assertEqual(run.variables["EXPECTED"], DIGEST.lower())
        self.assertEqual(run.variables["HASH1"], DIGEST.upper())
        self.assertNotEqual(run.variables["EXPECTED"], run.variables["HASH1"])

    def test_chk_case_insensitive_and_unequal_flag(self):
        runner = ModelRunner(self.program)
        self.assertTrue(runner.execute(parse_command(tokens('chk "aBc" "AbC"'))))
        self.assertFalse(runner.execute(parse_command(tokens('chk -u "aBc" "AbC"'))))
        self.assertTrue(runner.execute(parse_command(tokens('chk -u "aBc" "AbD"'))))

    def test_mismatched_binary_reference(self):
        fs = fixture()
        fs.files[REFERENCE] = bytes.fromhex(OTHER_DIGEST)
        run = self.run_script(fs)
        self.assert_finished(run, "REFERENCE_MISMATCH")
        self.assertEqual(log_fields(run)["reference_result"], "MISMATCH")

    def test_empty_reference_invalid(self):
        fs = fixture()
        fs.files[REFERENCE] = b""
        run = self.run_script(fs)
        self.assert_finished(run, "CONSISTENT_UNVERIFIED")
        self.assertEqual(log_fields(run)["reference_result"], "INVALID_OR_UNREADABLE")

    def test_short_reference_invalid(self):
        fs = fixture()
        fs.files[REFERENCE] = bytes.fromhex(DIGEST)[:-1]
        run = self.run_script(fs)
        self.assert_finished(run, "CONSISTENT_UNVERIFIED")
        self.assertEqual(log_fields(run)["reference_result"], "INVALID_OR_UNREADABLE")

    def test_extra_byte_reference_invalid(self):
        fs = fixture()
        fs.files[REFERENCE] = bytes.fromhex(DIGEST) + b"\0"
        run = self.run_script(fs)
        self.assert_finished(run, "CONSISTENT_UNVERIFIED")
        self.assertEqual(log_fields(run)["reference_result"], "INVALID_OR_UNREADABLE")
        self.assertNotIn("reference_sha1", log_fields(run))

    def test_ascii_hex_reference_invalid(self):
        fs = fixture()
        fs.files[REFERENCE] = DIGEST.encode("ascii")
        run = self.run_script(fs)
        self.assert_finished(run, "CONSISTENT_UNVERIFIED")
        self.assertEqual(log_fields(run)["reference_result"], "INVALID_OR_UNREADABLE")

    def test_reference_initial_read_error_invalid(self):
        fs = fixture()
        fs.files[REFERENCE] = bytes.fromhex(DIGEST)
        run = self.run_script(fs, failures={("fget", 3): "fail"})
        self.assert_finished(run, "CONSISTENT_UNVERIFIED")
        self.assertEqual(log_fields(run)["reference_result"], "INVALID_OR_UNREADABLE")

    def test_reference_probe_error_cannot_be_distinguished_from_eof(self):
        # This test records a supported limitation, not a successful size check:
        # GM9 fget returns false both for EOF and for an SD read failure. A file
        # with extra bytes may therefore appear loaded if the extra-byte probe
        # fails. The helper checks exact length on PC; the script cannot prove it.
        fs = fixture()
        fs.files[REFERENCE] = bytes.fromhex(DIGEST) + b"extra"
        run = self.run_script(fs, failures={("fget", 4): "fail"})
        self.assert_finished(run, "MATCHES_SUPPLIED_REFERENCE")
        self.assertEqual(log_fields(run)["reference_result"], "MATCH")

    def test_no_cart(self):
        run = self.run_script(FakeFS())
        self.assert_finished(run, "NO_DS_ROM")
        self.assertEqual(run.calls["shaget"], 0)

    def test_trimmed_view_alone_not_hashed(self):
        fs = fixture()
        del fs.files[ROM]
        run = self.run_script(fs)
        self.assert_finished(run, "FULL_ROM_UNAVAILABLE")
        self.assertEqual(run.calls["shaget"], 0)

    def test_dotted_cart_title_selects_full_rom(self):
        stem = "MY.GAME_AAAA_00"
        fs = fixture(stem)
        run = self.run_script(fs)
        self.assert_finished(run, "CONSISTENT_UNVERIFIED")
        self.assertEqual(log_fields(run)["rom"], "C:/" + stem + ".nds")

    def test_at_sign_cart_title_hashes_full_rom_with_explicit_offset(self):
        # GM9 treats the last '@' as a byte-range delimiter for shaget. The
        # explicit @0 suffix preserves earlier '@' characters in cart titles.
        run = self.run_script(fixture("NAME@HERE_ABCD_00"))
        self.assert_finished(run, "CONSISTENT_UNVERIFIED")
        self.assertEqual(log_fields(run)["sha1_pass1"], DIGEST)
        self.assertEqual(log_fields(run)["sha1_pass2"], DIGEST)

    def test_no_cartinfo_fails_closed(self):
        fs = fixture()
        del fs.files["C:/" + ROM_STEM + ".txt"]
        run = self.run_script(fs)
        self.assert_finished(run, "NO_DS_ROM")
        self.assertEqual(run.calls["shaget"], 0)

    def test_non_ds_cartinfo_cannot_select_nds(self):
        fs = FakeFS(files={"C:/3DS_TITLE.txt": b"info", "C:/3DS_TITLE.3ds": DATA})
        run = self.run_script(fs)
        self.assert_finished(run, "FULL_ROM_UNAVAILABLE")
        self.assertEqual(run.calls["shaget"], 0)

    def test_first_header_read_failure(self):
        run = self.run_script(failures={("fget", 1): "fail"})
        self.assert_finished(run, "HEADER_READ_FAILED")
        self.assertEqual(run.calls["shaget"], 0)

    def test_revision_read_failure(self):
        run = self.run_script(failures={("fget", 2): "fail"})
        self.assert_finished(run, "HEADER_READ_FAILED")
        self.assertEqual(run.calls["shaget"], 0)

    def test_first_hash_failure_or_cancel(self):
        run = self.run_script(hashes=[None])
        self.assert_finished(run, "READ_INCOMPLETE")
        self.assertEqual(log_fields(run)["read_result"], "PASS1_FAILED_OR_CANCELLED")
        self.assertNotIn("sha1_pass1", log_fields(run))
        self.assertNotIn("sha1_pass2", log_fields(run))

    def test_second_hash_failure_or_cancel(self):
        run = self.run_script(hashes=[DIGEST, None])
        self.assert_finished(run, "READ_INCOMPLETE")
        self.assertEqual(log_fields(run)["read_result"], "PASS2_FAILED_OR_CANCELLED")
        self.assertEqual(log_fields(run)["sha1_pass1"], DIGEST)
        self.assertNotIn("sha1_pass2", log_fields(run))

    def test_inconsistent_hashes(self):
        run = self.run_script(hashes=[DIGEST, OTHER_DIGEST])
        self.assert_finished(run, "INCONSISTENT_READS")
        self.assertEqual(log_fields(run)["read_result"], "INCONSISTENT")

    def test_inconsistent_hashes_take_priority_over_reference(self):
        fs = fixture()
        fs.files[REFERENCE] = bytes.fromhex(DIGEST)
        run = self.run_script(fs, hashes=[DIGEST, OTHER_DIGEST])
        self.assert_finished(run, "INCONSISTENT_READS")
        self.assertEqual(log_fields(run)["reference_result"], "LOADED")

    def test_cancel_start_creates_nothing(self):
        fs = fixture()
        original = dict(fs.files)
        run = self.run_script(fs, answers=[False])
        self.assertTrue(run.succeeded)
        self.assertEqual(fs.writes, [])
        self.assertEqual(fs.files, original)
        self.assertNotIn("LOG", run.variables)

    def test_existing_log_is_preserved(self):
        fs = fixture()
        old_log = OUTPUT_DIR + "/261018_120000_0000.txt"
        fs.files[old_log] = b"existing data\n"
        run = self.run_script(fs)
        self.assert_finished(run, "CONSISTENT_UNVERIFIED")
        self.assertNotEqual(run.variables["LOG"], old_log)
        self.assertEqual(fs.files[old_log], b"existing data\n")

    def test_existing_directories_are_reused(self):
        fs = fixture()
        fs.directories |= {"0:/gm9/out", OUTPUT_DIR}
        run = self.run_script(fs)
        self.assert_finished(run, "CONSISTENT_UNVERIFIED")
        self.assertEqual(run.calls["mkdir"], 0)

    def test_directory_creation_failure_stops_without_hashing(self):
        run = self.run_script(failures={("mkdir", 1): "fail"})
        self.assertFalse(run.succeeded)
        self.assertEqual(run.failed_command, "mkdir")
        self.assertEqual(run.calls["shaget"], 0)
        self.assertNotIn("LOG", run.variables)

    def test_unique_path_failure_stops_without_hashing(self):
        run = self.run_script(failures={("findnot", 1): "fail"})
        self.assertFalse(run.succeeded)
        self.assertEqual(run.calls["shaget"], 0)
        self.assertNotIn("LOG", run.variables)

    def test_first_log_write_failure_stops_without_hashing(self):
        run = self.run_script(failures={("dumptxt", 1): "fail"})
        self.assertFalse(run.succeeded)
        self.assertEqual(run.failed_command, "dumptxt")
        self.assertEqual(run.calls["shaget"], 0)

    def test_sd_write_failure_keeps_incomplete_marker(self):
        run = self.run_script(failures={("dumptxt", 5): "fail"})
        self.assertFalse(run.succeeded)
        self.assertEqual(log_fields(run)["state"], "INCOMPLETE")
        self.assertNotIn("result", log_fields(run))
        self.assertEqual(run.calls["shaget"], 0)

    def test_partial_final_write_does_not_produce_complete_marker(self):
        baseline = self.run_script()
        run = self.run_script(failures={("dumptxt", baseline.calls["dumptxt"]): "partial"})
        self.assertFalse(run.succeeded)
        self.assertNotEqual(log_fields(run).get("state"), "COMPLETE")
        self.assertEqual(log_fields(run)["result"], "CONSISTENT_UNVERIFIED")

    def test_every_log_write_failure_stops_execution(self):
        baseline = self.run_script()
        count = baseline.calls["dumptxt"]
        for occurrence in range(1, count + 1):
            with self.subTest(log_write=occurrence):
                run = self.run_script(failures={("dumptxt", occurrence): "fail"})
                self.assertFalse(run.succeeded)
                self.assertEqual(run.failed_command, "dumptxt")
                self.assertEqual(run.calls["dumptxt"], occurrence)
                self.assertNotEqual(log_fields(run).get("state"), "COMPLETE")

    def test_every_partial_log_write_stops_execution(self):
        baseline = self.run_script()
        count = baseline.calls["dumptxt"]
        for occurrence in range(1, count + 1):
            with self.subTest(log_write=occurrence):
                run = self.run_script(failures={("dumptxt", occurrence): "partial"})
                self.assertFalse(run.succeeded)
                self.assertEqual(run.failed_command, "dumptxt")
                self.assertEqual(run.calls["dumptxt"], occurrence)
                self.assertNotEqual(log_fields(run).get("state"), "COMPLETE")

    def test_final_marker_is_not_an_atomic_sd_transaction(self):
        # Upstream dumptxt writes the text, then separately writes a newline.
        # A failed second write leaves COMPLETE bytes despite command failure.
        # Never interpret marker presence as a proof of successful SD flushes.
        baseline = self.run_script()
        run = self.run_script(failures={("dumptxt", baseline.calls["dumptxt"]): "newline"})
        self.assertFalse(run.succeeded)
        self.assertEqual(log_fields(run)["state"], "COMPLETE")
        self.assertFalse(run.fs.files[run.variables["LOG"]].endswith(b"\n"))

    def test_viewer_failure_is_optional_after_completed_log(self):
        run = self.run_script(failures={("textview", 1): "fail"})
        self.assert_finished(run, "CONSISTENT_UNVERIFIED")

    def test_source_cart_and_reference_bytes_never_change(self):
        fs = fixture()
        fs.files[REFERENCE] = bytes.fromhex(DIGEST)
        original = dict(fs.files)
        run = self.run_script(fs)
        self.assert_finished(run, "MATCHES_SUPPLIED_REFERENCE")
        for path, value in original.items():
            self.assertEqual(fs.files[path], value, path)


class StaticChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = DEFAULT_SCRIPT.read_bytes()

    def reject(self, old, new):
        self.assertIn(old, self.source)
        with self.assertRaises(CheckError):
            Program.from_bytes(self.source.replace(old, new, 1))

    def test_shipped_script_passes(self):
        self.assertGreater(len(Program.from_bytes(self.source).lines), 100)

    def test_wrong_arity_rejected(self):
        self.reject(b"set EXPECTED \"\"", b"set EXPECTED")

    def test_unknown_command_rejected(self):
        self.reject(b"set EXPECTED \"\"", b"fset C:/game.nds@0:1 FF")

    def test_unsupported_flag_rejected(self):
        self.reject(b"shaget --sha1", b"shaget -w")

    def test_combined_short_flags_rejected(self):
        self.reject(b"textview -o -s", b"textview -os")

    def test_unknown_long_flag_rejected(self):
        self.reject(b"shaget --sha1", b"shaget --sha256")

    def test_missing_hash_algorithm_rejected(self):
        self.reject(b"shaget --sha1", b"shaget")

    def test_hash_file_destination_rejected(self):
        self.reject(b"$[ROM]@0 HASH1", b"$[ROM]@0 C:/written.sha1")

    def test_missing_explicit_hash_offset_rejected(self):
        self.reject(b"$[ROM]@0 HASH1", b"$[ROM] HASH1")

    def test_partial_rom_hash_range_rejected(self):
        self.reject(b"$[ROM]@0 HASH1", b"$[ROM]@0:100 HASH1")

    def test_cart_log_write_rejected(self):
        self.reject(b"dumptxt $[LOG]", b"dumptxt C:/written.txt")

    def test_nand_log_write_rejected(self):
        self.reject(b"dumptxt $[LOG]", b"dumptxt 1:/written.txt")

    def test_cart_mkdir_rejected(self):
        self.reject(b"mkdir 0:/gm9/out\n", b"mkdir C:/bad\n")

    def test_reassignment_of_log_rejected(self):
        self.reject(b"set EXPECTED \"\"", b"set LOG C:/bad")

    def test_nonunique_log_pattern_rejected(self):
        self.reject(b"$[STARTED]_????.txt LOG", b"$[STARTED].txt LOG")

    def test_log_path_traversal_rejected(self):
        self.reject(b"findnot 0:/gm9/out/dscheck/", b"findnot 0:/gm9/out/dscheck/../")

    def test_reassignment_of_timestamp_rejected(self):
        self.reject(b"set EXPECTED \"\"", b"set DATESTAMP EVIL")

    def test_wrong_started_expression_rejected(self):
        self.reject(b"set STARTED \"$[DATESTAMP]_$[TIMESTAMP]\"", b"set STARTED ../../bad")

    def test_unclosed_quotes_rejected(self):
        self.reject(b"set EXPECTED \"\"", b"set EXPECTED \"oops")

    def test_missing_end_rejected(self):
        self.reject(b"end\n", b"# end removed\n")

    def test_extra_end_rejected(self):
        self.reject(b"@done\n", b"@done\nend\n")

    def test_unknown_label_rejected(self):
        self.reject(b"goto done", b"goto absent")

    def test_at_sign_in_goto_argument_rejected(self):
        self.reject(b"goto done", b"goto @done")

    def test_duplicate_label_rejected(self):
        self.reject(b"@done\n", b"@done\n@done\n")

    def test_label_inside_conditional_rejected(self):
        self.reject(b"set SUCCESSMSG \"Cancelled before starting.\"", b"@badlabel")

    def test_control_flow_in_condition_rejected(self):
        self.reject(b"if not ask", b"if not goto")

    def test_undefined_variable_rejected(self):
        self.reject(b"set ROM $[BASE].nds", b"set ROM $[UNDEFINED].nds")

    def test_unclosed_variable_reference_rejected(self):
        self.reject(b"set ROM $[BASE].nds", b"set ROM $[BASE.nds")

    def test_overlong_variable_name_rejected(self):
        self.reject(b"set EXPECTED \"\"", b"set " + b"A" * 32 + b" \"\"")

    def test_overlong_literal_variable_value_rejected(self):
        self.reject(b"set EXPECTED \"\"", b"set EXPECTED \"" + b"x" * 256 + b"\"")

    def test_overlong_literal_argument_rejected(self):
        self.reject(b"set EXPECTED \"\"", b"echo \"" + b"x" * 512 + b"\"")

    def test_overlong_known_expansion_rejected(self):
        self.reject(b"set EXPECTED \"\"", b"set EXPECTED \"" + b"$[DATESTAMP]" * 43 + b"\"")

    def test_fget_missing_size_rejected(self):
        self.reject(b"$[ROM]@C:4 GAMECODE", b"$[ROM]@C GAMECODE")

    def test_fget_too_large_rejected(self):
        self.reject(b"$[ROM]@C:4 GAMECODE", b"$[ROM]@C:80 GAMECODE")

    def test_bom_rejected(self):
        with self.assertRaises(CheckError):
            Program.from_bytes(b"\xef\xbb\xbf" + self.source)

    def test_control_character_rejected(self):
        with self.assertRaises(CheckError):
            Program.from_bytes(self.source + b"# NUL:\0\n")

    def test_missing_final_newline_rejected(self):
        with self.assertRaises(CheckError):
            Program.from_bytes(self.source.rstrip(b"\r\n"))

    def test_crlf_accepted(self):
        Program.from_bytes(self.source.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))

    def test_bare_carriage_return_rejected(self):
        with self.assertRaises(CheckError):
            Program.from_bytes(self.source.replace(b"\n", b"\r", 1))

    def test_quoted_hash_is_text_and_unquoted_hash_is_comment(self):
        parts = tokens('echo "# hello" # trailing comment')
        self.assertEqual(parse_command(parts).args, ("# hello",))

    def test_unsupported_escape_rejected(self):
        self.reject(b"set EXPECTED \"\"", b'set EXPECTED "\\t"')

    def test_escape_decoder_consumes_only_one_escape(self):
        self.assertEqual(decode(r"line\nquote\""), 'line\nquote"')
        self.assertEqual(decode(r"\\n"), r"\\n")


if __name__ == "__main__":
    unittest.main()

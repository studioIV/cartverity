#!/usr/bin/env python3
"""Conservative static checks and a test-only model for CartVerity.gm9.

This is NOT GodMode9's parser, interpreter, a hardware emulator, or a ROM
validator. It intentionally accepts only this project's small command subset.
Arity/flag and modeled command semantics were checked against upstream
GodMode9 v2.2.3 arm9/source/utils/scripting.c. The model does not reproduce
FatFs, wildcard allocation order, cartridge caches, timing, UI, or physical I/O.
Unrecognized syntax/commands fail rather than silently doing nothing.

Run: python tools/gm9check.py [path/to/script.gm9]
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import re
from collections import Counter, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


DEFAULT_SCRIPT = Path(__file__).resolve().parents[1] / "gm9/scripts/CartVerity.gm9"
OUTPUT_DIR = "0:/gm9/out/dscheck"
LOG_PATTERN = OUTPUT_DIR + "/$[STARTED]_????.txt"
# Global optional/silent flags are permitted by get_cmd_id for every command.
# Keep this subset small: e.g. shaget to a file and fset are intentionally absent.
COMMANDS = {
    "set": (2, ""), "ask": (1, ""), "echo": (1, ""),
    "find": (2, "f"), "strsplit": (3, "bf"), "chk": (2, "u"),
    "exist": (1, ""), "isdir": (1, ""), "mkdir": (1, ""),
    "findnot": (2, ""), "fget": (2, "e"), "shaget": (2, "1"),
    "dumptxt": (2, "p"), "goto": (1, ""), "textview": (1, ""),
}
LONG_FLAGS = {
    "--sha1": "1", "--before": "b", "--first": "f",
    "--unequal": "u", "--flip_endian": "e", "--append": "p",
    "--optional": "o", "--silent": "s",
}
BUILTINS = {"NULL", "CURRDIR", "GM9OUT", "HAX", "ONTYPE", "RDTYPE",
            "GYROMODEL", "GM9VER", "DATESTAMP", "TIMESTAMP", "SERIAL",
            "REGION", "EMUID0", "SYSID0", "EMUBASE", "SDSIZE", "SDFREE",
            "NANDSIZE"}
VAR_RE = re.compile(r"\$\[([^\]]*)\]")
NAME_RE = re.compile(r"[A-Z][A-Z0-9_]{0,30}\Z")


class CheckError(ValueError):
    """A construct is invalid or outside the deliberately supported subset."""


@dataclass(frozen=True)
class Token:
    value: str
    quoted: bool = False


@dataclass(frozen=True)
class Command:
    name: str
    args: tuple[str, ...] = ()
    flags: frozenset[str] = frozenset()
    condition: Optional["Command"] = None


@dataclass(frozen=True)
class Line:
    number: int
    command: Optional[Command] = None
    label: Optional[str] = None


def tokens(text: str) -> list[Token]:
    """Match this script's GM9 quoting/comment rules, not shell quoting."""
    result = []
    pos = 0
    while pos < len(text):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos == len(text) or text[pos] == "#":
            break
        if text[pos] == '"':
            start = pos = pos + 1
            while pos < len(text) and not (text[pos] == '"' and text[pos - 1] != "\\"):
                pos += 1
            if pos == len(text):
                raise CheckError("unclosed double quote")
            result.append(Token(text[start:pos], True))
            pos += 1
            if pos < len(text) and not text[pos].isspace():
                raise CheckError("quoted token must end at whitespace")
        else:
            start = pos
            while pos < len(text) and not text[pos].isspace():
                pos += 1
            result.append(Token(text[start:pos]))
    return result


def parse_command(parts: list[Token], condition: bool = False) -> Command:
    if not parts or parts[0].quoted:
        raise CheckError("missing or quoted command")
    name = parts[0].value
    if name in {"if", "not"}:
        if name == "if" and condition:
            raise CheckError("control flow inside condition")
        return Command(name, condition=parse_command(parts[1:], True))
    if name in {"else", "end"}:
        if condition or len(parts) != 1:
            raise CheckError("invalid block delimiter")
        return Command(name)
    if name not in COMMANDS:
        raise CheckError(f"unsupported command: {name}")
    if condition and name == "goto":
        raise CheckError("control flow inside condition")
    flags, args = set(), []
    for part in parts[1:]:
        if part.value.startswith("-") and not part.quoted:
            flag = LONG_FLAGS.get(part.value)
            if flag is None and len(part.value) == 2:
                flag = part.value[1]
            if flag is None or flag not in COMMANDS[name][1] + "os":
                raise CheckError(f"unsupported flag for {name}: {part.value}")
            flags.add(flag)
        else:
            args.append(part.value)
    if len(args) != COMMANDS[name][0]:
        raise CheckError(f"{name} expects {COMMANDS[name][0]} arguments, got {len(args)}")
    return Command(name, tuple(args), frozenset(flags))


def decode(value: str) -> str:
    # expand_arg consumes one escape at a time. Unknown escapes retain the
    # backslash. Do not use unicode_escape, shell parsing, or recursive escapes.
    output = []
    pos = 0
    while pos < len(value):
        char = value[pos]
        pos += 1
        if char == "\\" and pos < len(value):
            escaped = value[pos]
            pos += 1
            output.append("\n" if escaped == "n" else '"' if escaped == '"' else "\\" + escaped)
        else:
            output.append(char)
    return "".join(output)


def variable_name(name: str) -> None:
    # GM9 permits more characters; this repository intentionally uses this set.
    if not NAME_RE.fullmatch(name):
        raise CheckError(f"invalid or overlong project variable name: {name!r}")


def flattened(command: Command):
    yield command
    if command.condition:
        yield from flattened(command.condition)


@dataclass
class Program:
    lines: list[Line]
    labels: dict[str, int] = field(default_factory=dict)
    branches: dict[int, int] = field(default_factory=dict)
    ends: dict[int, int] = field(default_factory=dict)

    @classmethod
    def from_path(cls, path: Path = DEFAULT_SCRIPT) -> "Program":
        return cls.from_bytes(path.read_bytes())

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Program":
        try:
            text = raw.decode("ascii")
        except UnicodeDecodeError as exc:
            raise CheckError("project script must be ASCII without BOM") from exc
        if not text.endswith("\n"):
            raise CheckError("script must end with a newline")
        if re.search(r"\r(?!\n)", text) or any(ord(c) < 32 and c not in "\r\n\t" for c in text):
            raise CheckError("illegal control character or bare carriage return")
        lines = []
        for number, textline in enumerate(text.splitlines(), 1):
            try:
                parts = tokens(textline)
                if not parts:
                    lines.append(Line(number))
                elif parts[0].value.startswith("@"):
                    if len(parts) != 1 or parts[0].quoted:
                        raise CheckError("label must be alone on its line")
                    label = parts[0].value[1:]
                    if not re.fullmatch(r"[a-z][a-z0-9_]*", label):
                        raise CheckError("invalid project label")
                    lines.append(Line(number, label=label))
                else:
                    lines.append(Line(number, command=parse_command(parts)))
            except CheckError as exc:
                raise CheckError(f"line {number}: {exc}") from exc
        program = cls(lines)
        program.validate()
        return program

    def validate(self) -> None:
        stack = []
        variables, references, assignments = set(), set(), {}
        # Known length bounds. Dynamic cart path sizes remain runtime-checked by
        # GM9's 255-byte variable / 511-byte argument limits, not proven here.
        lengths = {"DATESTAMP": 6, "TIMESTAMP": 6, "GM9VER": 31, "ONTYPE": 4}
        goto_targets = []
        for index, line in enumerate(self.lines):
            try:
                if line.label is not None:
                    if stack:
                        raise CheckError("labels inside conditional blocks cannot be goto targets")
                    if line.label in self.labels:
                        raise CheckError(f"duplicate label: {line.label}")
                    self.labels[line.label] = index
                command = line.command
                if not command:
                    continue
                if command.name == "if":
                    stack.append([index, None])
                elif command.name == "else":
                    if not stack or stack[-1][1] is not None:
                        raise CheckError("else without one unmatched if")
                    stack[-1][1] = index
                elif command.name == "end":
                    if not stack:
                        raise CheckError("end without if")
                    start, otherwise = stack.pop()
                    self.branches[start] = otherwise + 1 if otherwise is not None else index + 1
                    if otherwise is not None:
                        self.ends[otherwise] = index + 1
                for cmd in flattened(command):
                    for arg in cmd.args:
                        if re.search(r'\\(?![n"])', arg):
                            raise CheckError("project arguments support only newline and quote escapes")
                        if len(decode(arg)) > 511:
                            raise CheckError("literal argument exceeds GM9's 511-byte maximum")
                        for match in VAR_RE.finditer(arg):
                            variable_name(match[1])
                            references.add(match[1])
                        if "$[" in VAR_RE.sub("", arg):
                            raise CheckError("unclosed variable expansion")
                        refs = VAR_RE.findall(arg)
                        if all(v in lengths for v in refs):
                            bound = len(decode(VAR_RE.sub("", arg))) + sum(lengths[v] for v in refs)
                            if bound > 511:
                                raise CheckError("expanded argument exceeds GM9's 511-byte maximum")
                    dest = None
                    if cmd.name in {"set", "strsplit"}:
                        dest = cmd.args[0]
                    elif cmd.name in {"find", "findnot", "fget", "shaget"}:
                        dest = cmd.args[1]
                    if dest is not None:
                        variable_name(dest)
                        if dest in BUILTINS:
                            raise CheckError(f"builtin must not be assigned: {dest}")
                        variables.add(dest)
                        assignments.setdefault(dest, []).append(cmd)
                        if cmd.name == "set":
                            val = cmd.args[1]
                            refs = VAR_RE.findall(val)
                            if all(v in lengths for v in refs):
                                bound = len(decode(VAR_RE.sub("", val))) + sum(lengths[v] for v in refs)
                                if bound > 255:
                                    raise CheckError("set content exceeds GM9's 255-byte maximum")
                                lengths[dest] = max(bound, lengths.get(dest, 0))
                            else:
                                lengths.pop(dest, None)
                        elif cmd.name == "shaget":
                            if "1" not in cmd.flags:
                                raise CheckError("project shaget must explicitly select SHA-1")
                            if cmd.args[0] != "$[ROM]@0":
                                raise CheckError("project shaget must hash the complete ROM using explicit @0")
                            lengths[dest] = 40
                        elif cmd.name == "fget":
                            match = re.search(r"@[0-9A-Fa-f]+:([0-9A-Fa-f]+)\Z", cmd.args[0])
                            if not match or not 1 <= int(match[1], 16) <= 127:
                                raise CheckError("fget requires an explicit 1..127-byte hexadecimal slice")
                            lengths[dest] = int(match[1], 16) * 2
                        else:
                            lengths.pop(dest, None)
                    if cmd.name == "mkdir" and cmd.args[0] not in {"0:/gm9/out", OUTPUT_DIR}:
                        raise CheckError("mkdir outside allowed SD output directories")
                    if cmd.name == "dumptxt" and cmd.args[0] != "$[LOG]":
                        raise CheckError("dumptxt must target the protected LOG variable")
                    if cmd.name == "findnot" and cmd.args != (LOG_PATTERN, "LOG"):
                        raise CheckError("findnot must use the approved unique log pattern")
                    if cmd.name == "goto":
                        goto_targets.append(cmd.args[0])
            except CheckError as exc:
                raise CheckError(f"line {line.number}: {exc}") from exc
        if stack:
            raise CheckError("unclosed if block")
        for target in goto_targets:
            if target not in self.labels:
                raise CheckError(f"unknown goto target: {target!r} (omit @ in goto arguments)")
        if references - variables - BUILTINS:
            raise CheckError("undefined variables: " + ", ".join(sorted(references - variables - BUILTINS)))
        if len(variables | BUILTINS) > 256:
            raise CheckError("GM9 variable table exceeded")
        log_assignments = assignments.get("LOG", [])
        if len(log_assignments) != 1 or log_assignments[0].name != "findnot":
            raise CheckError("LOG must be assigned exactly once by approved findnot")
        started = assignments.get("STARTED", [])
        if len(started) != 1 or started[0].name != "set" or started[0].args[1] != "$[DATESTAMP]_$[TIMESTAMP]":
            raise CheckError("STARTED must be assigned only from the fixed timestamp expression")


@dataclass
class FakeFS:
    """In-memory fixture; failure injection does not reproduce actual FatFs."""
    files: dict[str, bytes] = field(default_factory=dict)
    directories: set[str] = field(default_factory=lambda: {"0:", "0:/gm9", "C:"})
    writes: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class RunResult:
    succeeded: bool
    variables: dict[str, str]
    fs: FakeFS
    messages: list[str]
    calls: Counter
    failed_command: Optional[str] = None


class ModelRunner:
    """Small test-only command model. Never use this to execute arbitrary GM9.

    failures maps (command, 1-based occurrence) to 'fail', 'partial', or 'newline'.
    A partial dumptxt appends half the text before failing; 'newline' writes the
    text but fails its separate newline write, exposing the non-atomic marker.
    Hash overrides (hex string or None for fail/cancel) model outcomes without
    pretending to reproduce card reads. None cannot distinguish cancel/error.
    """

    def __init__(self, program: Program, fs: Optional[FakeFS] = None, *,
                 answers=(True,), hashes=(), failures=None):
        self.program, self.fs = program, fs if fs is not None else FakeFS()
        self.answers, self.hashes = deque(answers), deque(hashes)
        self.failures = failures or {}
        if any(mode not in {"fail", "partial", "newline"} for mode in self.failures.values()):
            raise CheckError("unknown modeled failure mode")
        self.variables = {"NULL": "", "DATESTAMP": "261018", "TIMESTAMP": "120000",
                          "GM9VER": "2.2.3", "ONTYPE": "N3DS"}
        self.calls, self.messages = Counter(), []
        self.jump = None

    def expand(self, arg: str) -> str:
        value = VAR_RE.sub(lambda m: self.variables.get(m[1], ""), decode(arg))
        if len(value) > 511:
            raise CheckError("modeled expanded argument exceeds GM9 buffer")
        return value

    def assign(self, name: str, value: str) -> bool:
        if len(value) > 255:
            return False
        self.variables[name] = value
        return True

    def run(self, max_steps: int = 10000) -> RunResult:
        pc = steps = 0
        while pc < len(self.program.lines):
            steps += 1
            if steps > max_steps:
                raise CheckError("modeled step limit exceeded")
            line = self.program.lines[pc]
            cmd = line.command
            if cmd is None:
                pc += 1
                continue
            if cmd.name == "if":
                pc = pc + 1 if self.execute(cmd.condition) else self.program.branches[pc]
                continue
            if cmd.name == "else":
                pc = self.program.ends[pc]
                continue
            if cmd.name == "end":
                pc += 1
                continue
            ok = self.execute(cmd)
            if not ok and "o" not in cmd.flags:
                return RunResult(False, self.variables, self.fs, self.messages, self.calls, cmd.name)
            if self.jump is not None:
                pc, self.jump = self.jump, None
            else:
                pc += 1
        return RunResult(True, self.variables, self.fs, self.messages, self.calls)

    def execute(self, cmd: Command) -> bool:
        if cmd.name == "not":
            return not self.execute(cmd.condition)
        name = cmd.name
        if name not in COMMANDS:
            raise CheckError(f"unmodeled command: {name}")
        args = tuple(self.expand(arg) for arg in cmd.args)
        self.calls[name] += 1
        failure = self.failures.get((name, self.calls[name]))
        if failure and not (name == "dumptxt" and failure in {"partial", "newline"}):
            return False
        if name == "set":
            return self.assign(*args)
        if name == "ask":
            if not self.answers:
                raise CheckError("no modeled answer for ask")
            return self.answers.popleft()
        if name == "echo":
            self.messages.append(args[0])
            return True
        if name == "chk":
            # Upstream strncasecmp compares at most _VAR_CNT_LEN (256) bytes.
            # Fixture strings are ASCII, so lower() matches the C comparison.
            equal = args[0][:256].lower() == args[1][:256].lower()
            return not equal if "u" in cmd.flags else equal
        if name == "strsplit":
            dest, value, separator = args
            if len(separator) != 1 or separator not in value:
                return False
            pos = value.find(separator) if "f" in cmd.flags else value.rfind(separator)
            return self.assign(dest, value[:pos] if "b" in cmd.flags else value[pos + 1:])
        if name == "find":
            matches = sorted((path for path in self.fs.files if fnmatch.fnmatchcase(path.lower(), args[0].lower())), key=str.lower)
            if not matches:
                return False
            return self.assign(args[1], matches[0] if "f" in cmd.flags else matches[-1])
        if name == "findnot":
            # Allocation choice is simplified; only uniqueness is under test.
            if args[0].rsplit("/", 1)[0] not in self.fs.directories:
                return False
            for value in range(0x10000):
                path = args[0].replace("????", f"{value:04X}")
                if path not in self.fs.files and path not in self.fs.directories:
                    return self.assign(args[1], path)
            return False
        if name == "exist":
            return args[0] in self.fs.files or args[0] in self.fs.directories
        if name == "isdir":
            return args[0] in self.fs.directories
        if name == "mkdir":
            path = args[0]
            if path.rsplit("/", 1)[0] not in self.fs.directories:
                return False
            self.fs.directories.add(path)
            self.fs.writes.append((name, path))
            return True
        if name in {"fget", "shaget"}:
            path, _, spec = args[0].rpartition("@")
            if not path:
                path, spec = args[0], ""
            offset = size = 0
            if spec:
                # run_cmd uses sscanf on the text following the last '@'. A
                # title containing '@' is therefore truncated even when the
                # suffix is not a range; invalid offset parsing falls back to 0.
                match = re.match(r"([0-9A-Fa-f]+)(?::([0-9A-Fa-f]+))?", spec)
                if match:
                    offset = int(match[1], 16)
                    size = int(match[2], 16) if match[2] else 0
            if path not in self.fs.files:
                return False
            data = self.fs.files[path]
            if name == "fget":
                if size <= 0 or len(data[offset:offset + size]) != size:
                    return False
                content = data[offset:offset + size]
                if "e" in cmd.flags:
                    content = content[::-1]
                # hexntostr emits lowercase; shaget formats uppercase. chk is
                # case-insensitive, which is essential for reference matches.
                return self.assign(args[1], content.hex())
            if self.hashes:
                digest = self.hashes.popleft()
                if digest is None:
                    return False
            else:
                digest = hashlib.sha1(data[offset:offset + size] if size else data[offset:]).hexdigest().upper()
            if not re.fullmatch(r"[0-9A-Fa-f]{40}", digest):
                raise CheckError("modeled SHA-1 override must contain 40 hex digits")
            return self.assign(args[1], digest.upper())
        if name == "dumptxt":
            path, text = args
            if not path.startswith(OUTPUT_DIR + "/") or "/../" in path:
                raise CheckError("modeled write escaped output directory")
            if path.rsplit("/", 1)[0] not in self.fs.directories:
                return False
            previous = self.fs.files.get(path, b"") if "p" in cmd.flags else b""
            encoded = text.encode("ascii")
            self.fs.writes.append((name, path))
            if failure == "partial":
                self.fs.files[path] = previous + encoded[:max(1, len(encoded) // 2)]
                return False
            if failure == "newline":
                self.fs.files[path] = previous + encoded
                return False
            self.fs.files[path] = previous + encoded + b"\n"
            return True
        if name == "goto":
            self.jump = self.program.labels[args[0]]
            return True
        if name == "textview":
            return args[0] in self.fs.files
        raise CheckError(f"unmodeled command: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", nargs="?", type=Path, default=DEFAULT_SCRIPT)
    args = parser.parse_args()
    try:
        program = Program.from_path(args.script)
    except (OSError, CheckError) as exc:
        parser.exit(1, f"Static subset check failed: {exc}\n")
    count = sum(line.command is not None for line in program.lines)
    print(f"Static project-subset checks passed: {count} command lines, {len(program.labels)} labels.")
    print("This is not the real GM9 parser or a hardware test; run the unittest suite separately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

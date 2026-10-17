"""Fail CI if active native InitCartRead includes save probing/access calls."""
from pathlib import Path
import re
import sys

text = Path(sys.argv[1]).read_text()
match = re.search(r'\bInitCartRead\s*\([^;{}]*\)\s*\{', text)
if not match:
    raise SystemExit('Missing preprocessed initializer definition')
depth = 1
end = match.end()
while depth and end < len(text):
    depth += (text[end] == '{') - (text[end] == '}')
    end += 1
body = text[match.end():end-1]
if depth or 'NTR_Secure_Init' not in body:
    raise SystemExit('Unexpected native initializer body')
for forbidden in ('CardSPI', 'ReadCartSave', 'WriteCartSave'):
    if forbidden in body:
        raise SystemExit('Native initializer retains save access: ' + forbidden)
print('PASS: active native cartridge initializer has no save probing/access calls')

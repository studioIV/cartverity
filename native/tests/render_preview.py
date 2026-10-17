"""Render actual cv_draw calls with the upstream font; synthetic scan state.

python native/tests/render_preview.py library font_default.frf output.png
Requires Pillow, only for this optional host preview.
"""
import struct
import sys
from pathlib import Path
from PIL import Image, ImageDraw

font_path, output = map(Path, sys.argv[2:4])
import test_native as api  # Loads the shared C library from argv[1].

data = font_path.read_bytes()
chunks = {}
offset = 8
while offset < len(data):
    tag, size = struct.unpack_from('<4sI', data, offset)
    chunks[tag] = data[offset+8:offset+8+size]
    offset += 8 + size
width, height, count = struct.unpack('<BBH', chunks[b'META'])
mapping = struct.unpack('<' + 'H'*count, chunks[b'CMAP'])
glyphs = dict(zip(mapping, (chunks[b'CDAT'][i*height:(i+1)*height] for i in range(count))))
screens = [Image.new('RGB', (400, 240)), Image.new('RGB', (320, 240))]


def rgb(color):
    return ((color >> 11 & 31)*255//31, (color >> 5 & 63)*255//63, (color & 31)*255//31)


def rect(_, screen, x, y, w, h, color):
    ImageDraw.Draw(screens[screen]).rectangle((x, y, x+w-1, y+h-1), fill=rgb(color))


def text(_, screen, x, y, color, value):
    for char in value.decode('ascii'):
        for yy, row in enumerate(glyphs[ord(char)]):
            for xx in range(width):
                if row & (1 << (7 - xx)):
                    screens[screen].putpixel((x+xx, y+yy), rgb(color))
        x += width


result = api.Result(status=1, compared=43)
view = api.View(name=b'YU-GI-OH! WC7', code=b'AY7P', revision=0,
    total=67108864, pass_number=2, done=46137344, ms=76000, stage=1,
    detail=b'Two full read passes.', result=api.C.pointer(result))
painter = api.Painter(None, api.RECT(rect), api.TEXT(text))
api.LIBRARY.cv_draw(api.C.byref(painter), api.C.byref(view))
canvas = Image.new('RGB', (440, 540), (5, 9, 16))
canvas.paste(screens[0], (20, 12))
canvas.paste(screens[1], (60, 272))
ImageDraw.Draw(canvas).text((20, 522), 'HOST PREVIEW / SIMULATED SCAN DATA', fill=(145, 164, 187))
output.parent.mkdir(parents=True, exist_ok=True)
canvas.resize((880, 1080), Image.Resampling.NEAREST).save(output)
print(output)

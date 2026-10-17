"""Rebuild font.ttf: Noto Sans TC subset to the characters used in main.py.

    pip install fonttools
    curl -L -o NotoSansTC.ttf "https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf"
    python tools/make_font.py NotoSansTC.ttf
"""
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
EXTRA = "　，。、：；！？「」『』（）…—・·×÷±→←↑↓★☆▲▼◆■□●○%"

src = (ROOT / "main.py").read_text(encoding="utf-8")
chars = set(src) | set(map(chr, range(0x20, 0x7F))) | set(EXTRA)
text = "".join(c for c in chars if ord(c) >= 0x20)

font = instancer.instantiateVariableFont(TTFont(sys.argv[1]), {"wght": 500})
opts = subset.Options()
opts.layout_features = ["*"]
opts.name_IDs = ["*"]
opts.notdef_outline = True
sub = subset.Subsetter(opts)
sub.populate(text=text)
sub.subset(font)
font.save(ROOT / "font.ttf")
print("font.ttf rebuilt with %d characters" % len(text))

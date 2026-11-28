#!/usr/bin/env python3
"""Checks that the French and Spanish legal pages still line up with the English ones.

Run from the repo root:  python3 tools/legal/check.py
The English privacy and terms pages are the base. /fr/ and /es/ carry the same parts in the same order. When a
line changes in English, change the same line in French and Spanish (the legal check passes the words first),
then run this. It compares, part by part: the page structure, the count of bold spots, and every number.
It cannot read the words: a pass here is not a word check.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PART = re.compile(r"<(h1|h2|p|li)((?: [^>]*)?)>(.*?)</\1>", re.S)


def main_of(path):
    s = (ROOT / path).read_text(encoding="utf-8")
    return s[s.index("<main"):s.index("</main>")]


def frame(m):
    """The tags that hold the page together, without links, bold, line breaks or language marks."""
    m = re.sub(r"<(/?)(span|a|strong|br)\b[^>]*>", "", m)
    return [re.sub(r' (lang|hreflang|aria-current|href)="[^"]*"', "", t) for t in re.findall(r"</?[a-z0-9]+(?: [^>]*)?>", m)]


def numbers(inner):
    text = re.sub(r"<[^>]+>", "", inner).replace(",", "")
    text = re.sub(r"(?<=\d)[ \u00a0\u202f](?=\d{3}\b)", "", text)   # "25 000" is 25000
    return sorted(re.findall(r"\d+(?:\.\d+)*", text))


bad = 0
for page in ("privacy", "terms"):
    en = main_of(f"{page}/index.html")
    en_parts = [m.group(3) for m in PART.finditer(en) if "langs" not in m.group(2)]
    for lang in ("fr", "es"):
        tr = main_of(f"{lang}/{page}/index.html")
        tr_parts = [m.group(3) for m in PART.finditer(tr) if "langs" not in m.group(2)]
        problems = []
        if frame(en) != frame(tr):
            problems.append("page structure differs")
        if len(en_parts) != len(tr_parts):
            problems.append(f"{len(en_parts)} parts in English, {len(tr_parts)} here")
        for n, (a, b) in enumerate(zip(en_parts, tr_parts)):
            if a.count("<strong>") != b.count("<strong>"):
                problems.append(f"part {n}: bold spots differ")
            if numbers(a) != numbers(b):
                problems.append(f"part {n}: numbers differ {numbers(a)} / {numbers(b)}")
        print(f"/{lang}/{page}/:", "lines up with English" if not problems else "; ".join(problems[:8]))
        bad += len(problems)
sys.exit(1 if bad else 0)

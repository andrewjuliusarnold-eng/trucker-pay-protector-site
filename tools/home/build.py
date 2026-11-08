#!/usr/bin/env python3
"""Builds the home page in every language from template.html and the <lang>.json word files.

Run from the repo root:  python3 tools/home/build.py
Writes index.html (English) and es/, pa/, ru/, ar/ index.html. Change words in the .json files, not the .html.
"""
import html, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
LANGS = ["en", "es", "pa", "ru", "ar"]
PLAY_URL = "https://play.google.com/store/apps/details?id=com.truckerpayprotector.app"
ACCOUNT_URL = "https://account.truckerpayprotector.com/"

PLAY_ICON = ('<svg aria-hidden="true" width="26" height="28" viewBox="0 0 26 28"><path d="M1 1l14 13L1 27z" fill="#34A853"/>'
             '<path d="M1 1l18 10-4 3z" fill="#4285F4"/><path d="M1 27l18-10-4-3z" fill="#EA4335"/>'
             '<path d="M19 11l5 3-5 3-4-3z" fill="#FBBC04"/></svg>')


def path_for(code):
    return "/" if code == "en" else f"/{code}/"


def build(code, all_words):
    w = all_words[code]
    t = (HERE / "template.html").read_text(encoding="utf-8")
    e = lambda s: html.escape(s, quote=True)
    rep = {k: e(v) for k, v in w.items() if isinstance(v, str)}
    rep["path"] = path_for(code)
    rep["home"] = path_for(code)
    rep["account_url"] = ACCOUNT_URL
    rep["hreflang"] = "\n".join(
        f'<link rel="alternate" hreflang="{c}" href="https://truckerpayprotector.com{path_for(c)}">' for c in LANGS
    ) + '\n<link rel="alternate" hreflang="x-default" href="https://truckerpayprotector.com/">'
    rep["lang_links"] = "".join(
        f'<li><a href="{path_for(c)}" lang="{c}" hreflang="{c}"'
        + (' aria-current="page"' if c == code else "")
        + f'>{e(all_words[c]["lang_name"])}</a></li>'
        for c in LANGS
    )
    rep["play_badge"] = (f'<a class="play" href="{PLAY_URL}" aria-label="{e(w["play_alt"])}">{PLAY_ICON}'
                         f'<span lang="en" dir="ltr"><small>{e(w["play_small"])}</small><b>Google Play</b></span></a>')
    rep["chips"] = "".join(f"<li>{e(c)}</li>" for c in w["chips"])
    # FAQ answers may hold the two site links; those are written by us, so they are not escaped.
    rep["faq"] = "".join(f"<details><summary>{e(q)}</summary><p>{a}</p></details>" for q, a in w["faq"])
    rep["legal_note_html"] = f"<p>{e(w['legal_note'])}</p>" if w.get("legal_note") else ""
    for k, v in rep.items():
        t = t.replace("{{" + k + "}}", v)
    assert "{{" not in t, [line for line in t.splitlines() if "{{" in line][:3]
    out = ROOT / ("index.html" if code == "en" else f"{code}/index.html")
    out.parent.mkdir(exist_ok=True)
    out.write_text(t, encoding="utf-8")
    return out


if __name__ == "__main__":
    words = {c: json.loads((HERE / f"{c}.json").read_text(encoding="utf-8")) for c in LANGS}
    keys = set(words["en"])
    for c in LANGS:
        missing = keys - set(words[c])
        assert not missing, (c, sorted(missing))
    for c in LANGS:
        print("wrote", build(c, words).relative_to(ROOT))

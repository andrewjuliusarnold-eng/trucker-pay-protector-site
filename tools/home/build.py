#!/usr/bin/env python3
"""Builds the home page in every language from template.html and the <lang>.json word files.

Run from the repo root:  python3 tools/home/build.py
Writes index.html (English) and es/, pa/, ru/, ar/ index.html. Change words in the .json files, not the .html.

The use case video: the "See it work" part is left out of a language's page until that language has its own
video file, assets/video/use-case-<lang>.mp4, and its still picture, assets/video/use-case-<lang>.jpg. The words
are burned into the video, so each language needs its own file. No file, no video part, no empty box.
The video starts muted; the player's own sound button turns the sound on. When the final video exists, set the
length in each language's "video_note" line to the real length before adding the file.
"""
import html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
LANGS = ["en", "es", "pa", "ru", "ar"]
PLAY_URL = "https://play.google.com/store/apps/details?id=com.truckerpayprotector.app"
ACCOUNT_URL = "https://account.truckerpayprotector.com/"
SITE = "https://truckerpayprotector.com"
# The language tag share previews use (Open Graph "locale").
OG_LOCALE = {"en": "en_US", "es": "es_US", "pa": "pa_IN", "ru": "ru_RU", "ar": "ar_AR"}

PLAY_ICON = ('<svg aria-hidden="true" width="26" height="28" viewBox="0 0 26 28"><path d="M1 1l14 13L1 27z" fill="#34A853"/>'
             '<path d="M1 1l18 10-4 3z" fill="#4285F4"/><path d="M1 27l18-10-4-3z" fill="#EA4335"/>'
             '<path d="M19 11l5 3-5 3-4-3z" fill="#FBBC04"/></svg>')


def video_section(code, w, e):
    """The "See it work" part, or nothing when this language has no video file yet."""
    mp4 = ROOT / "assets" / "video" / f"use-case-{code}.mp4"
    poster = ROOT / "assets" / "video" / f"use-case-{code}.jpg"
    if not (mp4.exists() and poster.exists()):
        return ""
    return (
        '<section class="video" aria-labelledby="video-h"><div class="in">\n'
        f'  <p class="kicker">{e(w["video_kicker"])}</p><h2 id="video-h">{e(w["video_h"])}</h2>\n'
        f'  <div class="vframe"><video controls playsinline muted preload="none" width="1920" height="1080" '
        f'poster="/assets/video/use-case-{code}.jpg" aria-labelledby="video-h">'
        f'<source src="/assets/video/use-case-{code}.mp4" type="video/mp4"></video></div>\n'
        f'  <p class="vnote">{e(w["video_note"])}</p>\n'
        '</div></section>\n'
    )


def path_for(code):
    return "/" if code == "en" else f"/{code}/"


def json_ld(code, w):
    """What search engines read about the company and the app. No prices here: they live in one place, the price cards."""
    org = {"@type": "Organization", "@id": SITE + "/#company", "name": "Trucker Pay Protector LLC", "url": SITE + "/",
           "logo": SITE + "/icon-512.png", "email": "support@truckerpayprotector.com"}
    site = {"@type": "WebSite", "@id": SITE + "/#site", "name": "Trucker Pay Protector", "url": SITE + "/",
            "inLanguage": LANGS, "publisher": {"@id": org["@id"]}}
    app = {"@type": "MobileApplication", "name": "Trucker Pay Protector", "operatingSystem": "Android",
           "applicationCategory": "BusinessApplication", "description": w["meta_desc"], "inLanguage": code,
           "url": SITE + path_for(code), "installUrl": PLAY_URL, "publisher": {"@id": org["@id"]}}
    text = json.dumps({"@context": "https://schema.org", "@graph": [org, site, app]}, ensure_ascii=False)
    return text.replace("</", "<\\/")


def build(code, all_words):
    w = all_words[code]
    t = (HERE / "template.html").read_text(encoding="utf-8")
    e = lambda s: html.escape(s, quote=True)
    rep = {k: e(v) for k, v in w.items() if isinstance(v, str)}
    # A word with a hyphen in it ("Made-up") stays on one line in this heading.
    rep["inside_h"] = re.sub(r"(\w+-\w+)", r'<span class="nb">\1</span>', rep["inside_h"])
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
    # No aria-label: a screen reader says the words on the badge, so what is heard matches what is seen.
    rep["play_badge"] = (f'<a class="play" href="{PLAY_URL}">{PLAY_ICON}'
                         f'<span><small>{e(w["play_small"])}</small> <b lang="en" dir="ltr">Google Play</b></span></a>')
    rep["og_locale"] = "\n".join(
        [f'<meta property="og:locale" content="{OG_LOCALE[code]}">']
        + [f'<meta property="og:locale:alternate" content="{OG_LOCALE[c]}">' for c in LANGS if c != code]
    )
    rep["json_ld"] = json_ld(code, w)
    rep["chips"] = "".join(f"<li>{e(c)}</li>" for c in w["chips"])
    # FAQ answers may hold the two site links; those are written by us, so they are not escaped.
    rep["faq"] = "".join(f"<details><summary>{e(q)}</summary><p>{a}</p></details>" for q, a in w["faq"])
    video = video_section(code, w, e)
    rep["video_section"] = video
    # With no video the first part after the top fades out of the plum glow on its own.
    rep["how_class"] = "" if video else ' class="fade"'
    rep["csp_media"] = " media-src 'self';" if video else ""
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

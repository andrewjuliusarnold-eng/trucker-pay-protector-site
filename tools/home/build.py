#!/usr/bin/env python3
"""Builds the home page in every language from template.html and the <lang>.json word files.

Run from the repo root:  python3 tools/home/build.py
Writes index.html (English) and es/, fr/, pa/, ru/, ar/ index.html, plus sitemap.xml and llms.txt (the plain fact
sheet for AI assistants, from llms.txt in this folder). Change words in the .json files, not the .html.

The app's own languages are APP_LANGS below. French has a home page here, but the page only says the app is in
French once "fr" is in APP_LANGS. Add it only when French is in READY (the app's src/i18n/index.ts) on the commit
the store build is made from. Until then every page lists five languages ("priv_4"), and the French page says the
app is not in French yet. With "fr" in APP_LANGS every page uses its six language line ("priv_4_six").

The use case video: the "See it work" part is left out of a language's page until that language has its own
video file, assets/video/use-case-<lang>.mp4, and its still picture, assets/video/use-case-<lang>.jpg. The words
are burned into the video, so each language needs its own file. No file, no video part, no empty box.
The video starts muted; the player's own sound button turns the sound on. When the final video exists, set the
length in each language's "video_note" line to the real length before adding the file.
"""
import html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
LANGS = ["en", "es", "fr", "pa", "ru", "ar"]
# The languages the app itself offers. See the note at the top before adding "fr".
APP_LANGS = ["en", "es", "pa", "ru", "ar"]
LANG_NAMES_EN = {"en": "English", "es": "Spanish", "fr": "French", "pa": "Punjabi", "ru": "Russian", "ar": "Arabic"}
# Pages that are not built here but belong in the site map, in this order.
OTHER_PAGES = ["/about/", "/privacy/", "/terms/", "/delete-account/", "/beta-agreement/"]
PLAY_URL = "https://play.google.com/store/apps/details?id=com.truckerpayprotector.app"
ACCOUNT_URL = "https://account.truckerpayprotector.com/"
SITE = "https://truckerpayprotector.com"
# The language tag share previews use (Open Graph "locale").
OG_LOCALE = {"en": "en_US", "es": "es_US", "fr": "fr_CA", "pa": "pa_IN", "ru": "ru_RU", "ar": "ar_AR"}

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
    """What search engines and AI assistants read about the company, the app and the questions on the page.
    No prices here: they live in one place, the price cards. The question labels are made from the page's own
    questions and answers (links taken out), so the labels and the page can never say different things."""
    org = {"@type": "Organization", "@id": SITE + "/#company", "name": "Trucker Pay Protector LLC", "url": SITE + "/",
           "logo": SITE + "/icon-512.png", "email": "support@truckerpayprotector.com"}
    site = {"@type": "WebSite", "@id": SITE + "/#site", "name": "Trucker Pay Protector", "url": SITE + "/",
            "inLanguage": LANGS, "publisher": {"@id": org["@id"]}}
    app = {"@type": "MobileApplication", "name": "Trucker Pay Protector", "operatingSystem": "Android",
           "applicationCategory": "BusinessApplication", "description": w["meta_desc"], "inLanguage": code if code in APP_LANGS else APP_LANGS,
           "url": SITE + path_for(code), "installUrl": PLAY_URL, "publisher": {"@id": org["@id"]}}
    faq = {"@type": "FAQPage", "@id": SITE + path_for(code) + "#faq", "inLanguage": code,
           "mainEntity": [{"@type": "Question", "name": q,
                           "acceptedAnswer": {"@type": "Answer", "text": html.unescape(re.sub(r"<[^>]+>", "", a))}}
                          for q, a in w["faq"]]}
    text = json.dumps({"@context": "https://schema.org", "@graph": [org, site, app, faq]}, ensure_ascii=False)
    return text.replace("</", "<\\/")


def build(code, all_words):
    w = all_words[code]
    t = (HERE / "template.html").read_text(encoding="utf-8")
    e = lambda s: html.escape(s, quote=True)
    rep = {k: e(v) for k, v in w.items() if isinstance(v, str)}
    # A word with a hyphen in it ("Made-up") stays on one line in this heading.
    rep["inside_h"] = re.sub(r"(\w+-\w+)", r'<span class="nb">\1</span>', rep["inside_h"])
    if "fr" in APP_LANGS:
        rep["priv_4"] = rep["priv_4_six"]
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
    rep["foot_guides_html"] = f'<a href="/guides/">{e(w["foot_guides"])}</a>' if w.get("foot_guides") else ""
    rep["legal_note_html"] = f"<p>{e(w['legal_note'])}</p>" if w.get("legal_note") else ""
    for k, v in rep.items():
        t = t.replace("{{" + k + "}}", v)
    assert "{{" not in t, [line for line in t.splitlines() if "{{" in line][:3]
    out = ROOT / ("index.html" if code == "en" else f"{code}/index.html")
    out.parent.mkdir(exist_ok=True)
    out.write_text(t, encoding="utf-8")
    return out


def sitemap(guide_paths):
    """sitemap.xml: each home page with its language links, then the other pages and the guides."""
    alt = "".join(f'    <xhtml:link rel="alternate" hreflang="{c}" href="{SITE}{path_for(c)}"/>\n' for c in LANGS)
    alt += f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}/"/>\n'
    out = ['<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n']
    for c in LANGS:
        out.append(f"  <url>\n    <loc>{SITE}{path_for(c)}</loc>\n{alt}  </url>\n")
    for p in OTHER_PAGES + guide_paths:
        out.append(f"  <url>\n    <loc>{SITE}{p}</loc>\n  </url>\n")
    out.append("</urlset>\n")
    (ROOT / "sitemap.xml").write_text("".join(out), encoding="utf-8")


def guide_paths():
    """The guide pages that exist (made by tools/guides/build.py), the list page first."""
    g = ROOT / "guides"
    if not (g / "index.html").exists():
        return []
    return ["/guides/"] + sorted(f"/guides/{d.name}/" for d in g.iterdir() if (d / "index.html").exists())


def llms_txt():
    """llms.txt: the plain fact sheet. Its language line follows APP_LANGS; a guide link is kept only if the page exists."""
    t = (HERE / "llms.txt").read_text(encoding="utf-8")
    t = t.replace("{{app_languages}}", ", ".join(LANG_NAMES_EN[c] for c in APP_LANGS))
    have = set(guide_paths())
    lines = [ln for ln in t.splitlines() if "/guides/" not in ln or re.search(r"truckerpayprotector\.com(/guides/[^ ]*)", ln).group(1) in have]
    assert "{{" not in t
    (ROOT / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    words = {c: json.loads((HERE / f"{c}.json").read_text(encoding="utf-8")) for c in LANGS}
    keys = set(words["en"])
    for c in LANGS:
        missing = keys - set(words[c]) - {"foot_guides"}
        assert not missing, (c, sorted(missing))
    for c in LANGS:
        print("wrote", build(c, words).relative_to(ROOT))
    sitemap(guide_paths())
    llms_txt()
    print("wrote sitemap.xml and llms.txt")

#!/usr/bin/env python3
"""Builds the guide pages (English) from the .md files in this folder.

Run from the repo root:  python3 tools/guides/build.py   then   python3 tools/home/build.py
(the second one puts the guides in sitemap.xml and llms.txt).
Writes guides/index.html and guides/<name>/index.html. Change words in the .md files, not the .html.

A file is named <order>-<address name>.md and starts with "title:" and "description:" lines, then "---", then
the words. The few marks it knows: "# " the page heading, "## " a part heading, "- " a list, "1. " numbered steps,
lines right under each other stay on their own lines, and "[Get it on Google Play]" is the store button.
Every word here is public: it goes to the legal check before it is published.
"""
import html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
SITE = "https://truckerpayprotector.com"
PLAY_URL = "https://play.google.com/store/apps/details?id=com.truckerpayprotector.app"
ACCOUNT_URL = "https://account.truckerpayprotector.com/"
LIST_TITLE = "Pay guides for truck drivers"
LIST_DESC = "Short guides on how to check your own trucking pay, one question at a time."
LIST_INTRO = "Short guides on how to check your own pay. The numbers in them are made up. They are not legal, tax or payroll advice."
# Words in a guide that link to another guide.
LINKS = {"see our escrow guide": "/guides/escrow/"}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; manifest-src 'self'; script-src 'self'; base-uri 'none'; form-action 'none'">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}: Trucker Pay Protector</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#000000">
<meta name="color-scheme" content="dark">
<meta property="og:site_name" content="Trucker Pay Protector">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="https://truckerpayprotector.com/assets/social-plum-1200x630.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:type" content="{og_type}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://truckerpayprotector.com/assets/social-plum-1200x630.png">
<link rel="icon" href="/favicon.svg?v=plum2" type="image/svg+xml">
<link rel="icon" href="/favicon.ico?v=plum2" sizes="any">
<link rel="icon" href="/favicon-48.png?v=plum2" sizes="48x48" type="image/png">
<link rel="icon" href="/icon-192.png?v=plum2" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=plum2">
<link rel="canonical" href="{url}">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap">
<link rel="stylesheet" href="/assets/pages.css?v=2026-11-18">
<script type="application/ld+json">{json_ld}</script>
</head>
<body>
<a class="skip" href="#main">Skip to the main part</a>
<div class="wrap">

  <nav>
    <a class="brand" href="/" aria-label="Trucker Pay Protector">
      <img src="/assets/lockup-night.svg" alt="Trucker Pay Protector" width="110" height="36">
    </a>
    <div class="navlinks"><a href="/">Home</a><a href="/guides/"{here}>Guides</a><a class="login" href="{account}">Log in</a></div>
  </nav>

  <main id="main">
  <header class="page">
    <h1>{h1}</h1>
  </header>

  <div class="doc guide">
{body}
  </div>

  </main>

  <footer>
    <p class="row"><a href="/">Home</a><a href="/about/">Our story</a><a href="/guides/">Pay guides</a><a href="/privacy/">Privacy Policy</a><a href="/terms/">Terms of Service</a><a href="/delete-account/">Delete your account</a><a href="mailto:support@truckerpayprotector.com">Get help</a></p>
    <p class="tm">© 2026 Trucker Pay Protector LLC</p>
  </footer>

</div>
</body>
</html>
"""


def e(s):
    return html.escape(s, quote=True)


def inline(s):
    """One line of words, made safe, with the links to other guides put in."""
    out = e(s)
    for words, href in LINKS.items():
        out = out.replace(e(words), f'<a href="{href}">{e(words)}</a>')
    return out


def blocks(text):
    """The words of a guide as HTML. Returns (page heading, body)."""
    h1, out, part_open = None, [], False
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [ln.rstrip() for ln in block.splitlines() if ln.strip()]
        if lines[0].startswith("# "):
            assert h1 is None and len(lines) == 1, lines
            h1 = lines[0][2:]
        elif lines[0].startswith("## "):
            assert len(lines) == 1, lines
            out.append(("    </section>\n" if part_open else "") + f"    <section>\n      <h2>{inline(lines[0][3:])}</h2>")
            part_open = True
        elif all(ln.startswith("- ") for ln in lines):
            out.append("      <ul>\n" + "".join(f"        <li>{inline(ln[2:])}</li>\n" for ln in lines) + "      </ul>")
        elif all(re.match(r"\d+\. ", ln) for ln in lines):
            first = int(lines[0].split(".")[0])
            start = "" if first == 1 else f' start="{first}"'
            out.append(f"      <ol{start}>\n" + "".join(f"        <li>{inline(ln.split('. ', 1)[1])}</li>\n" for ln in lines) + "      </ol>")
        elif lines == ["[Get it on Google Play]"]:
            out.append(f'      <p><a class="btn" href="{PLAY_URL}">Get it on Google Play</a></p>')
        else:
            assert not any(ln.startswith(("#", "- ", "[")) for ln in lines), lines
            out.append("      <p>" + "<br>\n      ".join(inline(ln) for ln in lines) + "</p>")
    if part_open:
        out.append("    </section>")
    assert h1, "a guide needs a '# ' heading"
    return h1, "\n".join(out)


def ld(obj):
    return json.dumps({"@context": "https://schema.org", **obj}, ensure_ascii=False).replace("</", "<\\/")


def read(path):
    head, body = path.read_text(encoding="utf-8").split("\n---\n", 1)
    meta = dict(ln.split(": ", 1) for ln in head.splitlines() if ln.strip())
    slug = path.stem.split("-", 1)[1]
    return {"slug": slug, "title": meta["title"], "desc": meta["description"], "body": body}


def write(rel, **kw):
    out = ROOT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(PAGE.format(account=ACCOUNT_URL, **kw), encoding="utf-8")
    print("wrote", rel)


if __name__ == "__main__":
    guides = [read(p) for p in sorted(HERE.glob("[0-9]*-*.md"))]
    company = {"@type": "Organization", "@id": SITE + "/#company", "name": "Trucker Pay Protector LLC", "url": SITE + "/"}
    for g in guides:
        url = f"{SITE}/guides/{g['slug']}/"
        h1, body = blocks(g["body"])
        assert h1 == g["title"], (h1, g["title"])
        body += '\n    <p><a href="/guides/">All pay guides</a></p>'
        write(f"guides/{g['slug']}/index.html", title=e(g["title"]), desc=e(g["desc"]), url=url, og_type="article", here="",
              h1=e(h1), body=body,
              json_ld=ld({"@type": "Article", "headline": g["title"], "description": g["desc"], "inLanguage": "en",
                          "mainEntityOfPage": url, "author": company, "publisher": company}))
    items = "".join(f'        <li><a href="/guides/{g["slug"]}/">{e(g["title"])}</a><br>{e(g["desc"])}</li>\n' for g in guides)
    write("guides/index.html", title=e(LIST_TITLE), desc=e(LIST_DESC), url=SITE + "/guides/", og_type="website",
          here=' aria-current="page"', h1=e(LIST_TITLE),
          body=f"    <p>{e(LIST_INTRO)}</p>\n    <ul>\n{items}    </ul>",
          json_ld=ld({"@type": "CollectionPage", "name": LIST_TITLE, "description": LIST_DESC, "inLanguage": "en",
                      "url": SITE + "/guides/", "publisher": company,
                      "hasPart": [{"@type": "Article", "headline": g["title"], "url": f"{SITE}/guides/{g['slug']}/"} for g in guides]}))

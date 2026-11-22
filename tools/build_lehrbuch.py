"""Baut das SmartCar-Lehrbuch als eine einzige HTML-Datei aus der Doku im Repo.

Quelle sind die Markdown-Dateien (Übungen, Betriebshandbuch, Einstieg) plus die
Rahmentexte in docs/lehrbuch/. Reihenfolge und Gliederung stehen in BOOK unten.
Neue Übungen dort eintragen.

Aufruf (vom Repo-Wurzelverzeichnis aus):
    .venv/Scripts/python.exe tools/build_lehrbuch.py            # Windows
    .venv/bin/python tools/build_lehrbuch.py                    # Linux/Mac

Optionen:
    --out <datei>     Zieldatei (Standard: dist/SmartCar_Lehrbuch.html)
    --no-embed        Bilder nicht einbetten, sondern relativ verlinken
                      (kleinere Datei, funktioniert dann nur innerhalb des Repos)

Ergebnis: eine eigenständige HTML-Datei mit Inhaltsverzeichnis und eingebetteten
Bildern, die sich verschicken und im Browser als PDF drucken lässt.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import mimetypes
import re
import subprocess
import sys
from pathlib import Path

try:
    from markdown_it import MarkdownIt
except ImportError:
    sys.exit("Paket 'markdown-it-py' fehlt: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent.parent

TITLE = "SmartCar – Lehrbuch"
SUBTITLE = "Einem Raspberry-Pi-Auto das Einparken beibringen: Bildverarbeitung und mobile Robotik am echten Gerät"

# ---------------------------------------------------------------------------
# Gliederung. ("teil", Titel) beginnt einen neuen Teil.
# ("datei", Pfad, Titel oder None, Art). Titel ersetzt die erste Überschrift
# der Datei. Art steuert nur die Darstellung: "kapitel" = Kapitel-Einleitung,
# "uebung" = Übung, sonst normales Kapitel.
# ---------------------------------------------------------------------------
BOOK = [
    ("teil", "Teil I – Einstieg"),
    ("datei", "docs/lehrbuch/00_vorwort.md", None, ""),
    ("datei", "docs/KOLLEGEN_ANLEITUNG.md", "Zugang und Setup", ""),
    ("datei", "docs/lehrbuch/01_auto_ueberblick.md", None, ""),

    ("teil", "Teil II – Übungen"),
    ("datei", "docs/exercises/README.md", "Übersicht der Übungen", ""),
    ("datei", "docs/lehrbuch/10_kapitel_sehen.md", None, "kapitel"),
    ("datei", "docs/exercises/head_movement_exercise_1.md", None, "uebung"),
    ("datei", "docs/exercises/cv_exercise_1.md", None, "uebung"),
    ("datei", "docs/lehrbuch/20_kapitel_bewegen.md", None, "kapitel"),
    ("datei", "docs/exercises/drive_exercise_1.md", None, "uebung"),
    ("datei", "docs/exercises/turn_exercise_1.md", None, "uebung"),
    ("datei", "docs/lehrbuch/30_kapitel_finden.md", None, "kapitel"),
    ("datei", "docs/exercises/align_exercise_1.md", None, "uebung"),
    ("datei", "docs/exercises/calibration_exercise_1.md", None, "uebung"),
    ("datei", "docs/lehrbuch/40_kapitel_ankommen.md", None, "kapitel"),
    ("datei", "docs/exercises/park_exercise_1.md", None, "uebung"),
    ("datei", "docs/exercises/mission_exercise_1.md", None, "uebung"),

    ("teil", "Teil III – Weiter geht's"),
    ("datei", "docs/lehrbuch/50_weiter_gehts.md", None, ""),

    ("teil", "Anhang"),
    ("datei", "docs/OPERATIONS_MANUAL.md", "Anhang A: Betriebshandbuch", ""),
    ("datei", "docs/lehrbuch/90_glossar.md", "Anhang B: Glossar", ""),
]


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def gh_slug(text: str) -> str:
    """Anker wie bei GitHub: klein, Satzzeichen weg, Leerzeichen -> '-'."""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return text.replace(" ", "-")


def chapter_id(rel: str) -> str:
    return "k-" + re.sub(r"[^a-z0-9]+", "-", Path(rel).stem.lower()).strip("-")


def git_version() -> str:
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%h (%cs)"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip()
    except Exception:
        return ""


def replace_title(text: str, title: str) -> str:
    """Erste Überschrift der Ebene 1 ersetzen (außerhalb von Codeblöcken)."""
    lines, in_code = text.splitlines(), False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_code = not in_code
        if not in_code and line.startswith("# "):
            lines[i] = "# " + title
            return "\n".join(lines)
    return "# " + title + "\n\n" + text


def first_title(text: str) -> str:
    in_code = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
        if not in_code and line.startswith("# "):
            return line[2:].strip()
    return "Ohne Titel"


# ---------------------------------------------------------------------------
# Bauen
# ---------------------------------------------------------------------------
class Builder:
    def __init__(self, embed: bool, out: Path):
        self.embed = embed
        self.out = out
        self.warnings: list[str] = []
        # Datei im Buch -> Kapitel-Anker
        self.in_book = {str(Path(e[1])).replace("\\", "/"): chapter_id(e[1])
                        for e in BOOK if e[0] == "datei"}
        self.image_cache: dict[Path, str] = {}

    # --- Links und Bilder umschreiben ------------------------------------
    def resolve(self, src_file: Path, target: str) -> Path:
        return (src_file.parent / target).resolve()

    def rel_to_root(self, p: Path) -> str | None:
        try:
            return p.relative_to(ROOT).as_posix()
        except ValueError:
            return None

    def fix_href(self, src_file: Path, m: re.Match) -> str:
        """<a ATTRS href="HREF" ATTRS2>INNER</a> umschreiben."""
        attrs, href, inner = m.group(1) + m.group(3) + " ", m.group(2), m.group(4)
        if re.match(r"^[a-z]+:", href):                    # http, https, mailto
            return f'<a{attrs}href="{href}" target="_blank" rel="noopener">{inner}</a>'
        cid = chapter_id(str(src_file.relative_to(ROOT)))
        if href.startswith("#"):                            # Anker in derselben Datei
            return f'<a{attrs}href="#{cid}--{href[1:]}">{inner}</a>'
        path, _, frag = href.partition("#")
        rel = self.rel_to_root(self.resolve(src_file, path))
        if rel in self.in_book:
            target = self.in_book[rel] + (f"--{frag}" if frag else "")
            return f'<a{attrs}href="#{target}">{inner}</a>'
        # Datei liegt im Repo, aber nicht im Buch (Skripte, Admin-Doku, Ordner)
        shown = rel or href
        return f'<span class="repo-ref" title="Im Repository: {html.escape(shown)}">{inner}</span>'

    def image_data(self, p: Path) -> str | None:
        if p in self.image_cache:
            return self.image_cache[p]
        if not p.is_file():
            return None
        mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
        data = f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")
        self.image_cache[p] = data
        return data

    def fix_img(self, src_file: Path, m: re.Match) -> str:
        before, src, after = m.group(1), m.group(2), m.group(3)
        if re.match(r"^[a-z]+:", src):
            return m.group(0)
        p = self.resolve(src_file, src)
        if self.embed:
            data = self.image_data(p)
            if data is None:
                self.warnings.append(f"Bild fehlt: {src} (in {src_file.relative_to(ROOT)})")
                return m.group(0)
            return f'<img{before}src="{data}"{after}>'
        rel = Path(*([".."] * len(self.out.parent.relative_to(ROOT).parts))) / p.relative_to(ROOT)
        return f'<img{before}src="{rel.as_posix()}"{after} loading="lazy">'

    # --- Eine Datei rendern -----------------------------------------------
    def render(self, rel: str, title: str | None, kind: str):
        src_file = ROOT / rel
        if not src_file.is_file():
            self.warnings.append(f"Datei fehlt: {rel}")
            return None
        text = src_file.read_text(encoding="utf-8")
        if title:
            text = replace_title(text, title)
        chap_title = first_title(text)
        cid = chapter_id(rel)
        md = MarkdownIt("commonmark", {"html": True, "breaks": True}).enable("table")
        tokens = md.parse(text)

        # Überschriften eine Ebene tiefer (H1 = Teil des Buches), Anker wie bei GitHub
        sections, used = [], set()
        for i, tok in enumerate(tokens):
            if tok.type not in ("heading_open", "heading_close"):
                continue
            level = min(int(tok.tag[1]) + 1, 6)
            tok.tag = f"h{level}"
            if tok.type == "heading_open":
                inline = tokens[i + 1]
                slug = base = f"{cid}--{gh_slug(md.renderer.renderInline(inline.children, md.options, {}))}"
                n = 1
                while slug in used:
                    slug, n = f"{base}-{n}", n + 1
                used.add(slug)
                tok.attrSet("id", cid if level == 2 and cid not in used else slug)
                used.add(tok.attrGet("id"))
                if level == 3:
                    sections.append((tok.attrGet("id"),
                                     md.renderer.renderInline(inline.children, md.options, {})))
        body = md.renderer.render(tokens, md.options, {})
        body = re.sub(r'<a([^>]*?)href="([^"]*)"([^>]*)>(.*?)</a>',
                      lambda m: self.fix_href(src_file, m), body, flags=re.S)
        body = re.sub(r'<img([^>]*?)src="([^"]*)"([^>]*)>',
                      lambda m: self.fix_img(src_file, m), body)
        return {"id": cid, "title": chap_title, "kind": kind, "body": body,
                "sections": sections, "source": rel}

    # --- Gesamtes Buch -----------------------------------------------------
    def build(self) -> str:
        parts: list[dict] = []
        for entry in BOOK:
            if entry[0] == "teil":
                parts.append({"title": entry[1], "id": "t-" + gh_slug(entry[1]), "chapters": []})
            else:
                ch = self.render(entry[1], entry[2], entry[3])
                if ch:
                    parts[-1]["chapters"].append(ch)
        return self.page(parts)

    def page(self, parts: list[dict]) -> str:
        toc, content = [], []
        for part in parts:
            toc.append(f'<li class="toc-teil"><a href="#{part["id"]}">{html.escape(part["title"])}</a><ul>')
            content.append(f'<section class="teil" id="{part["id"]}"><h1>{html.escape(part["title"])}</h1></section>')
            for ch in part["chapters"]:
                subs = "".join(f'<li><a href="#{sid}">{name}</a></li>' for sid, name in ch["sections"])
                sub_html = f'<ul class="toc-sub">{subs}</ul>' if subs and ch["kind"] != "kapitel" else ""
                toc.append(f'<li class="toc-{ch["kind"] or "kap"}"><a href="#{ch["id"]}">'
                           f'{html.escape(ch["title"])}</a>{sub_html}</li>')
                content.append(f'<article class="kap {ch["kind"]}" data-source="{ch["source"]}">'
                               f'{ch["body"]}<p class="quelle">Quelle: <code>{ch["source"]}</code></p></article>')
            toc.append("</ul></li>")

        version = git_version()
        stand = dt.date.today().strftime("%d.%m.%Y")
        meta = f"Stand: {stand}" + (f" · Version {html.escape(version)}" if version else "")
        return TEMPLATE.format(
            title=html.escape(TITLE), subtitle=html.escape(SUBTITLE), meta=meta,
            toc="\n".join(toc), content="\n".join(content), css=CSS, js=JS)


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
CSS = r"""
:root{--bg:#fbfaf7;--fg:#1f2328;--muted:#5f6670;--line:#e3e0d8;--side:#f2efe8;--accent:#1f7a5a;
--accent-soft:#e3f1ea;--code:#f1eee7;--warn:#fff4dc;--kap:#eef4fb}
@media (prefers-color-scheme:dark){:root{--bg:#15171a;--fg:#e6e6e3;--muted:#9aa0a6;--line:#2c3036;
--side:#1b1e22;--accent:#5cc29a;--accent-soft:#1d2e27;--code:#22262b;--warn:#2e2818;--kap:#1b2532}}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:1rem}
body{margin:0;background:var(--bg);color:var(--fg);font:16.5px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--accent)}
nav#toc{position:fixed;top:0;left:0;bottom:0;width:19rem;overflow-y:auto;background:var(--side);
border-right:1px solid var(--line);padding:1.2rem 1rem 3rem;font-size:.9rem;line-height:1.4}
nav#toc .brand{font-weight:700;font-size:1.05rem;margin:0 0 1rem;display:block;color:var(--fg);text-decoration:none}
nav#toc ul{list-style:none;margin:0;padding:0}
nav#toc li{margin:.15rem 0}
nav#toc a{color:var(--fg);text-decoration:none;display:block;padding:.1rem .4rem;border-radius:4px}
nav#toc a:hover{background:var(--accent-soft)}
nav#toc a.active{background:var(--accent-soft);color:var(--accent);font-weight:600}
.toc-teil>a{font-weight:700;text-transform:uppercase;letter-spacing:.03em;font-size:.78rem;color:var(--muted)!important;margin-top:1rem}
.toc-kapitel>a{font-weight:600;margin-top:.5rem}
.toc-uebung{padding-left:.8rem}
.toc-sub{display:none;padding-left:.8rem!important;font-size:.84rem}
li.open>.toc-sub{display:block}
.toc-sub a{color:var(--muted)!important}
main{margin-left:19rem;padding:2rem 3rem 6rem;max-width:62rem}
.cover{padding:4rem 0 3rem;border-bottom:3px solid var(--accent);margin-bottom:2rem}
.cover h1{font-size:2.6rem;margin:0 0 .6rem;line-height:1.15}
.cover .sub{font-size:1.2rem;color:var(--muted);margin:0 0 1.5rem}
.cover .meta{font-size:.9rem;color:var(--muted)}
section.teil{margin:4rem 0 1rem;padding:1.4rem 0;border-top:3px solid var(--accent)}
section.teil h1{margin:0;font-size:2rem;color:var(--accent)}
article.kap{margin:2.5rem 0 3rem}
article.kap>h2:first-child{font-size:1.75rem;margin-top:0;padding-bottom:.4rem;border-bottom:1px solid var(--line)}
article.kapitel{background:var(--kap);border-radius:10px;padding:1.2rem 1.6rem}
article.kapitel>h2:first-child{border:0}
h3{font-size:1.35rem;margin-top:2.2rem}
h4{font-size:1.12rem;margin-top:1.8rem}
h5,h6{font-size:1rem}
code{background:var(--code);padding:.08em .35em;border-radius:4px;font-size:.88em;font-family:ui-monospace,Consolas,"Cascadia Mono",monospace}
pre{background:var(--code);padding:.9rem 1rem;border-radius:8px;overflow-x:auto;line-height:1.45;border:1px solid var(--line)}
pre code{background:none;padding:0;font-size:.85em}
table{border-collapse:collapse;margin:1rem 0;font-size:.93rem;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:.4rem .65rem;text-align:left;vertical-align:top}
th{background:var(--side)}
blockquote{margin:1rem 0;padding:.6rem 1rem;border-left:4px solid #d9a521;background:var(--warn);border-radius:0 6px 6px 0}
blockquote p{margin:.3rem 0}
img{max-width:100%;height:auto;border-radius:6px;border:1px solid var(--line);display:block;margin:1rem 0}
details{border:1px solid var(--accent);border-radius:8px;padding:.5rem 1rem;margin:1rem 0;background:var(--accent-soft)}
details>summary{cursor:pointer;font-weight:600;color:var(--accent)}
details[open]>summary{margin-bottom:.6rem}
hr{border:0;border-top:1px solid var(--line);margin:2rem 0}
.repo-ref{border-bottom:1px dotted var(--muted);cursor:help}
.quelle{font-size:.8rem;color:var(--muted);margin-top:2rem;text-align:right}
#menu{display:none}
@media (max-width:900px){
 nav#toc{transform:translateX(-100%);transition:transform .2s;z-index:10;box-shadow:0 0 20px rgba(0,0,0,.2)}
 body.menu-open nav#toc{transform:none}
 main{margin-left:0;padding:1rem 1.2rem 5rem}
 #menu{display:block;position:fixed;right:1rem;bottom:1rem;z-index:11;background:var(--accent);color:#fff;border:0;
 border-radius:50%;width:3.2rem;height:3.2rem;font-size:1.4rem;box-shadow:0 2px 8px rgba(0,0,0,.3)}
}
@media print{
 nav#toc,#menu{display:none}
 main{margin:0;padding:0;max-width:none}
 body{font-size:11pt;background:#fff;color:#000}
 section.teil,article.kap{break-before:page}
 details{border:1px solid #999}
 details>*:not(summary){display:block}
 pre,img,table{break-inside:avoid}
 a{color:#000}
}
"""

JS = r"""
window.addEventListener('beforeprint',()=>document.querySelectorAll('details').forEach(d=>{d.dataset.was=d.open;d.open=true}));
window.addEventListener('afterprint',()=>document.querySelectorAll('details').forEach(d=>{d.open=d.dataset.was==='true'}));
const menu=document.getElementById('menu');
menu.addEventListener('click',()=>document.body.classList.toggle('menu-open'));
document.querySelectorAll('nav#toc a').forEach(a=>a.addEventListener('click',()=>document.body.classList.remove('menu-open')));
const links=new Map();document.querySelectorAll('nav#toc a').forEach(a=>links.set(a.getAttribute('href').slice(1),a));
const heads=[...document.querySelectorAll('main h1[id],main section.teil,main h2[id],main h3[id]')].filter(h=>links.has(h.id));
let current=null;
function update(){let best=null;for(const h of heads){if(h.getBoundingClientRect().top<120)best=h;else break}
 if(best===current)return;current=best;document.querySelectorAll('nav#toc a.active').forEach(a=>a.classList.remove('active'));
 document.querySelectorAll('nav#toc li.open').forEach(li=>li.classList.remove('open'));
 if(!best)return;const a=links.get(best.id);a.classList.add('active');
 let li=a.closest('li');while(li){li.classList.add('open');li=li.parentElement.closest('li')}
 const n=document.getElementById('toc'),r=a.getBoundingClientRect();
 if(r.top<40||r.bottom>innerHeight-40)n.scrollTop+=r.top-innerHeight/2;}
addEventListener('scroll',()=>requestAnimationFrame(update),{passive:true});update();
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<nav id="toc">
<a class="brand" href="#top">🚗 {title}</a>
<ul>
{toc}
</ul>
</nav>
<button id="menu" aria-label="Inhaltsverzeichnis">☰</button>
<main>
<header class="cover" id="top">
<h1>{title}</h1>
<p class="sub">{subtitle}</p>
<p class="meta">{meta}<br>Erzeugt aus der Doku im Repository mit <code>tools/build_lehrbuch.py</code></p>
</header>
{content}
</main>
<script>{js}</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="dist/SmartCar_Lehrbuch.html")
    ap.add_argument("--no-embed", action="store_true")
    args = ap.parse_args()

    out = (ROOT / args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    b = Builder(embed=not args.no_embed, out=out)
    out.write_text(b.build(), encoding="utf-8")

    page = out.read_text(encoding="utf-8")
    ids = set(re.findall(r'id="([^"]+)"', page))
    for target in sorted(set(re.findall(r'href="#([^"]+)"', page)) - ids - {"top"}):
        b.warnings.append(f"Interner Link ohne Ziel: #{target}")

    for w in b.warnings:
        print("WARNUNG:", w)
    size = out.stat().st_size / 1e6
    print(f"Lehrbuch geschrieben: {out.relative_to(ROOT)} ({size:.1f} MB)")


if __name__ == "__main__":
    main()

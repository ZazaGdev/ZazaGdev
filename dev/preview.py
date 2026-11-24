# Renders README.md through GitHub's own Markdown API (so the sanitiser, camo and <picture> handling are
# GitHub's), then wraps it in a mock of the github.com/ZazaGdev profile page with a dark/light toggle.
# Run: python github-profile/dev/preview.py   (needs the `gh` CLI, logged in)
# Serve the repo root and open the printed URL:  python -m http.server 5375 --bind 127.0.0.1
#   ?theme=light|dark   which GitHub theme the mock shows (default dark)
#   &native=1           leave the <picture> sources alone, so the browser's own media queries pick the image
#                       (use Playwright's colorScheme and viewport to test them); without it the page emulates
#                       the pick from the theme toggle and the window width.
import argparse, html, json, os, subprocess, sys
from datetime import date

DEV = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DEV)                      # github-profile/, laid out like the ZazaGdev/ZazaGdev repo
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import fetch  # noqa: E402

CSS_VER = "5.8.1"  # github-markdown-css


def render_md(text):
    out = subprocess.run(["gh", "api", "markdown", "--input", "-"], input=json.dumps(
        {"text": text, "mode": "gfm", "context": "ZazaGdev/ZazaGdev"}), capture_output=True, text=True, encoding="utf8")
    if out.returncode:
        raise SystemExit(out.stderr)
    return out.stdout


def read(name):
    with open(os.path.join(fetch.FIXTURES, name), encoding="utf8") as f:
        return f.read()


def calendar_html():
    cal = fetch.parse_calendar(read("contrib-last-year.html"))
    first = date.fromisoformat(cal["days"][0][0])
    off = (first.weekday() + 1) % 7
    cells = []
    for i, (d, _, level) in enumerate(cal["days"]):
        cells.append(f'<i class="l{level}" style="grid-column:{(i + off) // 7 + 1};grid-row:{(i + off) % 7 + 1}" title="{d}"></i>')
    return cal["heading"], "".join(cells)


def pins_html():
    repos = [r for r in json.loads(read("repos.json")) if not r["fork"]]
    repos.sort(key=lambda r: -r["stargazers_count"])
    out = []
    for r in repos[:6]:
        star = f'<span>&#9734; {r["stargazers_count"]}</span>' if r["stargazers_count"] else ""
        out.append(f'<div class="pin"><div class="pin-h"><a href="https://github.com/ZazaGdev/{r["name"]}">{r["name"]}</a><span class="pub">Public</span></div>'
                   f'<p>{html.escape(r.get("description") or "")}</p><div class="pin-f"><span>{html.escape(r.get("language") or "")}</span>{star}</div></div>')
    return "".join(out)


PAGE = """<!doctype html>
<html lang="en" data-gh="dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ZazaGdev profile preview</title>
<base href="{base}">
<link id="md-light" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@{ver}/github-markdown-light.css" disabled>
<link id="md-dark" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@{ver}/github-markdown-dark.css">
<link rel="stylesheet" href="dev/frame.css">
</head><body>
<div class="demo-bar"><b>Profile preview</b><span class="demo-note">README.md rendered by GitHub's Markdown API, inside a mock of the profile page.</span>
<span class="demo-ctl"><button data-t="dark">Dark</button><button data-t="light">Light</button></span></div>
<header class="gh-top"><svg height="32" viewBox="0 0 24 24" width="32" aria-hidden="true"><circle cx="12" cy="12" r="11" fill="currentColor"/></svg>
<span class="crumb">ZazaGdev</span></header>
<nav class="gh-tabs"><span class="on">Overview</span><span>Repositories <em>{repos}</em></span><span>Projects</span><span>Packages</span><span>Stars</span></nav>
<main class="gh-main">
<aside class="gh-side">
<div class="avatar" style="background:var(--gh-line)"></div>
<h1><span class="nm">ZazaG</span><span class="lg">ZazaGdev</span></h1>
<button class="follow">Follow</button>
<p class="bio">Zaza Gejadze</p>
<ul class="meta-l"><li>Tbilisi, Georgia</li><li><a href="https://zazag.dev/">https://zazag.dev/</a></li><li><a href="https://x.com/ZazaGDev">@ZazaGDev</a></li></ul>
</aside>
<section class="gh-content">
<div class="readme"><div class="readme-h">ZazaGdev / README<span>.md</span></div>
<article class="markdown-body">{body}</article></div>
<div class="native"><div class="native-h">Pinned <small>(GitHub's own, shown below every profile README)</small></div>
<div class="pins">{pins}</div>
<div class="native-h">{contrib:,} contributions in the last year</div>
<div class="cal"><div class="cal-g">{cal}</div></div></div>
</section></main>
<script>
const q = new URLSearchParams(location.search), native = q.get('native') === '1';
const pics = [...document.querySelectorAll('.markdown-body picture')].map(p => ({
  img: p.querySelector('img'), light: p.querySelector('img').getAttribute('src'),
  srcs: [...p.querySelectorAll('source')].map(s => ({media: s.getAttribute('media'), srcset: s.getAttribute('srcset')}))}));
function pick(p, dark) {
  const phone = innerWidth <= 600;
  for (const s of p.srcs) {
    const conds = s.media.split(' and ').map(c => c.trim());
    if (conds.every(c => c.includes('prefers-color-scheme') ? dark : c.includes('max-width') ? phone : false)) return s.srcset;
  }
  return p.light;
}
function setTheme(t) {
  document.documentElement.dataset.gh = t;
  document.getElementById('md-light').disabled = t !== 'light';
  document.getElementById('md-dark').disabled = t !== 'dark';
  if (!native) pics.forEach(p => { p.img.parentElement.querySelectorAll('source').forEach(s => s.remove()); p.img.src = pick(p, t === 'dark'); });
  document.querySelectorAll('.demo-ctl button').forEach(b => b.classList.toggle('on', b.dataset.t === t));
  const u = new URL(location); u.searchParams.set('theme', t); history.replaceState(null, '', u);
}
document.querySelectorAll('.demo-ctl button').forEach(b => b.onclick = () => setTheme(b.dataset.t));
setTheme(q.get('theme') || 'dark');
if (!native) addEventListener('resize', () => pics.forEach(p => p.img.src = pick(p, document.documentElement.dataset.gh === 'dark')));
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    default_out = os.path.join(os.path.dirname(ROOT), "tmp", "3275", "final")
    ap.add_argument("--out", default=default_out, help="folder for index.html (default: <BuildinZZ>/tmp/3275/final, outside git)")
    ap.add_argument("--web-root", default=os.path.dirname(ROOT), help="the folder the preview server serves")
    ap.add_argument("--port", default="5375")
    args = ap.parse_args()
    with open(os.path.join(ROOT, "README.md"), encoding="utf8") as f:
        body = render_md(f.read())
    heading, cal = calendar_html()
    repos = len(json.loads(read("repos.json")))
    rel = os.path.relpath(ROOT, args.web_root).replace(os.sep, "/")
    page = PAGE
    for key, val in (("{base}", f"/{rel}/"), ("{ver}", CSS_VER), ("{pins}", pins_html()), ("{contrib:,}", f"{heading:,}"),
                     ("{cal}", cal), ("{repos}", str(repos)), ("{body}", body)):   # body last: it is GitHub's HTML
        page = page.replace(key, val)
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "index.html"), "w", encoding="utf8", newline="\n") as f:
        f.write(page)
    url_path = os.path.relpath(args.out, args.web_root).replace(os.sep, "/")
    print(f"wrote {os.path.join(args.out, 'index.html')}")
    print(f"serve the web root with: python -m http.server {args.port} --bind 127.0.0.1  (from {args.web_root})")
    print(f"open: http://127.0.0.1:{args.port}/{url_path}/")


if __name__ == "__main__":
    main()

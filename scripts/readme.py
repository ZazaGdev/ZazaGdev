# README.md from a template, so the numbers in every image's alt text stay current.
# Every image is a <picture> with a dark <source>. Pictures in PHONE also get phone sources.
# Source order matters: the browser takes the first one whose media matches, so dark+phone comes
# first, then phone, then dark, then the light desktop <img>.
from html import escape

from board import board_label
from cards import app_fact, app_label, fmt, hero_label, whoami_label

PHONE = ("hero", "github", "whoami")      # every picture that has a phone variant is called with phone=True


def picture(name, width, alt, phone=False):
    a = f"assets/{name}"
    srcs = []
    if phone:
        srcs.append(f'<source media="(prefers-color-scheme: dark) and (max-width: 600px)" srcset="{a}-phone-dark.svg">')
        srcs.append(f'<source media="(max-width: 600px)" srcset="{a}-phone-light.svg">')
    srcs.append(f'<source media="(prefers-color-scheme: dark)" srcset="{a}-dark.svg">')
    attr = f'height="{width[1:]}"' if width.startswith("h") else f'width="{width}"'
    return f'<picture>{"".join(srcs)}<img src="{a}-light.svg" {attr} alt="{escape(alt, quote=True)}"></picture>'


def link(url, inner):
    return f'<a href="{url}">{inner}</a>'


def render(data, P):
    L = P["links"]
    out = [link(L["site"]["url"], picture("hero", "100%", hero_label(P, data), "hero" in PHONE)), ""]
    badges = []
    for key, name in (("youtube", "yt"), ("x", "x"), ("linkedin", "li"), ("site", "site")):
        alt = f"{L[key]['label']} {L[key]['handle']}".strip()
        badges.append(link(L[key]["url"], picture(f"badge-{name}", "h44", alt)))
    out += ['<p align="center">', *badges, "</p>", ""]
    out += [picture("github", "100%", board_label(data), "github" in PHONE), ""]
    out += [picture("whoami", "100%", whoami_label(data, P), "whoami" in PHONE), ""]
    out += [picture("label-ship", "100%", "What I ship", True), ""]
    apps = []
    for a in P["apps"]:
        alt = app_label(a, app_fact(a, data, P))
        apps.append(link(a["url"], picture(f"app-{a['id']}", "49%", alt, True)))
    out += ['<p align="center">', *apps, "</p>", ""]
    S = P["store_links"]
    more = " · ".join(link(m["url"], m["name"]) for m in P["more"])
    out += [f'<p align="center"><sub>Martva on {link(S["martva_google_play"], "Google Play")} and the '
            f'{link(S["martva_app_store"], "App Store")} · more ships: {more}</sub></p>', ""]
    out += [picture("label-videos", "100%", "Latest videos", True), ""]
    vids = [link(f"https://www.youtube.com/watch?v={v['id']}", picture(f"video-{v['id']}", "32%", v["title"], True))
            for v in data["videos"]["videos"]]
    out += ['<p align="center">', *vids, "</p>", ""]
    out += [f'<p align="center"><sub>Drawn in the ZazaG Dev design system · numbers and videos redrawn every night by a GitHub Action · '
            f'{link(L["site"]["url"], "zazag.dev")}</sub></p>', ""]
    return "\n".join(out)

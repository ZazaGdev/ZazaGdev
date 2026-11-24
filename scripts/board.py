# The "On GitHub" stats board: sticker counters plus the contribution graph, drawn like GitHub's
# (53 weeks by 7 days, rounded cells, month labels, a Less/More legend) in design-system colours.
# Desktop is 880 wide; the phone variant is 440 wide with a 2-column counter grid and 26 weeks.
from datetime import date, timedelta

from cards import fmt, long_date, short_date
from svgkit import Svg, mix, text_width, wrap

FILLS = ["lx", "li", "rd", "x", "bd", "yt", "li"]
ROT = [-1.2, 1, -0.8, 1.2, -1, 0.8, -1.2]


def streak_text(cur):
    """The caption under the current streak. With no streak right now there is no start date to print."""
    if cur["days"] <= 0 or not cur["start"]:
        return "no streak right now"
    return f"current streak, since {short_date(cur['start'])}"


def counters(data):
    c, r = data["contrib"], data["repos"]
    cur, best = c["current_streak"], c["longest_streak"]
    since = f"contributions since {c['since_year']}"
    return [
        (fmt(c["last_year"]), "contributions in the last year"),
        (f"{cur['days']} days", streak_text(cur)),
        (f"{best['days']} days", "longest streak ever"),
        (fmt(c["all_time"]), since),
        (fmt(r["public_repos"]), "public repos"),
        (fmt(r["stars"]), "stars earned"),
        (fmt(r["downloads"]), "release downloads"),
    ]


def board_label(data):
    c, r = data["contrib"], data["repos"]
    cur, best = c["current_streak"], c["longest_streak"]
    streak = (f"a {cur['days']}-day current streak, since {short_date(cur['start'])}" if cur["days"] > 0 and cur["start"]
              else "no streak right now")
    return (f"On GitHub: {fmt(c['last_year'])} contributions in the last year, {streak}, "
            f"longest streak {best['days']} days, {fmt(c['all_time'])} contributions since {c['since_year']}, "
            f"{r['public_repos']} public repos, {r['stars']} stars earned, {fmt(r['downloads'])} downloads of my releases.")


def level_colors(s, bg):
    return [mix(s.col("muted"), s.col(bg), 0.14), s.col("li"), mix(s.col("go"), s.col("li"), 0.5), s.col("go"),
            mix(s.col("go"), s.col("line"), 0.7)]


def sticker(s, x, y, w, h, fill, rot):
    s.add(f'<g transform="rotate({rot} {x + w / 2:.1f} {y + h / 2:.1f})">')
    s.rect(x + 4, y + 4, w, h, "line", 18)
    s.rect(x, y, w, h, fill, 18, "line", 2)


def graph_h(pitch):
    return 16 + 22 + 7 * pitch + 10 + 26 + 14


def graph(s, x, y, w, grid, weeks, pitch, cell, note="contributions per day"):
    """A card holding the last `weeks` columns of the contribution grid. Returns the card height."""
    first = date.fromisoformat(grid["first"])
    off = (first.weekday() + 1) % 7              # row of the first cell (Sunday is row 0)
    n = len(grid["levels"])
    cols = (n - 1 + off) // 7 + 1
    c0 = max(0, cols - weeks)
    gx, gy = x + (w - weeks * pitch + (pitch - cell)) / 2, y + 16 + 22
    h = graph_h(pitch)
    s.rect(x + 4, y + 4, w, h, "line", 16)
    s.rect(x, y, w, h, "card", 16, "line", 2)
    lv = level_colors(s, "card")
    shown, prev_month = [], None
    for i in range(n):
        d = first + timedelta(days=i)
        col, row = (i + off) // 7, (i + off) % 7
        if col < c0:
            continue
        shown.append(f'<rect x="{gx + (col - c0) * pitch:.1f}" y="{gy + row * pitch:.1f}" width="{cell}" height="{cell}" rx="3" fill="{lv[int(grid["levels"][i])]}"/>')
        if row == 0 and d.day <= 7 and d.month != prev_month and (col - c0) <= weeks - 3:
            s.text(gx + (col - c0) * pitch, y + 16 + 14, d.strftime("%b"), "m400", 15, "muted")
            prev_month = d.month
    s.add("".join(shown))
    ly = gy + 7 * pitch + 10
    # legend, right aligned: Less [5 cells] More
    lw = text_width("Less", "m400", 15) + 8 + 5 * (cell + 3) + 5 + text_width("More", "m400", 15)
    lx = x + w - 16 - lw
    lx += s.text(lx, ly + 16, "Less", "m400", 15, "muted") + 8
    for k in range(5):
        s.rect(lx + k * (cell + 3), ly + 16 - cell + 1, cell, cell, lv[k], 3)
    s.text(lx + 5 * (cell + 3) + 5, ly + 16, "More", "m400", 15, "muted")
    s.text(x + 16, ly + 16, note, "m400", 15, "muted")
    return h


def github_board(t, data):
    cs = counters(data)
    W = 880
    s = Svg(W, int(322 + graph_h(14.8) + 30), t, board_label(data))
    s.board()
    s.text(32, 54, "On GitHub", "f700", 30)
    s.text(848, 52, f"redrawn every night · {long_date(data['today'])}", "m400", 15, "muted", "end")
    for i in range(4):
        x, y = 32 + i * 208, 78
        sticker(s, x, y, 190, 130, FILLS[i], ROT[i])
        num, lab = cs[i]
        s.text(x + 16, y + 52, num, "f700", 40)
        ly = y + 82
        for line in wrap(lab, "m400", 15, 160)[:3]:
            s.text(x + 16, ly, line, "m400", 15)
            ly += 19
        s.add("</g>")
    for j in range(3):
        x, y = 32 + j * 278, 230
        sticker(s, x, y, 260, 66, FILLS[4 + j], ROT[4 + j] * 0.6)
        num, lab = cs[4 + j]
        nw = s.text(x + 16, y + 44, num, "f700", 34)
        s.text(x + 16 + nw + 12, y + 40, lab, "m400", 15)
        s.add("</g>")
    graph(s, 32, 322, 816, data["contrib"]["grid"], 53, 14.8, 12)
    return s

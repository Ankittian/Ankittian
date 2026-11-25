"""Generate the crimson 'film' SVG assets for the GitHub profile README.

Mirrors the portfolio theme: blood-red grunge, white silk ribbons, black
letterbox, Michroma type, the crossbar-less Λ wordmark, clapperboard slates.
No typewriter effects — reveals are slams, fades and focus pulls.

Run from anywhere:  python tools/gen.py      (needs: pip install fonttools brotli)
See tools/README.md for how to change things.
"""
import base64, io, math, os
from fontTools.ttLib import TTFont
from fontTools import subset

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_TTF = os.path.join(HERE, "fonts", "Michroma.ttf")
BANNER = os.path.join(HERE, "source", "banner.webp")
OUT = os.path.join(HERE, "..", "assets")

RED, HOT, DEEP, BLOOD, INK, WHITE, ACC = (
    "#8e0a12", "#b3111c", "#4a0408", "#220103", "#0a0506", "#f6f3f0", "#ff3445")



def _subset_font():
    """Embed only the glyphs we use (ASCII + a few symbols) as woff2 — ~11 KB."""
    opts = subset.Options(); opts.flavor = "woff2"
    font = TTFont(FONT_TTF)
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=list(range(0x20, 0x7F)) + [0xB7, 0x2014, 0x2026, 0x2019, 0x25CF])
    sub.subset(font)
    buf = io.BytesIO(); font.flavor = "woff2"; font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


FONT_B64 = _subset_font()
TT = TTFont(FONT_TTF)
UPM = TT["head"].unitsPerEm
CMAP = TT.getBestCmap()
HMTX = TT["hmtx"]


def adv(ch, size, ls=0.0):
    g = CMAP.get(ord(ch))
    return (HMTX[g][0] / UPM * size if g else size * 0.6) + ls


def width(s, size, ls=0.0):
    return sum(adv(c, size, ls) for c in s) - ls


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


STYLE_BASE = f"""
@font-face{{font-family:'Mi';src:url(data:font/woff2;base64,{FONT_B64}) format('woff2');}}
.m{{font-family:'Mi','Arial Black',Arial,sans-serif;}}
.fit{{transform-box:fill-box;transform-origin:center;}}
"""

DEFS_FX = f"""
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/>
  <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1.4 -.55"/>
</filter>
<filter id="grunge" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".012 .02" numOctaves="5" seed="7"/>
  <feColorMatrix values="0 0 0 0 .05  0 0 0 0 0  0 0 0 0 0  -2.2 0 0 0 1.25"/>
</filter>
<filter id="glow" x="-20%" y="-50%" width="140%" height="200%">
  <feGaussianBlur stdDeviation="6" result="b"/>
  <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<filter id="shadow" x="-10%" y="-10%" width="120%" height="140%">
  <feDropShadow dx="0" dy="8" stdDeviation="7" flood-color="#140002" flood-opacity=".5"/>
</filter>
<radialGradient id="crimson" cx="55%" cy="18%" r="120%">
  <stop offset="0" stop-color="{HOT}"/><stop offset=".38" stop-color="{RED}"/>
  <stop offset=".72" stop-color="#5e060c"/><stop offset="1" stop-color="{BLOOD}"/>
</radialGradient>
<radialGradient id="vignette" cx="50%" cy="45%" r="75%">
  <stop offset=".45" stop-color="#140002" stop-opacity="0"/>
  <stop offset=".8" stop-color="#140002" stop-opacity=".55"/>
  <stop offset="1" stop-color="#0a0001" stop-opacity=".92"/>
</radialGradient>
"""

GRAIN_CSS = """
@keyframes jitter{0%{transform:translate(0,0)}25%{transform:translate(-14px,9px)}50%{transform:translate(11px,-7px)}75%{transform:translate(-6px,-12px)}100%{transform:translate(0,0)}}
.grain{animation:jitter .5s steps(1) infinite;}
"""


def svg(w, h, body, css, defs="", label=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">'
            f'<title>{esc(label)}</title><style>{STYLE_BASE}{GRAIN_CSS}{css}</style>'
            f'<defs>{DEFS_FX}{defs}</defs>{body}</svg>')


def grain(w, h, op=0.09):
    return (f'<g opacity="{op}"><rect class="grain" x="-20" y="-20" width="{w+40}" height="{h+40}" '
            f'filter="url(#grain)"/></g>')


def backdrop(w, h, rx=16, clip="clip"):
    return (f'<clipPath id="{clip}"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>'
            f'<g clip-path="url(#{clip})">'
            f'<rect width="{w}" height="{h}" fill="url(#crimson)"/>'
            f'<rect width="{w}" height="{h}" filter="url(#grunge)" opacity=".75"/>')


# ── ribbon (port of the site's procedural silk ribbon) ──────────────────
FRONT = ["#d9d4cf", "#ece8e4", "#f7f5f2", "#ffffff"]
BACK = ["#8f8883", "#a8a19b", "#bdb6b0"]


def catmull(points, samples):
    pts = [points[0], *points, points[-1]]
    out, segs = [], len(pts) - 3
    for i in range(samples + 1):
        u = i / samples * segs
        s = min(segs - 1, int(u)); t = u - s
        p0, p1, p2, p3 = pts[s:s + 4]
        f = lambda a, b, c, d: 0.5 * (2*b + (-a+c)*t + (2*a-5*b+4*c-d)*t*t + (-a+3*b-3*c+d)*t**3)
        out.append((f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])))
    return out


def ribbon(points, w, twists, phase=0.0, samples=160):
    c = catmull(points, samples); n = len(c)
    L, R, cs = [], [], []
    for i in range(n):
        a, b = c[max(0, i-1)], c[min(n-1, i+1)]
        tx, ty = b[0]-a[0], b[1]-a[1]; ln = math.hypot(tx, ty) or 1
        nx, ny = -ty/ln, tx/ln; k = i/(n-1)
        cv = math.cos(math.pi*twists*k + phase)
        taper = min(1, k*7, (1-k)*5)
        hw = w/2*(0.08+0.92*abs(cv))*taper
        L.append((c[i][0]+nx*hw, c[i][1]+ny*hw)); R.append((c[i][0]-nx*hw, c[i][1]-ny*hw)); cs.append(cv)
    buckets = {}
    for i in range(n-1):
        cv = (cs[i]+cs[i+1])/2; m = abs(cv)
        fill = FRONT[min(3, int(m*4))] if cv >= 0 else BACK[min(2, int(m*3))]
        d = "M%.1f %.1fL%.1f %.1fL%.1f %.1fL%.1f %.1fZ" % (*L[i], *L[i+1], *R[i+1], *R[i])
        buckets.setdefault(fill, []).append(d)
    return "".join(f'<path d="{"".join(ds)}" fill="{f}" stroke="{f}" stroke-width=".6" stroke-linejoin="round"/>'
                   for f, ds in buckets.items())


# ── Λ wordmark ──────────────────────────────────────────────────────────
def wordmark(text, x, y, size, fill=WHITE, ls_em=0.08, anchor="middle"):
    """Michroma letters with every 'A' swapped for the crossbar-less Λ."""
    ls = size*ls_em
    lam_w = size*0.9
    total = sum((lam_w + ls) if ch == "A" else adv(ch, size, ls) for ch in text) - ls
    cx = x - total/2 if anchor == "middle" else x
    parts = []
    for ch in text:
        if ch == "A":
            s = size/100*0.98
            parts.append(f'<polygon transform="translate({cx:.1f} {y - size*0.98:.1f}) scale({s:.4f})" '
                         f'points="0,100 38,0 52,0 90,100 74,100 45,24 16,100" fill="{fill}"/>')
            cx += lam_w + ls
        else:
            if ch != " ":
                parts.append(f'<text class="m" x="{cx:.1f}" y="{y}" font-size="{size}" fill="{fill}">{esc(ch)}</text>')
            cx += adv(ch, size, ls)
    return "".join(parts)


def digit_roll(x, y, size, count, period, fill=WHITE, name="d"):
    """A rolling digit column (stepped, film-counter style)."""
    lh = size*1.25
    col = "".join(f'<text class="m" x="0" y="{lh*i + size:.1f}" font-size="{size}" fill="{fill}">{i}</text>'
                  for i in range(count))
    css = (f"@keyframes {name}{{to{{transform:translateY(-{lh*count:.2f}px)}}}}"
           f".{name}{{animation:{name} {period}s steps({count}) infinite;}}")
    el = (f'<svg x="{x}" y="{y - size}" width="{size}" height="{lh:.1f}" overflow="hidden">'
          f'<g class="{name}">{col}</g></svg>')
    return el, css


# ════════════════════════════════════════════════════════════════════════
# HERO — the key-art banner, opened like a projector gate
# ════════════════════════════════════════════════════════════════════════
def hero():
    W, H = 1280, 427
    img = base64.b64encode(open(BANNER, "rb").read()).decode()
    bar = 36
    css = f"""
@keyframes kb{{from{{transform:scale(1.0)}}to{{transform:scale(1.045) translate(-10px,-4px)}}}}
.art{{transform-origin:62% 50%;animation:kb 16s ease-in-out infinite alternate;}}
@keyframes gateT{{0%,12%{{transform:translateY({H/2 - bar}px)}}100%{{transform:translateY(0)}}}}
@keyframes gateB{{0%,12%{{transform:translateY(-{H/2 - bar}px)}}100%{{transform:translateY(0)}}}}
.gt{{animation:gateT 1.9s cubic-bezier(.65,0,.35,1) forwards;}}
.gb{{animation:gateB 1.9s cubic-bezier(.65,0,.35,1) forwards;}}
@keyframes flash{{0%,55%{{opacity:0}}68%{{opacity:.28}}100%{{opacity:0}}}}
.flash{{animation:flash 2.4s ease-out forwards;}}
@keyframes up{{0%,70%{{opacity:0}}100%{{opacity:1}}}}
.guides{{animation:up 2.6s ease forwards;}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:.15}}}}
.rec{{animation:blink 1.2s steps(1) infinite;}}
@keyframes scan{{from{{transform:translateY(-20px)}}to{{transform:translateY({H+20}px)}}}}
.scan{{animation:scan 7s linear infinite;}}
@keyframes leak{{0%{{transform:translateX(-500px);opacity:0}}30%{{opacity:.55}}70%{{opacity:.4}}100%{{transform:translateX(1500px);opacity:0}}}}
.leak{{animation:leak 11s ease-in-out 2s infinite;}}
"""
    defs = f"""
<radialGradient id="leakg"><stop offset="0" stop-color="#ff7a3c" stop-opacity=".55"/>
<stop offset=".5" stop-color="{ACC}" stop-opacity=".18"/><stop offset="1" stop-color="{ACC}" stop-opacity="0"/></radialGradient>
<linearGradient id="scang" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
<stop offset=".5" stop-color="#fff" stop-opacity=".07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="hc"><rect width="{W}" height="{H}" rx="14"/></clipPath>
"""
    # timecode HH:MM:SS:FF — seconds and frames roll for real
    ts = 10
    s1, c1 = digit_roll(0, 0, ts, 6, 60, WHITE, "st")
    s2, c2 = digit_roll(0, 0, ts, 10, 10, WHITE, "su")
    f1, c3 = digit_roll(0, 0, ts, 3, 1, WHITE, "ft")  # 0-2 tens of frames (24fps)
    f2, c4 = digit_roll(0, 0, ts, 10, 10/24, WHITE, "fu")
    css += c1 + c2 + c3 + c4
    tc_x = W - 40
    dw = adv("0", ts, 1.5)
    tc_static_w = width("TC 00:00:", ts, 1.5)
    x0 = tc_x - (tc_static_w + dw*4 + adv(":", ts, 1.5))
    yb = H - bar/2 + 4

    def place(el, x):
        return f'<g transform="translate({x:.1f} {yb})">{el}</g>'
    tc = (f'<text class="m" x="{x0:.1f}" y="{yb}" font-size="{ts}" letter-spacing="1.5" fill="{WHITE}" opacity=".85">TC 00:00:</text>'
          + place(s1, x0 + tc_static_w) + place(s2, x0 + tc_static_w + dw)
          + f'<text class="m" x="{x0 + tc_static_w + dw*2:.1f}" y="{yb}" font-size="{ts}" fill="{WHITE}" opacity=".85">:</text>'
          + place(f1, x0 + tc_static_w + dw*2 + adv(":", ts, 1.5)) + place(f2, x0 + tc_static_w + dw*3 + adv(":", ts, 1.5)))

    g = 22  # guide inset
    br = lambda x, y, dx, dy: f'<path d="M{x} {y+dy*22}V{y}H{x+dx*22}" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="1.5"/>'
    top, bot = bar + g, H - bar - g
    body = f"""
<g clip-path="url(#hc)">
  <rect width="{W}" height="{H}" fill="{BLOOD}"/>
  <image class="art" href="data:image/webp;base64,{img}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/>
  <rect class="leak" x="-200" y="-180" width="700" height="780" fill="url(#leakg)"/>
  <rect class="scan" x="0" y="0" width="{W}" height="22" fill="url(#scang)"/>
  {grain(W, H, .1)}
  <rect width="{W}" height="{H}" fill="url(#vignette)" opacity=".55"/>
  <g class="guides">
    {br(g, top, 1, 1)}{br(W-g, top, -1, 1)}{br(g, bot, 1, -1)}{br(W-g, bot, -1, -1)}
    <path d="M{W/2-9} {H/2}H{W/2+9}M{W/2} {H/2-9}V{H/2+9}" stroke="#fff" stroke-opacity=".35"/>
  </g>
  <rect class="flash" width="{W}" height="{H}" fill="#fff"/>
  <g class="gt">
    <rect x="0" y="{-H}" width="{W}" height="{H+bar}" fill="{INK}"/>
    <circle class="rec" cx="40" cy="{bar/2}" r="4.5" fill="{ACC}"/>
    <text class="m" x="54" y="{bar/2+4}" font-size="10" letter-spacing="2" fill="{WHITE}">REC</text>
    <text class="m" x="104" y="{bar/2+4}" font-size="10" letter-spacing="2" fill="{WHITE}" opacity=".6">SCENE 01 · THE OPENING</text>
    <text class="m" x="{W-40}" y="{bar/2+4}" font-size="10" letter-spacing="2" fill="{WHITE}" opacity=".6" text-anchor="end">35MM · 2.39:1 · 24 FPS</text>
  </g>
  <g class="gb">
    <rect x="0" y="{H-bar}" width="{W}" height="{H}" fill="{INK}"/>
    <polygon points="40,{yb-8} 47,{yb-4} 40,{yb}" fill="{ACC}"/><text class="m" x="56" y="{yb}" font-size="10" letter-spacing="2" fill="{WHITE}" opacity=".85">IIT BHILAI '27 // AI RESEARCHER &amp; DEVELOPER</text>
    {tc}
  </g>
</g>"""
    return svg(W, H, body, css, defs, "Ankit Rath — AI Agents · Automation · Tech · Innovation")


# ════════════════════════════════════════════════════════════════════════
# TAGLINE — "Code in the dark. / Ship at light speed." slam reveal
# ════════════════════════════════════════════════════════════════════════
def tagline():
    W, H = 1280, 250
    css = """
@keyframes slam{0%{opacity:0;transform:scale(1.28)}9%{opacity:1;transform:scale(.985)}12%{transform:scale(1)}90%{opacity:1;transform:scale(1)}100%{opacity:0;transform:scale(.98)}}
.l1{animation:slam 9s cubic-bezier(.16,1,.3,1) infinite;}
.l2{animation:slam 9s cubic-bezier(.16,1,.3,1) .35s infinite;opacity:0}
@keyframes rise{0%,10%{opacity:0;transform:translateY(10px)}20%,90%{opacity:1;transform:translateY(0)}100%{opacity:0}}
.sub{animation:rise 9s ease infinite;opacity:0}
@keyframes sway{from{transform:translate(0,0) rotate(0)}to{transform:translate(-22px,10px) rotate(-1.6deg)}}
.rib{animation:sway 14s ease-in-out infinite alternate;transform-origin:30% 30%;}
.rib2{animation:sway 19s ease-in-out infinite alternate-reverse;transform-origin:80% 80%;}
@keyframes draw{0%,14%{stroke-dashoffset:520}40%,100%{stroke-dashoffset:0}}
.circ{stroke-dasharray:520;animation:draw 9s ease infinite;}
"""
    r1 = ribbon([(-60, 40), (150, -10), (330, 70), (520, 18), (640, -30)], 34, 3.2, .4)
    r2 = ribbon([(900, 320), (1040, 250), (1160, 270), (1260, 190), (1380, 160)], 28, 2.6, 1.1)
    line = lambda x, y, d: (f'<g class="circ" fill="none" stroke="#fff" stroke-opacity=".55" stroke-width="1.2">'
                            f'<path d="{d}"/><circle cx="{x}" cy="{y}" r="3.5"/></g>')
    body = f"""
{backdrop(W, H, 16, "tc")}
  <g class="rib" opacity=".62" filter="url(#shadow)">{r1}</g>
  <g class="rib2" opacity=".55" filter="url(#shadow)">{r2}</g>
  {line(360, 52, "M360 52H560L590 32H900")}
  {line(900, 232, "M900 232H700L680 222H380")}
  <g text-anchor="middle">
    <text class="m fit l1" x="{W/2}" y="112" font-size="40" letter-spacing="4" fill="{WHITE}" filter="url(#shadow)">CODE IN THE DARK.</text>
    <text class="m fit l2" x="{W/2}" y="164" font-size="40" letter-spacing="4" fill="none" stroke="{WHITE}" stroke-width="1.3">SHIP AT LIGHT SPEED.</text>
    <text class="m sub" x="{W/2}" y="204" font-size="11.5" letter-spacing="3.2" fill="{WHITE}" fill-opacity=".78">3D GAUSSIAN SPLATTING  ·  AGENTIC RAG  ·  COMPUTER VISION  ·  LLM SYSTEMS</text>
  </g>
  {grain(W, H, .08)}
  <rect width="{W}" height="{H}" fill="url(#vignette)" opacity=".6"/>
</g>"""
    return svg(W, H, body, css, "", "Code in the dark. Ship at light speed.")


# ════════════════════════════════════════════════════════════════════════
# SLATE — scroll-scrubbed clapperboard, one per scene
# ════════════════════════════════════════════════════════════════════════
SCENES = [
    (2, "CHARACTER STUDY", "THE PROTAGONIST", "Every story needs someone to root for."),
    (3, "ACT II", "THE JOURNEY", "Internships, research and the road so far."),
    (4, "THE CREW", "THE ARSENAL", "Every tool that made the cut."),
    (5, "FEATURE PRESENTATIONS", "THE WORKS", "Now showing in a repo near you."),
    (6, "BOX OFFICE", "THE NUMBERS", "Commits, streaks and opening-weekend stats."),
    (7, "THE SUPPORTING CAST", "THE ENSEMBLE", "Leading teams, clubs and juniors."),
    (8, "ACT III", "THE FINAL ACT", "Roll credits. Then roll the sequel."),
]
TOTAL = 8


def slate(no, kicker, title, logline):
    W, H = 1280, 124
    css = f"""
@keyframes clap{{0%{{transform:rotate(-24deg)}}10%{{transform:rotate(-24deg)}}15%{{transform:rotate(0)}}17%{{transform:rotate(-3deg)}}19%,100%{{transform:rotate(0)}}}}
.stick{{transform-origin:0 0;transform-box:view-box;animation:clap 6s cubic-bezier(.7,0,.3,1) infinite;}}
@keyframes focus{{0%,35%{{opacity:0;letter-spacing:14px}}100%{{opacity:1;letter-spacing:3px}}}}
.ttl{{animation:focus 2.2s cubic-bezier(.16,1,.3,1) both;}}
@keyframes fadein{{0%,50%{{opacity:0}}100%{{opacity:1}}}}
.fi{{animation:fadein 2.4s ease both;}}
@keyframes glint{{from{{transform:translateX(-120px)}}to{{transform:translateX(1400px)}}}}
.gl{{animation:glint 6s ease-in-out infinite;}}
@keyframes dot{{0%,49%{{opacity:1}}50%,100%{{opacity:.2}}}}
.dot{{animation:dot 1s steps(1) infinite;}}
"""
    # clapperboard
    stripes = lambda y, h, off: "".join(
        f'<polygon points="{x+off},{y} {x+off+14},{y} {x+off+4},{y+h} {x+off-10},{y+h}" fill="{WHITE}"/>'
        for x in range(0, 120, 28))
    cx, cy = 34, 46
    board = f"""
<g transform="translate({cx} {cy})">
  <rect x="0" y="12" width="96" height="58" rx="4" fill="{INK}" stroke="#fff" stroke-opacity=".25"/>
  <svg x="0" y="12" width="96" height="14" overflow="hidden"><rect width="96" height="14" fill="{INK}"/>{stripes(0, 14, 2)}</svg>
  <text class="m" x="8" y="42" font-size="7" letter-spacing="1" fill="{WHITE}" opacity=".6">SCENE</text>
  <text class="m" x="8" y="62" font-size="18" fill="{WHITE}">{no:02d}</text>
  <text class="m" x="56" y="42" font-size="7" letter-spacing="1" fill="{WHITE}" opacity=".6">TAKE</text>
  <text class="m" x="56" y="62" font-size="18" fill="{ACC}">1</text>
  <g class="stick">
    <svg x="0" y="-4" width="96" height="14" overflow="hidden"><rect width="96" height="14" fill="{INK}"/>{stripes(0, 14, 10)}</svg>
    <rect x="0" y="-4" width="96" height="14" fill="none" stroke="#fff" stroke-opacity=".25"/>
  </g>
  <circle cx="3" cy="11" r="2.4" fill="#cfc8c2"/>
</g>"""
    tx = 172
    prog = (no - 0.5) / TOTAL
    bx0, bx1 = tx, W - 40
    ticks = "".join(f'<rect x="{bx0 + (bx1-bx0)*i/TOTAL - .5:.1f}" y="104" width="1" height="6" fill="#fff" fill-opacity=".35"/>'
                    for i in range(TOTAL + 1))
    body = f"""
{backdrop(W, H, 14, "sc")}
  <rect class="gl" x="0" y="0" width="90" height="{H}" fill="#fff" opacity=".05" transform="skewX(-20)"/>
  {board}
  <text class="m fi" x="{tx}" y="40" font-size="11" letter-spacing="3" fill="{ACC}" filter="url(#glow)">SCENE {no:02d}<tspan fill="{WHITE}" fill-opacity=".7">  ·  {esc(kicker)}</tspan></text>
  <text class="m ttl" x="{tx}" y="80" font-size="30" letter-spacing="3" fill="{WHITE}" filter="url(#shadow)">{esc(title)}</text>
  <text class="m fi" x="{W-40}" y="40" font-size="10" letter-spacing="2" fill="{WHITE}" fill-opacity=".55" text-anchor="end"><tspan class="dot" fill="{ACC}">●</tspan> ROLL A · CAM 1</text>
  <text class="m fi" x="{W-40}" y="80" font-size="11" letter-spacing="1.2" fill="{WHITE}" fill-opacity=".8" text-anchor="end">{esc(logline)}</text>
  <rect x="{bx0}" y="106" width="{bx1-bx0}" height="2" fill="#fff" fill-opacity=".15"/>
  <rect x="{bx0}" y="106" width="{(bx1-bx0)*prog:.1f}" height="2" fill="{ACC}" filter="url(#glow)"/>
  <circle cx="{bx0 + (bx1-bx0)*prog:.1f}" cy="107" r="3.5" fill="{WHITE}"/>
  {ticks}
  {grain(W, H, .08)}
  <rect width="{W}" height="{H}" fill="url(#vignette)" opacity=".5"/>
</g>"""
    return svg(W, H, body, css, "", f"Scene {no:02d} — {title.title()}: {logline}")


# ════════════════════════════════════════════════════════════════════════
# FINALE — THE END … or is it?  → iris → the sequel
# ════════════════════════════════════════════════════════════════════════
def finale():
    W, H = 1280, 300
    css = """
@keyframes end{0%{opacity:0;transform:scale(1.16)}9%{opacity:1;transform:scale(1)}36%{opacity:1;transform:scale(.985)}44%,100%{opacity:0;transform:scale(.96)}}
.end{animation:end 11s cubic-bezier(.16,1,.3,1) infinite;}
@keyframes ask{0%,34%{opacity:0;transform:translateY(14px)}42%,58%{opacity:1;transform:translateY(0)}64%,100%{opacity:0;transform:translateY(-6px)}}
.ask{animation:ask 11s ease infinite;}
@keyframes iris{0%,60%{transform:scale(0)}76%,100%{transform:scale(1)}}
.iris{animation:iris 11s cubic-bezier(.65,0,.35,1) infinite;}
@keyframes irisfade{0%,93%{opacity:1}100%{opacity:0}}
.irisg{animation:irisfade 11s ease infinite;}
@keyframes seq{0%,72%{opacity:0;transform:scale(1.08)}80%,92%{opacity:1;transform:scale(1)}100%{opacity:0}}
.seq{animation:seq 11s cubic-bezier(.16,1,.3,1) infinite;}
"""
    rb = ribbon([(-40, 300), (240, 236), (520, 286), (820, 232), (1100, 276), (1340, 240)], 32, 4.2, .6)
    body = f"""
<clipPath id="fc"><rect width="{W}" height="{H}" rx="16"/></clipPath>
<g clip-path="url(#fc)">
  <rect width="{W}" height="{H}" fill="{INK}"/>
  <rect width="{W}" height="{H}" fill="url(#crimson)" opacity=".28"/>
  <text class="m fit end" x="{W/2}" y="{H/2+24}" font-size="68" letter-spacing="16" fill="{WHITE}" text-anchor="middle" filter="url(#glow)">THE END</text>
  <text class="m fit ask" x="{W/2}" y="{H/2+16}" font-size="30" letter-spacing="6" fill="{ACC}" text-anchor="middle" filter="url(#glow)">…or is it?</text>
  <g class="irisg">
    <g class="iris fit">
      <circle cx="{W/2}" cy="{H/2}" r="720" fill="url(#crimson)"/>
    </g>
    <g class="seq fit">
      <rect x="0" y="0" width="{W}" height="{H}" filter="url(#grunge)" opacity=".6"/>
      <g opacity=".8" filter="url(#shadow)">{rb}</g>
      <text class="m" x="{W/2}" y="96" font-size="12" letter-spacing="6" fill="{WHITE}" fill-opacity=".75" text-anchor="middle">COMING SOON</text>
      {wordmark("YOUR PROJECT", W/2, 158, 40)}
      <text class="m" x="{W/2}" y="200" font-size="13" letter-spacing="5" fill="{WHITE}" text-anchor="middle">STARRING US BOTH.</text>
    </g>
  </g>
  {grain(W, H, .1)}
  <rect width="{W}" height="{H}" fill="url(#vignette)" opacity=".7"/>
</g>"""
    return svg(W, H, body, css, "", "The End… or is it? Coming soon — your project, starring us both.")


# ════════════════════════════════════════════════════════════════════════
# END CREDITS — an infinite roll
# ════════════════════════════════════════════════════════════════════════
CREDITS = [
    ("WRITTEN & DIRECTED BY", "ANKIT RATH"),
    ("PRODUCED AT", "IIT BHILAI · CLASS OF '27"),
    ("RESEARCH UNIT", "TCS RESEARCH · COMPUTER VISION"),
    ("AI / ML UNIT", "CLAIRVYN AI · RAG SYSTEMS"),
    ("STARRING", "PYTHON · PYTORCH · LANGGRAPH · FASTAPI"),
    ("VISUAL EFFECTS", "3D GAUSSIAN SPLATTING"),
    ("SUPPORTING CAST", "LANGCHAIN · FAISS · PINECONE · DOCKER"),
    ("STUNT COORDINATION", "CRICKET · TABLE TENNIS"),
    ("ORIGINAL SCORE", "LATE-NIGHT LO-FI & THE OCCASIONAL SONG"),
    ("SHOT ON", "NEXT.JS · FRAMER MOTION · LENIS"),
]


def credits():
    W, H = 1280, 340
    step = 56
    block_h = 130 + step*len(CREDITS) + 90

    def block(y0):
        s = [f'<text class="m" x="{W/2}" y="{y0+30}" font-size="11" letter-spacing="6" fill="{ACC}" text-anchor="middle">A FILM BY</text>',
             wordmark("ANKIT RATH", W/2, y0+86, 40)]
        y = y0 + 150
        for role, name in CREDITS:
            s.append(f'<text class="m" x="{W/2-18}" y="{y}" font-size="10.5" letter-spacing="2.4" fill="{WHITE}" fill-opacity=".55" text-anchor="end">{esc(role)}</text>')
            s.append(f'<text class="m" x="{W/2+18}" y="{y}" font-size="13" letter-spacing="1.6" fill="{WHITE}">{esc(name)}</text>')
            y += step
        s.append(f'<text class="m" x="{W/2}" y="{y+14}" font-size="9.5" letter-spacing="3" fill="{WHITE}" fill-opacity=".45" text-anchor="middle">NO MODELS WERE OVERFIT IN THE MAKING OF THIS FILM.</text>')
        return "".join(s)

    css = f"""
@keyframes roll{{from{{transform:translateY(0)}}to{{transform:translateY(-{block_h}px)}}}}
.roll{{animation:roll 30s linear infinite;}}
"""
    defs = f"""
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{INK}"/><stop offset=".2" stop-color="{INK}" stop-opacity="0"/>
  <stop offset=".8" stop-color="{INK}" stop-opacity="0"/><stop offset="1" stop-color="{INK}"/></linearGradient>"""
    body = f"""
<clipPath id="cc"><rect width="{W}" height="{H}" rx="16"/></clipPath>
<g clip-path="url(#cc)">
  <rect width="{W}" height="{H}" fill="{INK}"/>
  <rect width="{W}" height="{H}" fill="url(#crimson)" opacity=".22"/>
  <line x1="{W/2}" y1="0" x2="{W/2}" y2="{H}" stroke="{ACC}" stroke-opacity=".18"/>
  <g class="roll"><g transform="translate(0 {H*0.55:.0f})">{block(0)}{block(block_h)}</g></g>
  <rect width="{W}" height="{H}" fill="url(#fade)"/>
  {grain(W, H, .08)}
</g>"""
    return svg(W, H, body, css, defs, "End credits — written and directed by Ankit Rath")


def write(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"{name:28s} {len(content)/1024:7.1f} KB")


write("hero.svg", hero())
write("tagline.svg", tagline())
for sc in SCENES:
    write(f"slate-{sc[0]:02d}.svg", slate(*sc))
write("finale.svg", finale())
write("credits.svg", credits())

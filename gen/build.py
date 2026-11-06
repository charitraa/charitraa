#!/usr/bin/env python3
"""Profile art: 17 animated SVGs drawn from live GitHub stats, rebuilt daily by .github/workflows/profile-art.yml.

Every file in art/ is standalone (no scripts, no external fonts), so GitHub shows it as an <img>.
Run locally: GITHUB_TOKEN=$(gh auth token) python3 gen/build.py
"""
import datetime as dt
import json
import math
import os
import random
import urllib.request
from html import escape
from pathlib import Path

LOGIN = os.environ.get('PROFILE_LOGIN', 'charitraa')
OUT = Path(__file__).resolve().parent.parent / 'art'
NPT = dt.timezone(dt.timedelta(hours=5, minutes=45))
W = 840
BG, INK, NEON, PURPLE, DIM = '#0d1117', '#e6edf3', '#00ff9c', '#7c3aed', '#7d8590'
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"


# ----------------------------------------------------------------- data
def api(url, data=None):
    h = {'Authorization': 'bearer ' + os.environ['GITHUB_TOKEN'], 'User-Agent': 'profile-art'}
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers=h)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch():
    now = dt.datetime.now(dt.timezone.utc)
    q = '''query($l:String!,$f:DateTime!,$t:DateTime!,$m:DateTime!){user(login:$l){name createdAt followers{totalCount}
    repositories(ownerAffiliations:OWNER,privacy:PUBLIC,first:100,orderBy:{field:PUSHED_AT,direction:DESC}){totalCount nodes{name description createdAt
    stargazerCount pushedAt primaryLanguage{name color} languages(first:5,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}
    contributionsCollection(from:$f,to:$t){contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}
    month:contributionsCollection(from:$m,to:$t){commitContributionsByRepository(maxRepositories:12){repository{name} contributions{totalCount}}}}}'''
    v = {'l': LOGIN, 'f': (now - dt.timedelta(days=365)).isoformat(), 't': now.isoformat(), 'm': (now - dt.timedelta(days=30)).isoformat()}
    u = api('https://api.github.com/graphql', {'query': q, 'variables': v})['data']['user']
    days = [(d['date'], d['contributionCount']) for w in u['contributionsCollection']['contributionCalendar']['weeks'] for d in w['contributionDays']]
    repos = u['repositories']['nodes']
    langs = {}
    for r in repos:
        for e in r['languages']['edges']:
            n = e['node']; langs.setdefault(n['name'], [0, n['color'] or '#8b949e'])[0] += e['size']
    top = sorted(langs.items(), key=lambda x: -x[1][0])[:6]
    msgs, commits = [], []
    for i, r in enumerate(repos[:15]):
        try:
            for c in api(f'https://api.github.com/repos/{LOGIN}/{r["name"]}/commits?author={LOGIN}&per_page=100'):
                m = c['commit']['message'].split('\n')[0].strip()
                commits.append((c['commit']['author']['date'], m))
                if i < 4 and len(msgs) < 60 and m and not m.lower().startswith('merge'):
                    msgs.append(m[:38])
        except Exception:
            pass
    month = [(x['repository']['name'], x['contributions']['totalCount']) for x in u['month']['commitContributionsByRepository']]
    return dict(name=u['name'] or LOGIN, created=u['createdAt'][:4], followers=u['followers']['totalCount'], repo_count=u['repositories']['totalCount'],
                repos=repos, days=days, total=u['contributionsCollection']['contributionCalendar']['totalContributions'],
                langs=[(n, c) for n, (s, c) in top], month=month, msgs=msgs or ['initial commit'], commits=commits)


def stats(D):
    today = dt.datetime.now(NPT).date().isoformat()
    counts = {d: c for d, c in D['days']}
    seq = [c for d, c in D['days'] if d <= today]
    i = len(seq) - 1
    if i >= 0 and seq[i] == 0:
        i -= 1
    streak = 0
    while i >= 0 and seq[i] > 0:
        streak += 1; i -= 1
    best = cur = 0
    for c in seq:
        cur = cur + 1 if c else 0; best = max(best, cur)
    last_active = next((d for d, c in reversed(D['days']) if c and d <= today), None)
    idle = (dt.date.fromisoformat(today) - dt.date.fromisoformat(last_active)).days if last_active else 99
    weeks = [sum(c for _, c in D['days'][k:k + 7]) for k in range(0, len(D['days']), 7)]
    return dict(today=today, today_count=counts.get(today, 0), streak=streak, best=best, idle=idle, weeks=weeks[-52:],
                week_now=sum(seq[-7:]), active_days=sum(1 for c in seq if c), hour=dt.datetime.now(NPT).hour)


def svg(h, body, title, extra_css=''):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="{escape(title)}">'
            f'<style>text{{font-family:{SANS}}} .m{{font-family:{MONO}}} {extra_css}</style>'
            f'<rect width="{W}" height="{h}" rx="14" fill="{BG}"/>{body}</svg>')


def label(x, y, s, size=14, fill=DIM, anchor='start', cls='', weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" class="{cls}">{escape(str(s))}</text>'


def header(title, sub):
    return label(24, 34, title, 18, INK, weight=700) + label(W - 24, 34, sub, 13, NEON, 'end', 'm')


# ----------------------------------------------------------------- 1 kites
def kites(D, S):
    rs = D['month'][:7] or [('rest', 1)]
    mx = max(c for _, c in rs)
    cols = ['#ff5c8a', '#ffd34a', '#00ff9c', '#4cb8ff', '#b69cf7', '#ff8c42', '#7ce0d3']
    body = ('<defs><linearGradient id="ks" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2a6b"/><stop offset=".7" stop-color="#e8875d"/>'
            '<stop offset="1" stop-color="#f6c27a"/></linearGradient></defs><rect width="840" height="300" rx="14" fill="url(#ks)"/>')
    body += '<path d="M0 300 L0 262 L60 250 L120 262 L200 244 L280 258 L360 240 L460 256 L560 242 L660 258 L760 246 L840 256 L840 300Z" fill="#2b1d3a"/>'
    for i, (name, c) in enumerate(rs):
        x = 80 + i * (680 / max(1, len(rs) - 1)) if len(rs) > 1 else 420
        s = 16 + 26 * c / mx; y = 70 + (i % 3) * 38 + (1 - c / mx) * 40
        col = cols[i % len(cols)]; dur = 3 + (i % 3)
        body += (f'<path d="M{x} {y + s} Q{x - 40} {y + 120} {x + (i % 2 and 30 or -30)} 262" stroke="#ffffff66" stroke-width="1" fill="none"/>'
                 f'<g style="transform-origin:{x}px {y + s}px;animation:sway {dur}s ease-in-out {i * .4}s infinite alternate">'
                 f'<path d="M{x} {y - s} L{x + s * .8} {y} L{x} {y + s} L{x - s * .8} {y}Z" fill="{col}" stroke="#0d1117" stroke-width="2"/>'
                 f'<path d="M{x} {y - s} L{x} {y + s} M{x - s * .8} {y} L{x + s * .8} {y}" stroke="#0d111766" stroke-width="1.5"/>'
                 f'<path d="M{x} {y + s} q-8 12 0 22 q8 10 0 22" stroke="{col}" stroke-width="2" fill="none"/></g>'
                 + label(x, y + s + 64 if y + s + 64 < 250 else 248, f'{name} · {c}', 11, '#fff', 'middle', 'm'))
    body += header('🪁 Dashain kite sky', 'repos flown this month')
    return svg(300, body, 'Dashain kite sky', '@keyframes sway{from{transform:rotate(-7deg)}to{transform:rotate(7deg)}}')


# ----------------------------------------------------------------- 2 tihar
def tihar(D, S):
    now = dt.datetime.now(NPT).date(); first = now.replace(day=1)
    nd = ((first.replace(month=first.month % 12 + 1, year=first.year + first.month // 12)) - first).days
    counts = dict(D['days']); lit = 0; body = ''
    for i in range(nd):
        d = (first + dt.timedelta(days=i)).isoformat(); c = counts.get(d, 0) if d <= now.isoformat() else 0
        x = 40 + (i % 16) * 49; y = 110 + (i // 16) * 90
        body += f'<path d="M{x - 16} {y} Q{x} {y + 18} {x + 16} {y} Z" fill="#a0522d" stroke="#3b1d0d" stroke-width="2"/>'
        if c:
            lit += 1
            body += (f'<circle cx="{x}" cy="{y - 10}" r="16" fill="#ffb347" opacity=".25" style="animation:glow 1.6s ease-in-out {i * .09:.2f}s infinite alternate"/>'
                     f'<path d="M{x} {y - 24} Q{x + 7} {y - 10} {x} {y - 2} Q{x - 7} {y - 10} {x} {y - 24}Z" fill="#ffd34a" '
                     f'style="transform-origin:{x}px {y}px;animation:flick .5s ease-in-out {i * .07:.2f}s infinite alternate"/>')
        else:
            body += f'<line x1="{x}" y1="{y - 2}" x2="{x}" y2="{y - 8}" stroke="#555" stroke-width="2"/>'
        body += label(x, y + 26, i + 1, 10, DIM, 'middle', 'm')
    body += header('🪔 Tihar lights', f'{lit}/{min(nd, now.day)} days lit · {now:%B}')
    return svg(300, body, 'Tihar lights', '@keyframes flick{from{transform:scale(1,1)}to{transform:scale(.85,1.12)}}@keyframes glow{from{opacity:.15}to{opacity:.45}}')


# ----------------------------------------------------------------- 3 everest climb
def everest(D, S):
    goal = 1000 if D['total'] < 1000 else 2000
    k = min(1, D['total'] / goal)
    camps = ['Base Camp', 'Camp I', 'Camp II', 'Camp III', 'Camp IV', 'Summit']
    pts = [(90, 300), (230, 250), (350, 200), (470, 150), (580, 105), (690, 55)]
    body = ('<defs><linearGradient id="es" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b1635"/><stop offset="1" stop-color="#2a3f7a"/></linearGradient></defs>'
            '<rect width="840" height="340" rx="14" fill="url(#es)"/>')
    for i in range(40):
        body += f'<circle cx="{(i * 97) % 840}" cy="{(i * 53) % 140}" r="{1 + i % 2}" fill="#fff" opacity=".6" style="animation:tw 2s {i * .13:.2f}s infinite alternate"/>'
    body += '<path d="M0 340 L120 300 L240 240 L360 190 L480 140 L600 90 L690 40 L760 110 L840 160 L840 340Z" fill="#cfd8e6"/>'
    body += '<path d="M690 40 L640 95 L668 88 L690 110 L712 86 L740 100Z" fill="#fff"/><path d="M0 340 L120 300 L240 300 L380 340Z" fill="#9aa8bd"/>'
    path = ' '.join(f'{"M" if i == 0 else "L"}{x} {y}' for i, (x, y) in enumerate(pts))
    body += f'<path d="{path}" stroke="#ffd34a" stroke-width="2" stroke-dasharray="5 6" fill="none" opacity=".8"/>'
    for (x, y), n in zip(pts, camps):
        body += f'<rect x="{x - 8}" y="{y - 12}" width="16" height="10" fill="#ff8c42" stroke="#0d1117"/>' + label(x, y + 16, n, 11, '#0b1635', 'middle', weight=700)
    seg = k * (len(pts) - 1); a = int(min(seg, len(pts) - 2)); f = seg - a
    cx = pts[a][0] + (pts[a + 1][0] - pts[a][0]) * f; cy = pts[a][1] + (pts[a + 1][1] - pts[a][1]) * f
    body += (f'<g style="animation:bob 1s ease-in-out infinite alternate"><circle cx="{cx}" cy="{cy - 26}" r="7" fill="#ffd34a"/>'
             f'<rect x="{cx - 6}" y="{cy - 19}" width="12" height="16" rx="3" fill="#e5484d"/><rect x="{cx + 5}" y="{cy - 18}" width="7" height="11" rx="2" fill="#0b1635"/>'
             f'<line x1="{cx - 4}" y1="{cy - 3}" x2="{cx - 7}" y2="{cy + 6}" stroke="#0b1635" stroke-width="3"/><line x1="{cx + 4}" y1="{cy - 3}" x2="{cx + 7}" y2="{cy + 6}" stroke="#0b1635" stroke-width="3"/></g>')
    if k >= 1:
        body += '<line x1="690" y1="40" x2="690" y2="8" stroke="#fff" stroke-width="2"/><path d="M690 8 L712 16 L700 18 L712 28 L690 30Z" fill="#dc143c"/>'
    body += header('🏔️ Everest climb', f'{D["total"]} / {goal} contributions · {int(k * 100)}% up')
    return svg(340, body, 'Everest climb', '@keyframes bob{from{transform:translateY(0)}to{transform:translateY(-4px)}}@keyframes tw{from{opacity:.2}to{opacity:.9}}')


# ----------------------------------------------------------------- 4 traffic
def traffic(D, S):
    n = max(1, min(14, S['week_now']))
    body = '<rect y="60" width="840" height="130" fill="#1a1f2e"/>'
    for i in range(10):
        x = i * 86 + 6; h = 70 + (i * 37) % 50
        body += (f'<rect x="{x}" y="{190 - h}" width="78" height="{h}" fill="{["#8b3a2b", "#a0472f", "#7a3326"][i % 3]}" stroke="#0d1117"/>'
                 f'<path d="M{x - 6} {190 - h} L{x + 39} {170 - h} L{x + 84} {190 - h}Z" fill="#3b2a1d"/>')
        for r in range(h // 30):
            body += f'<rect x="{x + 12}" y="{198 - h + r * 28}" width="16" height="14" fill="#f6c27a" opacity=".85"/><rect x="{x + 48}" y="{198 - h + r * 28}" width="16" height="14" fill="#2b1d12"/>'
    body += '<rect y="190" width="840" height="80" fill="#2d3340"/>' + ''.join(f'<rect x="{i * 70}" y="228" width="36" height="4" fill="#ffd34a"/>' for i in range(13))
    cols = ['#e5484d', '#ffd34a', '#30a46c', '#4cb8ff', '#ff8c42', '#b69cf7', '#f2f2f2']
    for i in range(n):
        lane = i % 2; dur = 6 + (i * 1.7) % 5; y = 202 if lane == 0 else 236; col = cols[i % len(cols)]; dirn = 'rl' if lane else 'lr'
        bus = i % 4 == 0
        w = 70 if bus else 44
        body += (f'<g style="animation:{dirn} {dur:.1f}s linear {-i * 1.3:.1f}s infinite"><rect x="0" y="{y}" width="{w}" height="22" rx="5" fill="{col}" stroke="#0d1117" stroke-width="2"/>'
                 f'<rect x="{w - 18}" y="{y + 4}" width="12" height="8" fill="#a9d6e4"/><circle cx="10" cy="{y + 23}" r="5" fill="#0d1117"/><circle cx="{w - 10}" cy="{y + 23}" r="5" fill="#0d1117"/></g>')
    body += header('🛺 Kathmandu traffic', f'{S["week_now"]} commits on the road this week')
    return svg(280, body, 'Kathmandu traffic', '@keyframes lr{from{transform:translateX(-90px)}to{transform:translateX(860px)}}@keyframes rl{from{transform:translateX(860px) scaleX(-1)}to{transform:translateX(-90px) scaleX(-1)}}')


# ----------------------------------------------------------------- 5 koi pond
def koi_shape(cx, cy, s, cols, fin):
    c1, c2 = cols[0], cols[1] if len(cols) > 1 else '#ffffff'
    return (f'<g transform="translate({cx} {cy}) scale({s})">'
            f'<path d="M-46 0 L-70 -18 L-62 0 L-70 18Z" fill="{c1}" opacity=".9"><animateTransform attributeName="transform" type="rotate" values="-12 -46 0;12 -46 0;-12 -46 0" dur="1.2s" repeatCount="indefinite"/></path>'
            f'<path d="M-8 -14 Q4 -34 16 -14Z M-8 14 Q4 34 16 14Z" fill="{c1}" fill-opacity="{0.25 + 0.75 * fin:.2f}" stroke="{c1}" stroke-width="1.5"/>'
            f'<ellipse cx="0" cy="0" rx="48" ry="16" fill="#f7f3ea"/>'
            f'<ellipse cx="-6" cy="-3" rx="14" ry="9" fill="{c1}"/><ellipse cx="18" cy="4" rx="10" ry="7" fill="{c2}"/><ellipse cx="-26" cy="5" rx="8" ry="5" fill="{c2}"/>'
            f'<circle cx="38" cy="-5" r="2.5" fill="#0d1117"/></g>')


def koi(D, S):
    stage, s = next(((n, sc) for lim, n, sc in [(100, 'FRY', .45), (500, 'YOUNG', .65), (1500, 'ADULT', .85), (10**9, 'ELDER', 1.05)] if D['total'] < lim))
    night = S['today_count'] == 0
    fin = min(1, S['streak'] / 30)
    lc = [c for _, c in D['langs']] or ['#ff5c48', '#ffd34a']
    bg = '#06121f' if night else '#0b3b4a'
    body = (f'<defs><radialGradient id="kp" cx=".5" cy=".4" r=".75"><stop offset="0" stop-color="{"#0f2b45" if night else "#1a7a8a"}"/><stop offset="1" stop-color="{bg}"/></radialGradient></defs>'
            '<rect width="840" height="340" rx="14" fill="url(#kp)"/>')
    for i in range(5):
        body += f'<circle cx="{150 + i * 140}" cy="{90 + (i % 2) * 150}" r="10" fill="none" stroke="#ffffff55" style="transform-origin:{150 + i * 140}px {90 + (i % 2) * 150}px;animation:rip 4s {i * .8}s infinite"/>'
    for x, y, r in [(110, 270, 34), (720, 80, 40), (640, 280, 26)]:
        body += f'<path d="M{x} {y} m{-r} 0 a{r} {r * .7} 0 1 0 {2 * r} 0 L{x} {y}Z" fill="#2e8b57" stroke="#1f5e3c" stroke-width="2"/><circle cx="{x + r * .3}" cy="{y - r * .4}" r="6" fill="#ff8fb1"/>'
    if not night:
        for i in range(4):
            body += f'<path d="M{200 + i * 160} 0 L{260 + i * 160} 0 L{180 + i * 160} 340 L{120 + i * 160} 340Z" fill="#ffffff" opacity=".04"/>'
    fish = [(lc[:2], s, 'M140 170 C 300 60, 540 60, 700 170 C 540 280, 300 280, 140 170', 18)]
    for j, col in enumerate(lc[2:4]):
        fish.append(([col, '#f7f3ea'], .45, f'M{700 - j * 80} {120 + j * 90} C 500 {300 - j * 60}, 300 {40 + j * 60}, {160 + j * 60} {150 + j * 50} C 300 {260 - j * 40}, 500 {60 + j * 40}, {700 - j * 80} {120 + j * 90}', 14 + j * 4))
    for cols, sc, p, dur in fish:
        body += f'<g>{koi_shape(0, 0, sc, cols, fin)}<animateMotion dur="{dur * (0.7 if S["today_count"] else 1)}s" repeatCount="indefinite" rotate="auto" path="{p}"/></g>'
    body += label(24, 34, '🐟 Living koi', 18, INK, weight=700)
    body += (f'<rect x="{W - 120}" y="16" width="96" height="26" rx="13" fill="none" stroke="{NEON}"/>' + label(W - 72, 34, stage, 13, NEON, 'middle', 'm', 700))
    body += label(24, 324, f'{D["total"]} contributions · fins {int(fin * 100)}% ({S["streak"]}-day streak) · {"night pond: no commit yet today" if night else "fed today"}', 12, '#cfe8ee', cls='m')
    return svg(340, body, 'Living koi', '@keyframes rip{0%{transform:scale(.2);opacity:.9}100%{transform:scale(5);opacity:0}}')


# ----------------------------------------------------------------- 6 bonsai
def bonsai(D, S):
    rs = [r for r in D['repos'][:10]]
    body = ('<rect x="330" y="290" width="180" height="40" rx="6" fill="#7a3b22" stroke="#0d1117" stroke-width="2"/><rect x="320" y="282" width="200" height="14" rx="4" fill="#94492a"/>'
            '<path d="M420 285 C 410 240, 440 210, 420 170 C 405 140, 430 110, 420 90" stroke="#5a3a22" stroke-width="16" fill="none" stroke-linecap="round"/>')
    random.seed(7)
    for i, r in enumerate(rs):
        side = -1 if i % 2 else 1; y = 260 - i * 18; bx = 420 + side * (60 + (i % 3) * 30); by = y - 30
        body += f'<path d="M420 {y} Q{420 + side * 30} {y - 10} {bx} {by}" stroke="#5a3a22" stroke-width="{7 - i * .4:.1f}" fill="none" stroke-linecap="round"/>'
        leaves = 4 + min(14, len(r['name']) % 7 + (3 if r['pushedAt'] > (dt.datetime.now() - dt.timedelta(days=30)).isoformat() else 0))
        for j in range(leaves):
            lx = bx + random.uniform(-28, 28); ly = by + random.uniform(-16, 12)
            body += f'<circle cx="{lx:.0f}" cy="{ly:.0f}" r="{random.uniform(6, 11):.0f}" fill="{random.choice(["#2e8b57", "#3fa86b", "#57c27e"])}" opacity=".9"/>'
        body += label(bx, by + 30, r['name'][:16], 9, DIM, 'middle', 'm')
    if S['idle'] >= 3:
        for j in range(6):
            body += f'<circle cx="{300 + j * 50}" cy="120" r="5" fill="#c9a227" style="animation:fall {3 + j % 3}s linear {j * .6}s infinite"/>'
    body += header('🌳 Code bonsai', f'{len(rs)} branches · {"resting" if S["idle"] >= 3 else "growing"}')
    return svg(340, body, 'Code bonsai', '@keyframes fall{from{transform:translate(0,0);opacity:1}to{transform:translate(40px,210px);opacity:0}}')


# ----------------------------------------------------------------- 7 pet
def pet(D, S):
    mood = 'HAPPY' if S['idle'] <= 1 else 'SLEEPY' if S['idle'] <= 4 else 'HUNGRY'
    lvl = max(1, S['active_days'] // 10)
    P = ['..XXXX..', '.XXXXXX.', 'XXOXXOXX', 'XXXXXXXX', 'XXMMMMXX', '.XXXXXX.', '.X.XX.X.', 'X..XX..X']
    if mood == 'SLEEPY':
        P[2] = 'XX-XX-XX'
    if mood == 'HUNGRY':
        P[4] = 'XXXMMXXX'
    col = {'HAPPY': NEON, 'SLEEPY': '#b69cf7', 'HUNGRY': '#ff8c42'}[mood]
    px = 18; ox = 420 - 4 * px; oy = 80; g = ''
    for r, row in enumerate(P):
        for c, ch in enumerate(row):
            if ch != '.':
                g += f'<rect x="{ox + c * px}" y="{oy + r * px}" width="{px}" height="{px}" fill="{ {"X": col, "O": "#0d1117", "-": "#0d1117", "M": "#0d1117"}[ch] }"/>'
    body = f'<g style="animation:{"hop" if mood == "HAPPY" else "breathe"} {".6" if mood == "HAPPY" else "2"}s ease-in-out infinite alternate">{g}</g>'
    body += f'<rect x="{ox - 30}" y="{oy + 8 * px + 6}" width="{8 * px + 60}" height="6" rx="3" fill="#30363d"/>'
    say = {'HAPPY': 'yay, you coded today!', 'SLEEPY': 'zzz... commit soon?', 'HUNGRY': 'feed me commits!'}[mood]
    body += f'<rect x="560" y="70" width="230" height="44" rx="10" fill="#161b22" stroke="{col}"/>' + label(675, 98, say, 14, INK, 'middle', 'm')
    if mood == 'SLEEPY':
        body += ''.join(f'<text x="{560 - i * 20}" y="{70 - i * 18}" font-size="{14 + i * 4}" fill="#b69cf7" style="animation:zz 2s {i * .5}s infinite">z</text>' for i in range(3))
    body += header('🐉 Dev pet', f'LV {lvl} · {mood} · last code {S["idle"]}d ago')
    bars = label(60, 270, 'HUNGER', 11, DIM, cls='m') + f'<rect x="130" y="260" width="200" height="10" rx="5" fill="#30363d"/><rect x="130" y="260" width="{max(6, 200 - min(200, S["idle"] * 30))}" height="10" rx="5" fill="{col}"/>'
    bars += label(460, 270, 'JOY', 11, DIM, cls='m') + f'<rect x="510" y="260" width="200" height="10" rx="5" fill="#30363d"/><rect x="510" y="260" width="{max(6, min(200, S["streak"] * 20))}" height="10" rx="5" fill="{col}"/>'
    return svg(300, body + bars, 'Dev pet', '@keyframes hop{from{transform:translateY(0)}to{transform:translateY(-14px)}}@keyframes breathe{from{transform:scaleY(1)}to{transform:scaleY(.96)}}@keyframes zz{0%{opacity:0}50%{opacity:1}100%{opacity:0;transform:translateY(-12px)}}')


# ----------------------------------------------------------------- 8 game cartridge
def cartridge(D, S):
    lvl = int(math.sqrt(D['total'] / 4)) + 1
    ach = [('FIRST COMMIT', D['total'] > 0), ('100 CONTRIBUTIONS', D['total'] >= 100), ('500 CONTRIBUTIONS', D['total'] >= 500),
           ('7-DAY STREAK', S['best'] >= 7), ('30-DAY STREAK', S['best'] >= 30), ('POLYGLOT (5 LANGS)', len(D['langs']) >= 5),
           ('50 REPOS', D['repo_count'] >= 50), ('100 ACTIVE DAYS', S['active_days'] >= 100)]
    body = ('<rect x="20" y="20" width="800" height="300" rx="18" fill="#2b2d42" stroke="#8d99ae" stroke-width="3"/>'
            '<rect x="50" y="48" width="740" height="244" rx="8" fill="#0f380f"/>')
    for y in range(52, 290, 4):
        body += f'<rect x="50" y="{y}" width="740" height="1" fill="#000" opacity=".18"/>'
    G = '#9bbc0f'
    body += label(80, 88, f'{D["name"].upper()}  LV {lvl}', 22, G, cls='m', weight=700)
    body += label(80, 122, 'HP', 14, G, cls='m') + f'<rect x="120" y="108" width="260" height="16" fill="#306230"/><rect x="120" y="108" width="{max(8, min(260, S["streak"] * 260 // 30))}" height="16" fill="{G}"/>' + label(390, 122, f'{S["streak"]}d streak', 12, G, cls='m')
    body += label(80, 152, 'XP', 14, G, cls='m') + f'<rect x="120" y="138" width="260" height="16" fill="#306230"/><rect x="120" y="138" width="{min(260, int(260 * (D["total"] % 100) / 100) + 8)}" height="16" fill="{G}"/>' + label(390, 152, f'{D["total"]} xp', 12, G, cls='m')
    body += label(80, 190, 'ACHIEVEMENTS', 14, G, cls='m', weight=700)
    for i, (n, ok) in enumerate(ach):
        body += label(80 + (i % 2) * 340, 216 + (i // 2) * 20, ('★ ' if ok else '☆ ') + n, 13, G if ok else '#306230', cls='m')
    body += f'<text x="620" y="88" font-size="14" fill="{G}" class="m" style="animation:blink 1s steps(2) infinite">PRESS START</text>'
    return svg(340, body, 'Game cartridge', '@keyframes blink{0%{opacity:1}100%{opacity:0}}')


# ----------------------------------------------------------------- 9 trading cards
def cards(D, S):
    rs = sorted(D['repos'], key=lambda r: (-r['stargazerCount'], r['pushedAt']), reverse=False)[:3]
    rs = sorted(D['repos'][:12], key=lambda r: -len(r['description'] or ''))[:3]
    body = '<defs><linearGradient id="holo" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff5c8a" stop-opacity=".0"/><stop offset=".5" stop-color="#ffffff" stop-opacity=".35"/><stop offset="1" stop-color="#4cb8ff" stop-opacity="0"/>' \
           '<animate attributeName="x1" values="-1;1" dur="3s" repeatCount="indefinite"/><animate attributeName="x2" values="0;2" dur="3s" repeatCount="indefinite"/></linearGradient></defs>'
    for i, r in enumerate(rs):
        x = 30 + i * 270; lang = r['primaryLanguage'] or {'name': 'Code', 'color': '#8b949e'}
        body += (f'<rect x="{x}" y="50" width="240" height="270" rx="14" fill="#161b22" stroke="{lang["color"]}" stroke-width="3"/>'
                 f'<rect x="{x + 14}" y="64" width="212" height="110" rx="8" fill="{lang["color"]}" opacity=".85"/>'
                 + label(x + 120, 130, r['name'][:18], 17, '#0d1117', 'middle', weight=800)
                 + label(x + 18, 200, lang['name'], 12, lang['color'], cls='m', weight=700))
        desc = (r['description'] or 'A project by ' + LOGIN)
        words, line, ly = desc.split(), '', 224
        for w in words:
            if len(line + w) > 30:
                body += label(x + 18, ly, line, 11, INK); ly += 16; line = ''
                if ly > 280: break
            line += w + ' '
        if ly <= 280: body += label(x + 18, ly, line, 11, INK)
        body += label(x + 222, 306, f'★ {r["stargazerCount"]}', 12, '#ffd34a', 'end', 'm') + f'<rect x="{x}" y="50" width="240" height="270" rx="14" fill="url(#holo)"/>'
    body += header('🃏 Project trading cards', 'holo edition')
    return svg(340, body, 'Project trading cards')


# ----------------------------------------------------------------- 10 rocket
def rocket(D, S):
    goal = 15; fuel = min(1, S['week_now'] / goal); launch = fuel >= 1
    body = '<defs><linearGradient id="rs" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05070f"/><stop offset="1" stop-color="#1b2a6b"/></linearGradient></defs><rect width="840" height="340" rx="14" fill="url(#rs)"/>'
    for i in range(50):
        body += f'<circle cx="{(i * 131) % 840}" cy="{(i * 71) % 300}" r="1.2" fill="#fff" opacity=".7"/>'
    body += '<rect x="0" y="300" width="840" height="40" fill="#2d3340"/><rect x="390" y="230" width="10" height="70" fill="#8b949e"/>'
    anim = 'animation:lift 4s ease-in infinite' if launch else 'animation:idle .15s linear infinite alternate'
    body += (f'<g style="{anim}"><path d="M420 150 Q440 180 440 250 L400 250 Q400 180 420 150Z" fill="#e6edf3" stroke="#0d1117" stroke-width="2"/>'
             f'<circle cx="420" cy="200" r="9" fill="#4cb8ff" stroke="#0d1117" stroke-width="2"/><path d="M400 225 L385 262 L400 250Z M440 225 L455 262 L440 250Z" fill="{PURPLE}"/>'
             f'<path d="M406 252 Q420 {290 + fuel * 30} 434 252Z" fill="#ffb347" style="transform-origin:420px 252px;animation:flame .12s infinite alternate"/></g>')
    body += f'<rect x="60" y="90" width="26" height="200" rx="6" fill="#30363d"/><rect x="60" y="{90 + 200 * (1 - fuel):.0f}" width="26" height="{200 * fuel:.0f}" rx="6" fill="{NEON}"/>' + label(73, 312, 'FUEL', 11, DIM, 'middle', 'm')
    body += header('🚀 Weekly launch', f'{S["week_now"]}/{goal} commits · {"LIFTOFF!" if launch else "fuelling…"}')
    return svg(340, body, 'Weekly launch', '@keyframes lift{0%{transform:translateY(0)}20%{transform:translateY(0)}100%{transform:translateY(-320px)}}@keyframes idle{from{transform:translateX(-.6px)}to{transform:translateX(.6px)}}@keyframes flame{from{transform:scaleY(.8)}to{transform:scaleY(1.2)}}')


# ----------------------------------------------------------------- 11 matrix
def matrix(D, S):
    words = D['msgs'][:24]
    body = ''
    for i in range(24):
        w = words[i % len(words)]; x = 14 + i * 35; dur = 6 + (i * 7) % 6
        col = ''.join(f'<tspan x="{x}" dy="16">{escape(ch)}</tspan>' for ch in w[:22])
        body += f'<text y="-360" font-size="13" fill="{NEON}" class="m" opacity="{.45 + (i % 3) * .2:.2f}" style="animation:rain {dur}s linear {-i * .9:.1f}s infinite">{col}</text>'
    body += f'<rect width="840" height="54" fill="{BG}"/>' + header('🟩 Commit rain', 'your real commit messages')
    return svg(340, body, 'Commit rain', '@keyframes rain{from{transform:translateY(0)}to{transform:translateY(760px)}}')


# ----------------------------------------------------------------- 12 radar
def radar(D, S):
    now = dt.datetime.now(dt.timezone.utc); cx, cy, R = 420, 190, 140
    body = ''.join(f'<circle cx="{cx}" cy="{cy}" r="{R * k / 4}" fill="none" stroke="#00ff9c33"/>' for k in range(1, 5))
    body += f'<line x1="{cx - R}" y1="{cy}" x2="{cx + R}" y2="{cy}" stroke="#00ff9c22"/><line x1="{cx}" y1="{cy - R}" x2="{cx}" y2="{cy + R}" stroke="#00ff9c22"/>'
    body += (f'<defs><linearGradient id="sw" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00ff9c" stop-opacity="0"/><stop offset="1" stop-color="#00ff9c" stop-opacity=".45"/></linearGradient></defs>'
             f'<path d="M{cx} {cy} L{cx + R} {cy} A{R} {R} 0 0 0 {cx + R * math.cos(-0.6):.1f} {cy + R * math.sin(-0.6):.1f}Z" fill="url(#sw)" style="transform-origin:{cx}px {cy}px;animation:spin 4s linear infinite"/>')
    for i, r in enumerate(D['repos'][:12]):
        age = (now - dt.datetime.fromisoformat(r['pushedAt'].replace('Z', '+00:00'))).days
        rad = 20 + min(1, age / 365) * (R - 30); ang = i * 2.4
        x, y = cx + rad * math.cos(ang), cy + rad * math.sin(ang)
        body += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="5" fill="{NEON}" style="animation:ping 4s {(ang % 6.283) / 6.283 * 4:.2f}s infinite"/>' + label(x + 9, y + 4, r['name'][:14], 10, '#00ff9caa', cls='m')
    body += header('🛰️ Repo radar', 'closer to centre = updated more recently')
    return svg(360, body, 'Repo radar', '@keyframes spin{to{transform:rotate(360deg)}}@keyframes ping{0%{opacity:1}30%{opacity:.25}100%{opacity:.25}}')


# ----------------------------------------------------------------- 13 terminal
def terminal(D, S):
    langs = ', '.join(n for n, _ in D['langs'][:4])
    lines = [('charitra@kathmandu', ':~$ neofetch', NEON), (f'{LOGIN}@github', '', '#b69cf7'), ('----------------', '', DIM),
             ('OS      ', 'Linux (CachyOS) · Kali for the labs', INK), ('Role    ', 'Software Developer @ YakshaSoft', INK), ('Repos   ', f'{D["repo_count"]} public', INK),
             ('Commits ', f'{D["total"]} in the last year', INK), ('Streak  ', f'{S["streak"]} days (best {S["best"]})', INK), ('Langs   ', langs, INK),
             ('Since   ', f'{D["created"]} on GitHub', INK), ('Followers', f' {D["followers"]}', INK)]
    body = '<rect x="20" y="20" width="800" height="330" rx="12" fill="#161b22" stroke="#30363d"/><circle cx="44" cy="40" r="6" fill="#ff5f56"/><circle cx="64" cy="40" r="6" fill="#ffbd2e"/><circle cx="84" cy="40" r="6" fill="#27c93f"/>'
    art = ['   /\\   ', '  /  \\  ', ' / /\\ \\ ', '/_/  \\_\\', '  NEPAL ']
    for i, a in enumerate(art):
        body += label(50, 100 + i * 20, a, 15, NEON, cls='m', weight=700)
    for i, (k, v, col) in enumerate(lines):
        y = 80 + i * 24; t = 0.4 + i * 0.35
        body += (f'<text x="230" y="{y}" font-size="14" class="m" style="opacity:0;animation:show .01s {t:.2f}s forwards"><tspan fill="{col}" font-weight="700">{escape(k)}</tspan>'
                 f'<tspan fill="{INK}">{escape(v)}</tspan></text>')
    body += f'<rect x="230" y="{80 + len(lines) * 24 - 13}" width="9" height="16" fill="{NEON}" style="animation:blink 1s steps(2) infinite"/>'
    return svg(370, body, 'Animated terminal', '@keyframes show{to{opacity:1}}@keyframes blink{0%{opacity:1}100%{opacity:0}}')


# ----------------------------------------------------------------- 14 galaxy (realistic spiral)
def galaxy(D, S):
    """A tilted two-armed spiral galaxy: golden core, blue-white arms with dust lanes, pink star-forming
    regions and nebula haze. Each day you contributed is one bright twinkling star placed along the arms."""
    H = 420; cx, cy = 420, 215
    rnd = random.Random(2026)
    act = [(d, c) for d, c in D['days'] if c]
    defs = ('<defs>'
            '<filter id="gb6" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>'
            '<filter id="gb2" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2"/></filter>'
            '<filter id="gb16" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="16"/></filter>'
            '<radialGradient id="core"><stop offset="0" stop-color="#fffaf0"/><stop offset=".18" stop-color="#ffe6b0"/>'
            '<stop offset=".45" stop-color="#e9a95b" stop-opacity=".55"/><stop offset="1" stop-color="#7a4a2a" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="disk"><stop offset="0" stop-color="#b9c8ff" stop-opacity=".22"/><stop offset=".6" stop-color="#6d7fd6" stop-opacity=".08"/>'
            '<stop offset="1" stop-color="#0b0d1a" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="neb1"><stop offset="0" stop-color="#7c3aed" stop-opacity=".35"/><stop offset="1" stop-color="#7c3aed" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="neb2"><stop offset="0" stop-color="#1d6fd8" stop-opacity=".28"/><stop offset="1" stop-color="#1d6fd8" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="neb3"><stop offset="0" stop-color="#d6337a" stop-opacity=".2"/><stop offset="1" stop-color="#d6337a" stop-opacity="0"/></radialGradient>'
            '</defs>')
    out = f'<rect width="{W}" height="{H}" rx="14" fill="#05060d"/>'
    out += ('<ellipse cx="140" cy="110" rx="220" ry="120" fill="url(#neb1)"/><ellipse cx="720" cy="320" rx="240" ry="130" fill="url(#neb2)"/>'
            '<ellipse cx="640" cy="80" rx="160" ry="90" fill="url(#neb3)"/>')
    for k in range(170):  # distant field stars
        x, y = rnd.uniform(0, W), rnd.uniform(0, H); r = rnd.choice([.4, .5, .6, .8, 1.1])
        tw = f' style="animation:tw {rnd.uniform(2, 5):.1f}s {rnd.uniform(0, 4):.1f}s infinite alternate"' if k % 9 == 0 else ''
        out += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#dfe6ff" opacity="{rnd.uniform(.25, .8):.2f}"{tw}/>'

    a, b, turns = 23.0, 0.255, 3.35 * math.pi       # logarithmic spiral r = a*e^(b*t)
    rmax = a * math.exp(b * turns)
    def arm_point(t, arm, spread):
        r = a * math.exp(b * t); ang = t + arm * math.pi
        dr = rnd.gauss(0, spread * (0.10 * r + 3)); da = rnd.gauss(0, spread * 0.10)
        return (r + dr) * math.cos(ang + da), (r + dr) * math.sin(ang + da), r
    disk = f'<circle r="{rmax * 1.08:.0f}" fill="url(#disk)"/>'
    lanes = ''
    for arm in (0, 1):  # dark dust lanes just inside each arm
        pts = []
        for s_ in range(90):
            t = 0.9 + s_ / 89 * (turns - 0.9); r = a * math.exp(b * t) * 0.93; ang = t + arm * math.pi - 0.12
            pts.append(f'{r * math.cos(ang):.1f} {r * math.sin(ang):.1f}')
        lanes += f'<path d="M{" L".join(pts)}" fill="none" stroke="#120c08" stroke-opacity=".32" stroke-width="7" stroke-linecap="round" filter="url(#gb2)"/>'
    glow, dots, hii = '', '', ''
    for arm in (0, 1):
        for s_ in range(26):  # soft arm glow
            t = 0.6 + s_ / 25 * (turns - 0.6); x, y, r = arm_point(t, arm, 0)
            glow += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{12 + r * 0.2:.0f}" fill="#9fb4ff" opacity=".13" filter="url(#gb6)"/>'
        for s_ in range(760):  # the arm stars
            t = rnd.uniform(0.35, turns) ** 1.0; x, y, r = arm_point(t, arm, 1.7)
            f = r / rmax
            col = '#ffe2b0' if f < .22 else ('#f4f1ff' if f < .5 else rnd.choice(['#cfe0ff', '#a9c3ff', '#e8eeff']))
            dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rnd.uniform(.5, 1.5):.1f}" fill="{col}" opacity="{rnd.uniform(.3, .95):.2f}"/>'
        for s_ in range(12):  # pink star-forming regions
            t = rnd.uniform(1.6, turns); x, y, r = arm_point(t, arm, .6)
            hii += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rnd.uniform(2, 4.5):.1f}" fill="#ff6fa8" opacity=".75" filter="url(#gb2)"/>'
    bulge = ''.join(f'<circle cx="{rnd.gauss(0, 30):.1f}" cy="{rnd.gauss(0, 30):.1f}" r="{rnd.uniform(.5, 1.3):.1f}" fill="#ffe9c0" opacity=".8"/>' for _ in range(140))
    core = '<circle r="120" fill="url(#core)" filter="url(#gb6)"/><circle r="30" fill="#fffaf0" opacity=".9" filter="url(#gb6)"/><circle r="7" fill="#ffffff"/>'
    # your contribution days: bright stars spread along the arms, oldest near the core
    commits = ''
    n = max(1, len(act))
    for i, (d, c) in enumerate(act):
        arm = i % 2; t = 0.9 + (i // 2) / max(1, n / 2) * (turns - 1.1); x, y, r = arm_point(t, arm, .55)
        size = 1.3 + min(2.6, c * .45)
        col = ['#ffffff', '#bfe3ff', '#7ef7ff', '#b69cf7'][min(3, c // 3)]
        commits += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{size * 2.6:.1f}" fill="{col}" opacity=".18" filter="url(#gb2)"/>'
                    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{size:.1f}" fill="{col}" style="animation:tw {rnd.uniform(1.4, 3.2):.1f}s {rnd.uniform(0, 3):.1f}s infinite alternate"/>')
    spin = f'<g style="transform-origin:0 0;animation:spin 240s linear infinite">{disk}{glow}{lanes}{dots}{hii}{bulge}{commits}</g>'
    out += f'<g transform="translate({cx} {cy}) rotate(-18) scale(1 .46)">{spin}{core}</g>'
    out += f'<ellipse cx="{cx}" cy="{cy}" rx="300" ry="130" fill="url(#neb2)" opacity=".25" filter="url(#gb16)"/>'
    out += header('🌌 Galaxy of commits', f'{len(act)} active days = {len(act)} bright stars')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Galaxy of commits">'
            f'<style>text{{font-family:{SANS}}} .m{{font-family:{MONO}}} @keyframes spin{{to{{transform:rotate(360deg)}}}}@keyframes tw{{from{{opacity:.35}}to{{opacity:1}}}}</style>'
            f'{defs}{out}</svg>')


# ----------------------------------------------------------------- 15 equalizer
def equalizer(D, S):
    wk = S['weeks'][-26:]; mx = max(1, max(wk)); bw = 760 / len(wk)
    body = ''
    for i, v in enumerate(wk):
        h = 20 + 200 * v / mx; x = 40 + i * bw
        body += (f'<rect x="{x:.1f}" y="{290 - h:.0f}" width="{bw - 6:.1f}" height="{h:.0f}" rx="4" fill="url(#eq)" '
                 f'style="transform-origin:{x:.1f}px 290px;animation:pulse {0.6 + (i % 5) * .15:.2f}s ease-in-out {i * .05:.2f}s infinite alternate"/>')
    body = ('<defs><linearGradient id="eq" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#7c3aed"/><stop offset="1" stop-color="#00ff9c"/></linearGradient></defs>'
            + body + '<rect x="40" y="292" width="760" height="2" fill="#30363d"/>' + header('🎵 Commit equalizer', 'last 26 weeks'))
    return svg(320, body, 'Commit equalizer', '@keyframes pulse{from{transform:scaleY(.82)}to{transform:scaleY(1.04)}}')


# ----------------------------------------------------------------- 16 himalaya
def himalaya(D, S):
    wk = S['weeks']; mx = max(1, max(wk)); n = len(wk); step = 800 / max(1, n - 1)
    pts = [(20 + i * step, 280 - 200 * v / mx) for i, v in enumerate(wk)]
    path = 'M20 300 ' + ' '.join(f'L{x:.1f} {y:.1f}' for x, y in pts) + f' L{20 + (n - 1) * step:.1f} 300 Z'
    body = ('<defs><linearGradient id="hs" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b1635"/><stop offset="1" stop-color="#7c3aed" stop-opacity=".5"/></linearGradient>'
            '<linearGradient id="hm" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".35" stop-color="#cfd8e6"/><stop offset="1" stop-color="#4a5878"/></linearGradient></defs>'
            f'<rect width="840" height="330" rx="14" fill="url(#hs)"/><path d="{path}" fill="url(#hm)" stroke="#0b1635" stroke-width="1.5"/>')
    bi = max(range(n), key=lambda i: wk[i]); bx, by = pts[bi]
    body += (f'<line x1="{bx}" y1="{by}" x2="{bx}" y2="{by - 34}" stroke="#fff" stroke-width="2"/><path d="M{bx} {by - 34} L{bx + 20} {by - 26} L{bx + 9} {by - 24} L{bx + 20} {by - 14} L{bx} {by - 12}Z" fill="#dc143c" stroke="#003893" stroke-width="1.5"/>'
             + label(bx, by - 42, f'your Everest week · {wk[bi]}', 11, '#ffd34a', 'middle', 'm', 700))
    body += header('🏔️ Your Himalaya', 'last 52 weeks of contributions')
    return svg(330, body, 'Your Himalaya')


# ----------------------------------------------------------------- 17 kathmandu sky
def sky(D, S):
    h = S['hour']
    if 5 <= h < 8: a, b, phase = '#f6a96b', '#6b5bb5', 'sunrise'
    elif 8 <= h < 17: a, b, phase = '#7cc4f2', '#cfeefe', 'day'
    elif 17 <= h < 19: a, b, phase = '#f08a5d', '#3b2a5c', 'sunset'
    else: a, b, phase = '#0b1635', '#1b2a6b', 'night'
    body = f'<defs><linearGradient id="sk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{b if phase != "day" else a}"/><stop offset="1" stop-color="{a if phase != "day" else b}"/></linearGradient></defs><rect width="840" height="260" rx="14" fill="url(#sk)"/>'
    if phase == 'night':
        body += ''.join(f'<circle cx="{(i * 89) % 840}" cy="{(i * 41) % 150}" r="1.4" fill="#fff" style="animation:tw 2s {i * .1:.1f}s infinite alternate"/>' for i in range(60))
        body += '<circle cx="680" cy="60" r="22" fill="#f4f1de"/><circle cx="690" cy="54" r="20" fill="#0b1635"/>'
    else:
        sy = {'sunrise': 150, 'day': 60, 'sunset': 160}[phase]
        body += f'<circle cx="640" cy="{sy}" r="34" fill="#ffd34a" opacity=".95"/><circle cx="640" cy="{sy}" r="60" fill="#ffd34a" opacity=".15"/>'
        body += ''.join(f'<ellipse cx="{150 + i * 260}" cy="{60 + i * 15}" rx="60" ry="14" fill="#fff" opacity=".7" style="animation:drift {30 + i * 10}s linear infinite"/>' for i in range(3))
    body += '<path d="M0 200 L90 120 L150 160 L240 90 L310 150 L380 110 L460 170 L560 100 L640 150 L720 115 L840 170 L840 260 L0 260Z" fill="#c9d4e5" opacity=".9"/>'
    body += '<path d="M240 90 L222 108 L240 104 L256 110Z M560 100 L544 116 L560 112 L576 118Z" fill="#fff"/>'
    city = '<path d="M0 230 '
    random.seed(3)
    x = 0
    while x < 840:
        w = random.randint(26, 50); hh = random.randint(14, 44)
        city += f'L{x} {230 - hh} L{x + w} {230 - hh} '
        x += w
    city += 'L840 260 L0 260Z" fill="#1b1f2e"/>'
    body += city
    body += '<path d="M410 230 L410 176 L420 160 L430 176 L430 230Z" fill="#2b2f40"/><path d="M402 182 L420 150 L438 182Z" fill="#c9a227"/><circle cx="420" cy="146" r="4" fill="#c9a227"/>'
    if phase == 'night':
        body += ''.join(f'<rect x="{(i * 47) % 830}" y="{232 - (i * 13) % 30}" width="4" height="5" fill="#ffd34a" opacity=".8"/>' for i in range(40))
    body += label(24, 34, '🌄 Kathmandu right now', 18, '#ffffff', weight=700) + label(W - 24, 34, f'{phase} · {dt.datetime.now(NPT):%H:%M} NPT', 13, '#ffffff', 'end', 'm')
    return svg(260, body, 'Kathmandu sky', '@keyframes tw{from{opacity:.2}to{opacity:1}}@keyframes drift{from{transform:translateX(-200px)}to{transform:translateX(900px)}}')



# ----------------------------------------------------------------- coding clock
def clock(D, S):
    hours = [0] * 24
    for when, _ in D['commits']:
        t = dt.datetime.fromisoformat(when.replace('Z', '+00:00')).astimezone(NPT); hours[t.hour] += 1
    mx = max(1, max(hours)); cx, cy, r0, r1 = 300, 210, 62, 168
    body = f'<circle cx="{cx}" cy="{cy}" r="{r1 + 8}" fill="none" stroke="#30363d"/><circle cx="{cx}" cy="{cy}" r="{r0 - 4}" fill="#161b22" stroke="#30363d"/>'
    for h in range(24):
        a = (h / 24) * 2 * math.pi - math.pi / 2; L = r0 + (r1 - r0) * hours[h] / mx
        x0, y0, x1, y1 = cx + r0 * math.cos(a), cy + r0 * math.sin(a), cx + L * math.cos(a), cy + L * math.sin(a)
        night = h >= 21 or h < 6
        col = '#b69cf7' if night else ('#ffd34a' if 6 <= h < 17 else '#ff8c42')
        body += (f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{col}" stroke-width="11" stroke-linecap="round" '
                 f'style="animation:pulse 3s ease-in-out {h * .12:.2f}s infinite alternate"/>')
        if h % 3 == 0:
            lx, ly = cx + (r1 + 22) * math.cos(a), cy + (r1 + 22) * math.sin(a)
            body += label(f'{lx:.0f}', f'{ly + 4:.0f}', f'{h:02d}', 11, DIM, 'middle', 'm')
    peak = max(range(24), key=lambda h: hours[h]); total = sum(hours)
    night_share = sum(hours[h] for h in list(range(21, 24)) + list(range(0, 6))) / max(1, total)
    day_share = sum(hours[6:17]) / max(1, total)
    kind = ('🦉 Night owl' if night_share > .35 else '🌅 Early bird' if sum(hours[5:9]) / max(1, total) > .3 else '☀️ Daytime coder' if day_share > .5 else '🌆 Evening coder')
    body += label(cx, cy - 4, f'{peak:02d}:00', 20, INK, 'middle', 'm', 700) + label(cx, cy + 16, 'peak hour', 11, DIM, 'middle')
    body += label(520, 140, kind, 26, INK, weight=800)
    body += label(520, 176, f'most active around {peak:02d}:00 Nepal time', 14, DIM)
    body += label(520, 210, f'{total} commits analysed', 14, DIM, cls='m')
    for i, (lab, share, col) in enumerate([('night 21-06', night_share, '#b69cf7'), ('day 06-17', day_share, '#ffd34a'), ('evening 17-21', 1 - night_share - day_share, '#ff8c42')]):
        y = 250 + i * 30
        body += label(520, y + 10, lab, 12, DIM, cls='m') + f'<rect x="630" y="{y}" width="170" height="12" rx="6" fill="#30363d"/><rect x="630" y="{y}" width="{max(4, 170 * share):.0f}" height="12" rx="6" fill="{col}"/>'
    body += header('⏰ Coding clock', 'when do I commit?')
    return svg(420, body, 'Coding clock', '@keyframes pulse{from{opacity:.75}to{opacity:1}}')


# ----------------------------------------------------------------- language journey
def journey(D, S):
    first = {}
    for r in D['repos']:
        L = r['primaryLanguage']
        if L and (L['name'] not in first or r['createdAt'] < first[L['name']][0]):
            first[L['name']] = (r['createdAt'], L['color'] or '#8b949e', r['name'])
    ev = sorted(first.items(), key=lambda x: x[1][0])[:12]
    if not ev:
        return svg(200, header('🗺️ Language journey', 'no data yet'), 'Language journey')
    t0 = dt.datetime.fromisoformat(ev[0][1][0].replace('Z', '+00:00')); t1 = dt.datetime.now(dt.timezone.utc); span = max(1, (t1 - t0).days)
    body = '<line x1="50" y1="200" x2="790" y2="200" stroke="#30363d" stroke-width="4" stroke-linecap="round"/>'
    for yv in range(t0.year + 1, t1.year + 1):
        x = 50 + 740 * max(0, (dt.datetime(yv, 1, 1, tzinfo=dt.timezone.utc) - t0).days) / span
        body += f'<line x1="{x:.0f}" y1="192" x2="{x:.0f}" y2="208" stroke="#30363d" stroke-width="2"/>' + label(f'{x:.0f}', 228, yv, 12, DIM, 'middle', 'm')
    for i, (name, (when, col, repo)) in enumerate(ev):
        x = 50 + 740 * (dt.datetime.fromisoformat(when.replace('Z', '+00:00')) - t0).days / span
        up = i % 2 == 0; tier = (i // 2) % 3; y = 150 - tier * 44 if up else 254 + tier * 44
        bx = min(max(x, 66), 774)
        body += (f'<g style="opacity:0;animation:show .4s {i * .25:.2f}s forwards"><line x1="{x:.0f}" y1="200" x2="{x:.0f}" y2="{y + (14 if up else -14)}" stroke="{col}" stroke-width="2"/>'
                 f'<circle cx="{x:.0f}" cy="200" r="8" fill="{col}" stroke="#0d1117" stroke-width="3"/>'
                 f'<rect x="{bx - 58:.0f}" y="{y - 14}" width="116" height="28" rx="14" fill="#161b22" stroke="{col}"/>'
                 + label(f'{bx:.0f}', y + 5, name[:14], 13, INK, 'middle', weight=700) + label(f'{bx + 64:.0f}' if bx < 700 else f'{bx - 64:.0f}', y + 4, when[:7], 10, DIM, 'start' if bx < 700 else 'end', 'm') + '</g>')
    body += header('🗺️ Language journey', 'when each language first appeared')
    return svg(400, body, 'Language journey', '@keyframes show{to{opacity:1}}')


# ----------------------------------------------------------------- commit mood
STOP = set('the a an to of and in for on with from by is be it this that at as into via update updated add added fix fixed readme md use using new feat chore docs home meow desktop source'.split())
def mood(D, S):
    msgs = [m for _, m in D['commits'] if m]
    verbs = {'feat': 0, 'fix': 0, 'chore': 0, 'docs': 0, 'refactor': 0, 'update': 0, 'other': 0}
    words = {}
    for m in msgs:
        w0 = m.split()[0].lower().rstrip(':') if m.split() else ''
        w0 = {'add': 'feat', 'added': 'feat', 'adds': 'feat', 'fixed': 'fix', 'fixes': 'fix', 'updated': 'update'}.get(w0.split('(')[0], w0)
        k = next((v for v in verbs if w0.startswith(v)), 'other'); verbs[k] += 1
        for w in ''.join(ch.lower() if ch.isalnum() else ' ' for ch in m).split():
            if len(w) > 2 and w not in STOP and not w.isdigit():
                words[w] = words.get(w, 0) + 1
    top = sorted(words.items(), key=lambda x: -x[1])[:8]; mx = max([c for _, c in top] or [1])
    body = label(40, 84, 'MOST-USED WORDS', 12, DIM, cls='m', weight=700)
    for i, (w, c) in enumerate(top):
        y = 100 + i * 30
        body += (label(40, y + 15, w[:14], 14, INK, cls='m') + f'<rect x="160" y="{y + 2}" width="230" height="16" rx="8" fill="#30363d"/>'
                 f'<rect x="160" y="{y + 2}" width="{max(8, 230 * c / mx):.0f}" height="16" rx="8" fill="url(#mg)" style="transform-origin:160px 0;animation:grow .8s {i * .08:.2f}s both"/>' + label(400, y + 15, c, 12, DIM, cls='m'))
    tot = max(1, sum(verbs.values())); cols = {'feat': '#30a46c', 'fix': '#e5484d', 'chore': '#ffd34a', 'docs': '#4cb8ff', 'refactor': '#b69cf7', 'update': '#ff8c42', 'other': '#6e7681'}
    cx, cy, R = 600, 200, 92; a0 = -math.pi / 2; body += label(470, 84, 'HOW I START COMMITS', 12, DIM, cls='m', weight=700)
    for k, v in verbs.items():
        if not v: continue
        a1 = a0 + 2 * math.pi * v / tot; large = 1 if a1 - a0 > math.pi else 0
        body += (f'<path d="M{cx} {cy} L{cx + R * math.cos(a0):.1f} {cy + R * math.sin(a0):.1f} A{R} {R} 0 {large} 1 {cx + R * math.cos(a1):.1f} {cy + R * math.sin(a1):.1f}Z" fill="{cols[k]}" stroke="#0d1117" stroke-width="2"/>')
        a0 = a1
    body += f'<circle cx="{cx}" cy="{cy}" r="50" fill="#0d1117"/>' + label(cx, cy + 6, f'{len(msgs)}', 18, INK, 'middle', 'm', 700)
    for i, k in enumerate([k for k in verbs if verbs[k]]):
        y = 110 + i * 26
        body += f'<rect x="720" y="{y - 10}" width="12" height="12" rx="3" fill="{cols[k]}"/>' + label(740, y, f'{k} {100 * verbs[k] // tot}%', 12, INK, cls='m')
    fav = max(verbs, key=lambda k: verbs[k] if k != 'other' else -1)
    body += label(40, 372, f'favourite commit type: {fav}  ·  {sum(1 for m in msgs if ":" in m.split(" ")[0])} conventional commits', 12, DIM, cls='m')
    body = '<defs><linearGradient id="mg" x1="0" x2="1"><stop offset="0" stop-color="#7c3aed"/><stop offset="1" stop-color="#00ff9c"/></linearGradient></defs>' + body
    body += header('📈 Commit mood', 'what my commit messages say')
    return svg(400, body, 'Commit mood', '@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}')


# ----------------------------------------------------------------- isometric contribution city
def city(D, S):
    days = D['days'][-364:]; mx = max(1, max(c for _, c in days))
    tw, th = 24.0, 12.0; ox, oy = 420 - (53 - 7) * 12 / 2 + 0, 120
    cells = []
    for k, (d, c) in enumerate(days):
        i, j = k // 7, k % 7
        cells.append((i + j, i, j, c, d))
    cells.sort()
    pal = [('#21262d', '#1a1f26', '#14181e'), ('#0e4429', '#0b3521', '#08281a'), ('#006d32', '#005526', '#003f1c'), ('#26a641', '#1e8434', '#176427'), ('#39d353', '#2fae45', '#258a37')]
    body = ''
    for n, (_, i, j, c, d) in enumerate(cells):
        x = ox + (i - j) * tw * 0.5
        y = oy + (i + j) * th * 0.5
        lvl = 0 if c == 0 else min(4, 1 + int(3.99 * c / mx)); top, left, right = pal[lvl]
        h = 3 if c == 0 else 8 + 110 * c / mx
        T = f'{x:.1f},{y - h:.1f} {x + tw / 2:.1f},{y - h + th / 2:.1f} {x:.1f},{y - h + th:.1f} {x - tw / 2:.1f},{y - h + th / 2:.1f}'
        L = f'{x - tw / 2:.1f},{y - h + th / 2:.1f} {x:.1f},{y - h + th:.1f} {x:.1f},{y + th:.1f} {x - tw / 2:.1f},{y + th / 2:.1f}'
        Rr = f'{x + tw / 2:.1f},{y - h + th / 2:.1f} {x:.1f},{y - h + th:.1f} {x:.1f},{y + th:.1f} {x + tw / 2:.1f},{y + th / 2:.1f}'
        anim = f' style="transform-origin:{x:.1f}px {y + th:.1f}px;animation:rise .9s cubic-bezier(.2,.9,.3,1.2) {(i * .03):.2f}s both"' if c else ''
        body += f'<g{anim}><polygon points="{L}" fill="{left}"/><polygon points="{Rr}" fill="{right}"/><polygon points="{T}" fill="{top}"/></g>'
    best = max(days, key=lambda x: x[1])
    body += header('🧩 Contribution city', f'{sum(c for _, c in days)} contributions · tallest tower {best[1]} on {best[0]}')
    return svg(560, body, 'Contribution city', '@keyframes rise{from{transform:scaleY(0)}to{transform:scaleY(1)}}')


# ----------------------------------------------------------------- light-mode versions
LIGHT = [('#21262d', '#eaeef2'), ('#1a1f26', '#d8dee4'), ('#14181e', '#c6ced6'), ('#0d1117', '#ffffff'), ('#161b22', '#f6f8fa'), ('#30363d', '#d0d7de'), ('#e6edf3', '#1f2328'), ('#7d8590', '#59636e'),
         ('#00ff9c', '#1a7f37'), ('#11161d', '#e7ebf0'), ('#ffd34a', '#bf8700'), ('#b69cf7', '#8250df')]
def lighten(text):
    for a, b in LIGHT:
        text = text.replace(a, b).replace(a.upper(), b)
    return text


ALL = [('galaxy', galaxy), ('clock', clock), ('journey', journey), ('city', city)]
HAS_LIGHT = {'clock', 'journey', 'city'}   # galaxy stays dark: it is space

if __name__ == '__main__':
    D = fetch(); S = stats(D); OUT.mkdir(exist_ok=True)
    for name, fn in ALL:
        try:
            text = fn(D, S); (OUT / f'{name}.svg').write_text(text)
            if name in HAS_LIGHT:
                (OUT / f'{name}-light.svg').write_text(lighten(text))
            print('ok', name)
        except Exception as e:  # one broken piece must not stop the others
            print('FAILED', name, e)

#!/usr/bin/env python3
"""Visitor games for the profile README: community chess, a poll, a guestbook and a daily riddle.

Visitors play by opening an issue with a pre-filled title (the README links do that). The
"interact" workflow runs this with the issue in environment variables, never on a command line:
    ISSUE_TITLE, ISSUE_BODY, ISSUE_USER, ISSUE_NUMBER, GITHUB_TOKEN, GITHUB_REPOSITORY
`python gen/interact.py --refresh` only redraws the README sections (used daily for the riddle).

Everything visitors type is cleaned before it reaches the README: no links, no HTML, no markdown, short.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
README = ROOT / 'README.md'
REPO = os.environ.get('GITHUB_REPOSITORY', 'charitraa/charitraa')
NPT = dt.timezone(dt.timedelta(hours=5, minutes=45))
BODY_HINT = 'Just press "Submit new issue". The README updates in about a minute.'


def load(name, default):
    p = DATA / name
    return json.loads(p.read_text()) if p.exists() else default


def save(name, obj):
    DATA.mkdir(exist_ok=True)
    (DATA / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False))


def link(title, body=BODY_HINT):
    return f'https://github.com/{REPO}/issues/new?title={urllib.parse.quote(title)}&body={urllib.parse.quote(body)}'


def clean(text, limit=80):
    """Visitor text -> safe plain text: no URLs, no HTML, no markdown, one short line."""
    t = (text or '').split('\n')[0]
    t = re.sub(r'https?://\S+|www\.\S+|\S+\.(com|net|org|io|xyz|ru|cn)\b\S*', '', t, flags=re.I)
    t = re.sub(r'[<>\[\]()`*_#|~\\!@]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return escape(t[:limit])


def today():
    return dt.datetime.now(NPT).date().isoformat()


def section(text, name, content):
    a, b = f'<!-- {name}:START -->', f'<!-- {name}:END -->'
    if a not in text:
        return text
    i, j = text.index(a) + len(a), text.index(b)
    return text[:i] + '\n' + content.strip() + '\n' + text[j:]


# ------------------------------------------------------------------ chess
def chess_state():
    return load('chess.json', {'fen': None, 'moves': [], 'players': {}, 'games': 0})


def chess_svg(board, last, light=False):
    import chess
    dark_sq, light_sq = ('#7c6db0', '#e8e4f6') if not light else ('#b58863', '#f0d9b5')
    hi = '#00ff9c' if not light else '#f6f669'
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="420" height="440" viewBox="0 0 420 440">',
           f'<rect width="420" height="440" rx="12" fill="{"#0d1117" if not light else "#ffffff"}"/>']
    for r in range(8):
        for c in range(8):
            sq = chess.square(c, 7 - r); x, y = 30 + c * 45, 20 + r * 45
            col = light_sq if (r + c) % 2 == 0 else dark_sq
            if last and sq in (last.from_square, last.to_square):
                col = hi
            out.append(f'<rect x="{x}" y="{y}" width="45" height="45" fill="{col}"/>')
            p = board.piece_at(sq)
            if p:
                g = p.unicode_symbol(invert_color=False)
                fill = '#ffffff' if p.color else '#111111'; stroke = '#111111' if p.color else '#ffffff'
                out.append(f'<text x="{x + 22.5}" y="{y + 35}" font-size="36" text-anchor="middle" fill="{fill}" stroke="{stroke}" stroke-width=".8" '
                           f'font-family="\'Segoe UI Symbol\',\'DejaVu Sans\',\'Apple Symbols\',sans-serif">{chess.UNICODE_PIECE_SYMBOLS[p.symbol().lower()]}</text>')
    for i in range(8):
        lc = '#7d8590'
        out.append(f'<text x="{30 + i * 45 + 22.5}" y="{20 + 8 * 45 + 18}" font-size="12" text-anchor="middle" fill="{lc}" font-family="monospace">{"abcdefgh"[i]}</text>')
        out.append(f'<text x="16" y="{20 + i * 45 + 27}" font-size="12" text-anchor="middle" fill="{lc}" font-family="monospace">{8 - i}</text>')
    out.append('</svg>')
    return ''.join(out)


def chess_render(st):
    import chess
    board = chess.Board(st['fen']) if st['fen'] else chess.Board()
    last = chess.Move.from_uci(st['moves'][-1]['uci']) if st['moves'] else None
    (ROOT / 'art').mkdir(exist_ok=True)
    (ROOT / 'art' / 'chess.svg').write_text(chess_svg(board, last))
    (ROOT / 'art' / 'chess-light.svg').write_text(chess_svg(board, last, light=True))
    white = board.turn
    names = {chess.PAWN: 'Pawn', chess.KNIGHT: 'Knight', chess.BISHOP: 'Bishop', chess.ROOK: 'Rook', chess.QUEEN: 'Queen', chess.KING: 'King'}
    icons = {'Pawn': '♙♟', 'Knight': '♘♞', 'Bishop': '♗♝', 'Rook': '♖♜', 'Queen': '♕♛', 'King': '♔♚'}
    colours = {'Pawn': '30363d', 'Knight': '7c3aed', 'Bishop': '1f6feb', 'Rook': 'bf8700', 'Queen': 'd6336c', 'King': '00a86b'}
    groups = {}
    for mv in board.legal_moves:
        groups.setdefault(names[board.piece_at(mv.from_square).piece_type], []).append((board.san(mv), mv.uci()))

    def badge(text, colour, label=None, style='for-the-badge'):
        enc = lambda s: urllib.parse.quote(s.replace('-', '--').replace('_', '__'))
        part = f'{enc(label)}-{enc(text)}' if label else enc(text)
        return f'https://img.shields.io/badge/{part}-{colour}?style={style}&labelColor=0d1117'

    rows = []
    for nm in ['Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King']:
        if nm in groups:
            icon = icons[nm][0 if white else 1]
            btns = ' '.join(f'<a href="{link("chess: move " + uci)}"><img src="{badge(f"{icon} {san}", colours[nm], style="flat-square")}" alt="{san}" height="24"/></a>'
                            for san, uci in sorted(groups[nm]))
            rows.append(f'<p align="center"><b>{nm}</b><br/>{btns}</p>')
    medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
    top = sorted(st['players'].items(), key=lambda x: -x[1])[:5]
    leaders = ' &nbsp; '.join(f'{medals[i]} <img src="https://github.com/{u}.png?size=40" width="20" height="20" alt=""/> <b>@{u}</b> ({n})'
                              for i, (u, n) in enumerate(top)) or 'nobody yet: be the first!'
    recent = ' &nbsp;·&nbsp; '.join(f'<img src="https://github.com/{m["user"]}.png?size=40" width="18" height="18" alt=""/> <code>{m["san"]}</code> by @{m["user"]}'
                                    for m in st['moves'][-4:][::-1]) or 'no moves yet'
    status = badge(f'{"⚪ White" if white else "⚫ Black"} to move · Move {board.fullmove_number}', '00ff9c' if white else '7c3aed')
    if board.is_check():
        status = badge(f'{"⚪ White" if white else "⚫ Black"} is in CHECK · Move {board.fullmove_number}', 'e5484d')
    v = f'{st["games"]}-{len(st["moves"])}'   # new URL after every move, so browsers don't show a cached board
    board_img = (f'<picture><source media="(prefers-color-scheme: light)" srcset="art/chess-light.svg?v={v}"/>'
                 f'<img src="art/chess.svg?v={v}" width="420" alt="Community chess board"/></picture>')
    stats = (f'<img src="{badge(str(len(st["moves"])), "30363d", "moves this game")}" height="22"/> '
             f'<img src="{badge(str(len(st["players"])), "30363d", "players")}" height="22"/> '
             f'<img src="{badge(str(st["games"]), "30363d", "games finished")}" height="22"/>')
    return (f'<p align="center">{board_img}</p>\n'
            f'<p align="center"><img src="{status}" height="30"/></p>\n'
            '<p align="center"><b>How to play:</b> ① click a move below &nbsp;→&nbsp; ② press <b>Submit new issue</b> &nbsp;→&nbsp; '
            '③ ⏳ <b>wait 1–2 minutes</b> and refresh: the board updates by itself.<br/>'
            '<sub>Anyone can play either colour. One move per issue. If the board looks old, press Ctrl + Shift + R.</sub></p>\n'
            + '\n'.join(rows) + '\n'
            f'<p align="center"><b>Last moves</b><br/>{recent}</p>\n'
            f'<p align="center"><b>🏆 Top players</b><br/>{leaders}</p>\n'
            f'<p align="center">{stats}</p>')


def chess_move(st, user, uci):
    import chess
    board = chess.Board(st['fen']) if st['fen'] else chess.Board()
    try:
        mv = chess.Move.from_uci(uci)
    except ValueError:
        return False, f'`{escape(uci)}` is not a move I understand.'
    if mv not in board.legal_moves:
        return False, f'`{uci}` is not legal right now (someone may have moved first). Pick a move from the README.'
    san = board.san(mv); board.push(mv)
    st['moves'].append({'uci': uci, 'san': san, 'user': user, 'date': today()})
    st['players'][user] = st['players'].get(user, 0) + 1
    msg = f'You played **{san}**. Thanks @{user}!'
    if board.is_game_over():
        msg += f' 🏁 Game over: {board.result()}. A new game has started.'
        st['games'] += 1; board = chess.Board(); st['moves'] = []
    st['fen'] = board.fen()
    return True, msg


# ------------------------------------------------------------------ poll
def poll_state():
    return load('poll.json', {'question': 'What should I build next?', 'options': [
        'NepLang 2.0: more Nepali keywords', 'More Linux fix videos on Nooe Hack', 'An open-source EducationERP demo', 'A VS Code theme in my neon colours'], 'votes': {}})


def poll_render(st):
    total = sum(len(v) for v in st['votes'].values())
    lines = [f'**{escape(st["question"])}** ({total} vote{"s" if total != 1 else ""})\n', '| Option | Votes | |', '|---|---|---|']
    for i, opt in enumerate(st['options'], 1):
        n = len(st['votes'].get(str(i), [])); pct = n * 100 // max(1, total)
        bar = '▰' * (pct // 10) + '▱' * (10 - pct // 10)
        lines.append(f'| {i}. {escape(opt)} | `{bar}` {pct}% ({n}) | [vote]({link(f"poll: vote {i}")}) |')
    return '\n'.join(lines) + '\n\nOne vote per GitHub account; voting again moves your vote.'


def poll_vote(st, user, n):
    if not 1 <= n <= len(st['options']):
        return False, 'That option does not exist.'
    for k in st['votes']:
        st['votes'][k] = [u for u in st['votes'][k] if u != user]
    st['votes'].setdefault(str(n), []).append(user)
    return True, f'Vote counted for **{escape(st["options"][n - 1])}**. Thanks @{user}!'


# ------------------------------------------------------------------ guestbook
def guestbook_render(st):
    rows = []
    for e in st[-10:][::-1]:
        rows.append(f'| <img src="https://github.com/{e["user"]}.png?size=40" width="32" height="32" alt=""/> | @{e["user"]} | {e["msg"]} | {e["date"]} |')
    table = '| | Visitor | Message | Date |\n|---|---|---|---|\n' + '\n'.join(rows) if rows else '_No signatures yet. Be the first!_'
    return (table + f'\n\n**[✍️ Sign the guestbook]({link("guestbook: sign", "Write your message on the first line (max 80 characters). Links and formatting are removed.")})** '
            f'· {len(st)} signature{"s" if len(st) != 1 else ""} so far')


def guestbook_sign(st, user, body):
    msg = clean(body, 80)
    if not msg or msg.lower().startswith('write your message'):
        return False, 'Your message was empty. Write it on the first line of the issue body.'
    st[:] = [e for e in st if e['user'] != user]
    st.append({'user': user, 'msg': msg, 'date': today()})
    return True, f'Signed! Thanks @{user} 🙏'


# ------------------------------------------------------------------ daily riddle
RIDDLES = [
    ('I have keys but open no locks, I have space but no room. What am I?', ['keyboard']),
    ('The more of me you take, the more you leave behind. What am I?', ['footsteps', 'steps', 'footstep']),
    ('I am 404 when you need me most. What am I, in two words?', ['page not found', 'not found']),
    ('I run but never walk, I have a head but no hair, and in code I go from top to bottom. What am I?', ['program', 'script', 'code']),
    ('I am the only bug that every developer wants: I make your code shorter by deleting me. What am I?', ['comment', 'dead code']),
    ('Divide me in two and I become a byte\'s half. How many bits am I?', ['8', 'eight']),
    ('I can be pushed and pulled, I have branches but no leaves. What am I?', ['git', 'repo', 'repository', 'git repository']),
    ('I am always coming but never arrive. Developers promise to fix bugs in me. What am I?', ['tomorrow']),
    ('What has a neck but no head, and holds the water a coder drinks at 2 AM?', ['bottle', 'water bottle']),
    ('I go up and down but never move. Programmers climb me in the stack. What am I?', ['stairs', 'staircase']),
    ('What 3-letter word means "to make code run faster" and also what a cat does with milk?', ['lap']),
    ('I am an array that forgot how many items I hold, so you call me before you loop. Which method gives my size in Python?', ['len', 'len()']),
    ('Forward I am heavy, backward I am not. What am I?', ['ton']),
    ('I have cities, but no houses; forests, but no trees; and water, but no fish. What am I?', ['map']),
    ('What starts with "e", ends with "e", and contains one letter? (Hint: you send it.)', ['envelope']),
    ('I am the number that is its own square and its own cube, and every boolean "true". What am I?', ['1', 'one']),
    ('In Nepal I am the highest; in Git I am the latest commit. What word links us?', ['top', 'head', 'summit', 'peak']),
    ('What can you catch but never throw, unless you are using try?', ['exception', 'cold', 'error']),
    ('I am binary for 2 and the start of every infinite loop of laughter. Write me in binary.', ['10']),
    ('What gets wetter the more it dries?', ['towel']),
    ('I have no life, but I can die; I have no lungs, but I need air. What am I?', ['fire']),
]


def riddle_state():
    return load('riddle.json', {'date': None, 'index': -1, 'today': [], 'fame': {}, 'yesterday': None})


def riddle_roll(st):
    d = today()
    if st['date'] == d:
        return
    if st['index'] >= 0:
        st['yesterday'] = {'q': RIDDLES[st['index']][0], 'a': RIDDLES[st['index']][1][0], 'solvers': len(st['today'])}
    st['date'] = d; st['index'] = dt.date.fromisoformat(d).toordinal() % len(RIDDLES); st['today'] = []


def riddle_render(st):
    q = RIDDLES[st['index']][0]
    out = (f'> 🎯 **Today\'s riddle ({st["date"]}):** {escape(q)}\n\n'
           f'**[💡 Answer it]({link("riddle: answer ", "Type your answer at the end of the issue title, after riddle: answer")})** '
           f'(type your answer after `riddle: answer` in the title) · solved today by {len(st["today"])}')
    if st['today']:
        out += ': ' + ' '.join(f'@{u}' for u in st['today'][-8:])
    if st.get('yesterday'):
        y = st['yesterday']
        out += f'\n\nYesterday\'s answer: <details><summary>reveal</summary>{escape(y["a"])} (solved by {y["solvers"]})</details>'
    top = sorted(st['fame'].items(), key=lambda x: -x[1])[:5]
    out += f'\n\n🏆 **Hall of fame:** {" · ".join(f"@{u} ({n})" for u, n in top) or "nobody yet"}'
    return out


def riddle_answer(st, user, guess):
    g = re.sub(r'[^a-z0-9 ]', '', (guess or '').lower()).strip()
    if user in st['today']:
        return True, 'You already solved today\'s riddle. Come back tomorrow!'
    ok = any(g == re.sub(r'[^a-z0-9 ]', '', a.lower()) for a in RIDDLES[st['index']][1])
    if ok:
        st['today'].append(user); st['fame'][user] = st['fame'].get(user, 0) + 1
        return True, f'✅ Correct, @{user}! You\'re on today\'s solver list.'
    return False, f'❌ Not quite. Try again with a new issue. (Your guess: `{escape(g[:40])}`)'


# ------------------------------------------------------------------ main
def render_all():
    text = README.read_text()
    text = section(text, 'CHESS', chess_render(chess_state()))
    text = section(text, 'POLL', poll_render(poll_state()))
    text = section(text, 'GUESTBOOK', guestbook_render(load('guestbook.json', [])))
    README.write_text(text)


def reply(number, body):
    tok = os.environ.get('GITHUB_TOKEN')
    if not (tok and number):
        print('reply:', body); return
    h = {'Authorization': 'bearer ' + tok, 'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-games'}
    base = f'https://api.github.com/repos/{REPO}/issues/{number}'
    for url, data, method in [(base + '/comments', {'body': body + f'\n\n[⬅ Back to the profile](https://github.com/{REPO.split("/")[0]})'}, 'POST'),
                              (base, {'state': 'closed', 'state_reason': 'completed'}, 'PATCH')]:
        urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(data).encode(), headers=h, method=method), timeout=30)


def handle():
    title = (os.environ.get('ISSUE_TITLE') or '').strip(); user = re.sub(r'[^A-Za-z0-9-]', '', os.environ.get('ISSUE_USER') or '')[:39]
    body = os.environ.get('ISSUE_BODY') or ''; number = os.environ.get('ISSUE_NUMBER')
    m = re.match(r'^(chess)\s*:\s*(.*)$', title, re.I)   # poll, guestbook and riddle were removed on 2026-11-06
    if not m or not user:
        return  # not a game issue: leave it alone
    game, rest = m.group(1).lower(), m.group(2).strip()
    ok, msg = False, 'I did not understand that. Use the links in the README.'
    if game == 'chess':
        mm = re.match(r'^move\s+([a-h][1-8][a-h][1-8][qrbn]?)$', rest, re.I)
        if mm:
            st = chess_state(); ok, msg = chess_move(st, user, mm.group(1).lower())
            if ok: save('chess.json', st)
    elif game == 'poll':
        mm = re.match(r'^vote\s+(\d+)$', rest, re.I)
        if mm:
            st = poll_state(); ok, msg = poll_vote(st, user, int(mm.group(1)))
            if ok: save('poll.json', st)
    elif game == 'guestbook':
        st = load('guestbook.json', []); ok, msg = guestbook_sign(st, user, body)
        if ok: save('guestbook.json', st)
    elif game == 'riddle':
        mm = re.match(r'^answer\s*(.*)$', rest, re.I)
        st = riddle_state(); riddle_roll(st)
        ok, msg = riddle_answer(st, user, mm.group(1) if mm else '')
        save('riddle.json', st)
    render_all()
    reply(number, msg)


if __name__ == '__main__':
    if '--refresh' in sys.argv:
        render_all()
    else:
        handle()

"""Regenerate ogp.png (2400x1260) from index.html.

Usage:  python3 tools/ogp/build.py
Card numbers, logos, and status labels are read from the DATA array in
index.html; the per-card detail rows and chain tags below are maintained here.
Requires Google Chrome (override the path with the CHROME env var).
"""
import html, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROME = os.environ.get('CHROME', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')

CARDS = [
    ('Collector Crypt', [('チェーン', 'Solana'), ('買い戻し', '85〜93%')]),
    ('Courtyard.io', [('チェーン', 'Polygon'), ('決済', 'クレカ対応')]),
    ('Beezie', [('チェーン', 'Solana'), ('ARR', '$142M')]),
    ('Monster', [('チェーン', 'MegaETH'), ('買い戻し', '85%')]),
    ('PACKS', [('チェーン', 'Base'), ('開示', 'フルオンチェーン')]),
    ('DYLI', [('チェーン', 'Base'), ('決済', 'USDC')]),
]
CHAINS = ['Solana', 'Base', 'Polygon', 'BNB Chain', 'MegaETH', 'Arbitrum', 'Abstract', 'Monad', 'Robinhood Chain']


def load_entries():
    s = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    a = s.index('var DATA = [')
    body = s[a:s.index('\n  ];', a)]
    entries = {}
    for e in re.split(r'(?=\{no:"\d+",name:")', body):
        m = re.match(r'\{no:"(\d+)",name:"([^"]+)"', e)
        if not m:
            continue
        logo = re.search(r'logo:"(data:[^"]+)"', e)
        status = re.search(r'statusLabel:"([^"]+)"', e)
        entries[m.group(2)] = {'no': m.group(1), 'logo': logo and logo.group(1), 'status': status.group(1)}
    return entries


def card_html(d, name, rows):
    logo = (f'<img class="logo" src="{d["logo"]}" alt="">' if d['logo']
            else f'<span class="logo initial">{html.escape(name[0])}</span>')
    rows_html = ''.join(f'<div class="mrow"><span class="k">{html.escape(k)}</span>'
                        f'<span class="v">{html.escape(v)}</span></div>' for k, v in rows)
    return (f'<div class="card"><div class="no">FILE.{d["no"]}</div>'
            f'<div class="row">{logo}<div class="nm">{html.escape(name)}</div></div>'
            f'<div class="pill">{html.escape(d["status"])}</div>'
            f'<div class="meta">{rows_html}</div></div>')


CSS = """
  :root{ --bg:#F6F3EF; --surface:#FFFFFF; --ink:#1D1730; --ink-soft:#564E6E; --ink-faint:#8B839C;
    --line:#E2DCD2; --line-strong:#CBC2B4; --accent:#D9691E; --accent-ink:#9A4A12; --mint:#0E8F72; --mint-soft:#DCF3EC; }
  *{ box-sizing:border-box; margin:0; padding:0; }
  html,body{ width:1200px; height:630px; overflow:hidden; }
  body{ background:var(--bg); color:var(--ink); position:relative;
    font-family:'Hiragino Sans','Hiragino Kaku Gothic ProN','Yu Gothic','Noto Sans JP',sans-serif; -webkit-font-smoothing:antialiased; }
  .leftbg{ position:absolute; inset:0 auto 0 0; width:565px;
    background:radial-gradient(520px 360px at 8% 0%, hsl(262 84% 58% / .13), transparent 70%),
               radial-gradient(420px 300px at 70% 105%, hsl(262 84% 58% / .07), transparent 70%); }
  .rightbg{ position:absolute; inset:0 0 0 565px;
    background:radial-gradient(560px 380px at 100% 0%, hsl(20 90% 52% / .08), transparent 70%), #F4F0EA; }
  .wrap{ position:relative; z-index:2; height:100%; display:flex; }
  .left{ width:565px; flex:none; padding:64px 0 52px 66px; display:flex; flex-direction:column; justify-content:space-between; }
  .eyebrow{ display:inline-flex; align-items:center; gap:12px; align-self:flex-start;
    font-family:ui-monospace,'SF Mono',Menlo,monospace; font-size:17px; font-weight:700; letter-spacing:.16em;
    color:var(--accent-ink); background:rgba(255,255,255,.75); border:1.5px solid var(--line-strong);
    border-radius:999px; padding:10px 22px 10px 16px; }
  .dot{ width:12px; height:12px; border-radius:50%; background:var(--mint); box-shadow:0 0 0 4px var(--mint-soft); }
  h1{ font-size:70px; font-weight:900; line-height:1.16; letter-spacing:-.01em; margin-top:34px; }
  .holo{ background:linear-gradient(100deg, var(--accent) 0%, var(--mint) 30%, var(--accent) 55%, #E9B64A 75%, var(--accent) 100%);
    background-size:280% 100%; background-position:30% 0; -webkit-background-clip:text; background-clip:text; color:transparent; }
  .lede{ font-size:21px; line-height:1.62; color:var(--ink-soft); margin-top:24px; }
  .lede b{ color:var(--ink); font-weight:800; }
  .tags{ display:flex; flex-wrap:wrap; gap:8px; margin-top:26px; max-width:499px; }
  .tag{ font-family:ui-monospace,'SF Mono',Menlo,monospace; font-size:14px; color:var(--ink-soft);
    border:1.5px solid var(--line-strong); border-radius:999px; padding:5px 12px; background:rgba(255,255,255,.7); }
  .url{ font-family:ui-monospace,'SF Mono',Menlo,monospace; font-size:20px; letter-spacing:.06em; color:var(--ink-faint); }
  .url b{ color:var(--accent-ink); font-weight:700; }
  .right{ flex:1; position:relative; overflow:hidden; }
  .deck{ position:absolute; top:-70px; left:50px; display:grid; grid-template-columns:repeat(2,232px); gap:18px;
    transform:rotate(-6deg); transform-origin:top left; }
  .card{ background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:16px 16px 14px;
    box-shadow:0 1px 2px rgba(20,20,20,.05), 0 18px 36px -18px rgba(20,20,20,.35); }
  .card:nth-child(even){ margin-top:-34px; }
  .card .no{ font-family:ui-monospace,'SF Mono',Menlo,monospace; font-size:11px; font-weight:700; color:var(--accent-ink); letter-spacing:.06em; }
  .card .row{ display:flex; align-items:center; gap:10px; margin-top:9px; }
  .card .logo{ width:30px; height:30px; border-radius:8px; flex:none; object-fit:cover; border:1px solid var(--line); background:#fff; }
  .card .initial{ display:flex; align-items:center; justify-content:center; font-weight:800; color:var(--accent-ink); }
  .card .nm{ font-size:16px; font-weight:800; line-height:1.2; }
  .card .pill{ display:inline-block; margin-top:11px; font-size:10.5px; font-weight:700; padding:3px 10px; border-radius:999px;
    background:var(--mint-soft); color:var(--mint); }
  .card .meta{ margin-top:11px; padding-top:9px; border-top:1px dashed var(--line-strong); display:flex; flex-direction:column; gap:5px; }
  .card .mrow{ display:flex; gap:8px; font-size:11.5px; }
  .card .mrow .k{ color:var(--ink-faint); width:54px; flex:none; font-weight:700; }
  .card .mrow .v{ color:var(--ink); }
  .fade{ position:absolute; inset:0; pointer-events:none;
    background:linear-gradient(to top, #F4F0EA 0%, transparent 16%), linear-gradient(to bottom, #F4F0EA 0%, transparent 9%); }
"""


def build_html(entries):
    missing = [n for n, _ in CARDS if n not in entries]
    if missing:
        sys.exit(f'not in DATA: {missing}')
    cards = ''.join(card_html(entries[n], n, rows) for n, rows in CARDS)
    tags = ''.join(f'<span class="tag">{html.escape(c)}</span>' for c in CHAINS)
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="leftbg"></div><div class="rightbg"></div>
<div class="wrap">
  <div class="left">
    <div>
      <div class="eyebrow"><span class="dot"></span>ON-CHAIN TCG DIRECTORY</div>
      <h1>オンチェーン<br><span class="holo">トレカ図鑑</span></h1>
      <p class="lede">オンチェーンの<b>オリパ／ガチャ</b>を、<br>同じものさしで横断比較。</p>
      <div class="tags">{tags}</div>
    </div>
    <div class="url">onchaintcg<b>.xyz</b></div>
  </div>
  <div class="right"><div class="deck">{cards}</div><div class="fade"></div></div>
</div></body></html>'''


def main():
    page = build_html(load_entries())
    out = os.path.join(ROOT, 'ogp.png')
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, 'ogp.html')
        open(src, 'w', encoding='utf-8').write(page)
        subprocess.run([CHROME, '--headless', '--disable-gpu', '--no-sandbox', '--hide-scrollbars',
                        '--force-device-scale-factor=2', '--window-size=1200,630', '--virtual-time-budget=3000',
                        f'--screenshot={out}', f'file://{src}'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()

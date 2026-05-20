"""Build pending.html — review page for picks with rework notes + needs-update slides.

Standalone /report-style page deployed alongside the picker page.
"""
import json, html, datetime, os

esc = html.escape

ROOT = '/Users/steven/Documents/Claude/sea-voice-iterate'
fz = json.load(open(f'{ROOT}/finalized.json'))
pending = [e for e in fz['finalized'] if e.get('rework_note')]
needs_update = fz.get('needs_update', [])

# Pull idea title + variant subtitle from data files
def slide_title(sid):
    p = f'{ROOT}/data/{sid}/full.json'
    if not os.path.exists(p): return ''
    try:
        return json.load(open(p)).get('title', '')
    except Exception:
        return ''

def variant_iterated_vo(sid, vid):
    p = f'{ROOT}/data/{sid}/full.json'
    if not os.path.exists(p): return ''
    d = json.load(open(p))
    for g in ['hormozi', 'garyvee']:
        for s in d.get(g, {}).get('scripts', []):
            if s.get('id') == vid:
                return s.get('iterated_vo', '')
    return ''

TS = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

# Sidebar nav
nav_items = []
for i, e in enumerate(pending, 1):
    nav_items.append(f'<a href="#p{i}" class="nav-item nav-rework"><span class="nav-num">{i}</span><span class="nav-id">{esc(e["slide_id"])}</span><span class="nav-label">{esc(e["variant_id"])} · rework</span></a>')
for j, sid in enumerate(needs_update, len(pending) + 1):
    nav_items.append(f'<a href="#p{j}" class="nav-item nav-flag"><span class="nav-num">{j}</span><span class="nav-id">{esc(sid)}</span><span class="nav-label">full regen</span></a>')

# Body sections
sections = []
for i, e in enumerate(pending, 1):
    title = slide_title(e['slide_id'])
    sections.append(f'''
<section id="p{i}" class="panel">
  <div class="panel-num">{i:02d}</div>
  <div class="panel-body">
    <div class="meta-row">
      <span class="tag">REWORK</span>
      <span class="meta-id">{esc(e['slide_id'])} · {esc(e['variant_id'])}</span>
      <span class="meta-version">{esc(e['version'])}</span>
      <span class="meta-hook">hook: {esc(e['hook_label'])}</span>
    </div>
    <h2>{esc(title or e.get('subtitle',''))}</h2>
    <div class="subtitle">{esc(e.get('subtitle',''))}</div>

    <div class="block">
      <div class="block-label">Steven's note</div>
      <div class="rework-note">{esc(e['rework_note'])}</div>
    </div>

    <div class="block">
      <div class="block-label">Current draft ({e['word_count']} words)</div>
      <p class="vo">{esc(e['final_vo'])}</p>
    </div>
  </div>
</section>''')

for j, sid in enumerate(needs_update, len(pending) + 1):
    title = slide_title(sid)
    sections.append(f'''
<section id="p{j}" class="panel">
  <div class="panel-num">{j:02d}</div>
  <div class="panel-body">
    <div class="meta-row">
      <span class="tag tag-flag">FULL REGEN</span>
      <span class="meta-id">{esc(sid)}</span>
      <span class="meta-version">all 10 variants</span>
    </div>
    <h2>{esc(title)}</h2>
    <div class="subtitle">Steven flagged this idea — none of the 10 variants fit. Generate a fresh set with different hooks and bodies.</div>

    <div class="block">
      <div class="block-label">Action</div>
      <p class="vo">Re-run hormozi + garyvee voice generation for this idea. New hooks (avoid the angles already attempted). New iterated_vo. Same factcheck topic.</p>
    </div>
  </div>
</section>''')

CSS = """
:root {
  --ink: #0a0a0a;
  --ink-soft: #3a3a3a;
  --ink-mute: #6a6a6a;
  --line: #d8d8d8;
  --line-s: #ececec;
  --bg: #fff;
  --tint: #f7f7f5;
  --serif: ui-serif, "New York", "Iowan Old Style", Georgia, serif;
  --mono: "JetBrains Mono", ui-monospace, Menlo, monospace;
  --sans: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter", sans-serif;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--bg); color: var(--ink); font-family: var(--sans); -webkit-font-smoothing: antialiased; }
.layout { display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; max-width: 1400px; margin: 0 auto; }

.sidebar { position: sticky; top: 0; height: 100vh; border-right: 1px solid var(--line); padding: 28px 20px 28px 32px; overflow-y: auto; }
.sb-kicker { font-family: var(--mono); font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink-mute); margin-bottom: 6px; }
.sb-title { font-size: 17px; font-weight: 700; letter-spacing: -0.01em; margin-bottom: 4px; }
.sb-meta { font-family: var(--mono); font-size: 10px; color: var(--ink-mute); margin-bottom: 24px; }
.sb-nav { display: flex; flex-direction: column; gap: 1px; }
.nav-item { display: grid; grid-template-columns: 28px 1fr; gap: 8px; padding: 8px 10px;
  border: 1px solid transparent; border-radius: 5px; text-decoration: none; color: var(--ink-soft);
  font-size: 12px; transition: all 0.15s; align-items: baseline; }
.nav-item:hover { border-color: var(--line); background: var(--tint); color: var(--ink); }
.nav-num { font-family: var(--mono); font-size: 10px; color: var(--ink-mute); }
.nav-id { font-family: var(--mono); font-size: 11px; font-weight: 600; color: var(--ink); }
.nav-label { font-size: 10px; color: var(--ink-mute); font-family: var(--mono); text-transform: uppercase; letter-spacing: 0.04em; grid-column: 2; }
.nav-rework .nav-id { color: var(--ink); }
.nav-flag .nav-id { color: var(--ink); }

.main { padding: 60px 56px 120px; }
.hero { padding-bottom: 32px; border-bottom: 1px solid var(--line); margin-bottom: 48px; }
.kicker { font-family: var(--mono); font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink-mute); margin-bottom: 14px; }
h1 { font-size: 36px; line-height: 1.15; letter-spacing: -0.022em; font-weight: 600; margin: 0 0 12px; }
.lede { font-size: 16px; color: var(--ink-soft); line-height: 1.55; max-width: 720px; }
.stats { display: flex; gap: 36px; margin-top: 28px; }
.stat-block { display: flex; flex-direction: column; gap: 4px; }
.stat-num { font-family: var(--serif); font-size: 32px; font-weight: 500; letter-spacing: -0.01em; }
.stat-label { font-family: var(--mono); font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-mute); }

.panel { display: grid; grid-template-columns: 60px 1fr; gap: 24px; padding: 36px 0; border-bottom: 1px solid var(--line-s); }
.panel:last-child { border-bottom: none; }
.panel-num { font-family: var(--mono); font-size: 12px; color: var(--ink-mute); letter-spacing: 0.04em; padding-top: 6px; }
.panel-body { min-width: 0; }

.meta-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: baseline; margin-bottom: 10px; }
.tag { font-family: var(--mono); font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-mute); font-weight: 700;
  padding: 3px 8px; border: 1px solid var(--ink-mute); border-radius: 100px; }
.tag-flag { color: var(--ink); border-color: var(--ink); }
.meta-id { font-family: var(--mono); font-size: 12px; font-weight: 700; color: var(--ink); letter-spacing: 0.04em; }
.meta-version, .meta-hook { font-family: var(--mono); font-size: 10px; color: var(--ink-mute); letter-spacing: 0.04em; text-transform: uppercase; }

h2 { font-size: 22px; line-height: 1.25; letter-spacing: -0.012em; font-weight: 600; margin: 0 0 4px; }
.subtitle { font-size: 13px; color: var(--ink-soft); font-style: italic; margin-bottom: 22px; line-height: 1.5; }

.block { margin-bottom: 20px; }
.block-label { font-family: var(--mono); font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-mute); font-weight: 700; margin-bottom: 8px; }
.rework-note { font-family: var(--serif); font-size: 15px; line-height: 1.55; color: var(--ink);
  padding: 14px 18px; background: var(--tint); border-left: 3px solid var(--ink); border-radius: 0 6px 6px 0; }
.vo { font-family: var(--serif); font-size: 15px; line-height: 1.65; color: var(--ink-soft); margin: 0;
  padding: 14px 18px; border: 1px solid var(--line-s); border-radius: 6px; background: var(--bg); }

@media (max-width: 900px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar { position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--line); padding: 24px; }
  .main { padding: 32px 24px 80px; }
  .panel { grid-template-columns: 1fr; gap: 12px; }
  .panel-num { padding-top: 0; }
  h1 { font-size: 26px; }
  .stats { gap: 24px; }
  .stat-num { font-size: 26px; }
}
"""

HTML_PAGE = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex,nofollow">
<title>SEA Batch 1 — Pending Review</title>
<style>{CSS}</style>
</head>
<body>
<div class="layout">
  <nav class="sidebar">
    <div class="sb-kicker">/spark_script · pending</div>
    <div class="sb-title">SEA Batch 1 — Pending Review</div>
    <div class="sb-meta">{TS}</div>
    <div class="sb-nav">{''.join(nav_items)}</div>
  </nav>
  <main class="main">
    <div class="hero">
      <div class="kicker">Sparkloop · /spark_script · review queue</div>
      <h1>Pending review</h1>
      <p class="lede">Picks with rework notes and ideas flagged for full regeneration. Finalized scripts (no notes, no flags) live in the Google Doc.</p>
      <div class="stats">
        <div class="stat-block"><div class="stat-num">{len(pending)}</div><div class="stat-label">Rework notes</div></div>
        <div class="stat-block"><div class="stat-num">{len(needs_update)}</div><div class="stat-label">Full regen</div></div>
        <div class="stat-block"><div class="stat-num">{len(pending) + len(needs_update)}</div><div class="stat-label">Total pending</div></div>
      </div>
    </div>
    {''.join(sections)}
  </main>
</div>
</body>
</html>
"""

with open(f'{ROOT}/pending.html', 'w') as f:
    f.write(HTML_PAGE)

print(f"Built pending.html: {len(pending)} rework + {len(needs_update)} full-regen")

"""SEA Voice Iterate — original → polish iteration + fact-check engine."""
import json, html, os, glob, re

DATA_DIR = '/Users/steven/Documents/Claude/sea-voice-iterate/data'
OUT = '/Users/steven/Documents/Claude/sea-voice-iterate/index.html'


def esc(s):
    return html.escape(str(s or ''))


def render_diff(markup):
    """Convert <del>...</del> and <ins>...</ins> markers in agent output to safe HTML.
    Agent output may contain raw < > so we sanitize everything else."""
    if not markup:
        return ''
    # Replace markers with placeholders, escape, then restore
    placeholders = {}
    counter = [0]
    def stash(match):
        tag = match.group(1)
        content = match.group(2)
        key = f"__DIFF_{counter[0]}__"
        counter[0] += 1
        placeholders[key] = (tag, content)
        return key
    s = re.sub(r'<(del|ins)>(.*?)</\1>', stash, markup, flags=re.DOTALL)
    s = html.escape(s)
    for key, (tag, content) in placeholders.items():
        css_class = 'diff-del' if tag == 'del' else 'diff-ins'
        s = s.replace(key, f'<span class="{css_class}">{html.escape(content)}</span>')
    return s


def _normalize_script(s):
    """Some agents used variant_id/variant_name instead of id/subtitle. Normalize."""
    if 'id' not in s and 'variant_id' in s:
        s['id'] = s['variant_id']
    if 'subtitle' not in s and 'variant_name' in s:
        s['subtitle'] = s['variant_name']
    return s


def load_hooks(slide_id):
    """Load the 5 trigger-distinct hooks for a slide. Returns list or []."""
    path = os.path.join(os.path.dirname(__file__), 'hooks', f'{slide_id}.json')
    if not os.path.exists(path):
        return []
    try:
        return json.load(open(path)).get('hooks', [])
    except Exception:
        return []


def render_hook_palette(slide_id):
    hooks = load_hooks(slide_id)
    if not hooks:
        return ''
    opts = []
    for h in hooks:
        trig = h.get('trigger', '')
        txt = h.get('text', '')
        label = trig.replace('_', ' ').title()
        opts.append(
            f'<label class="hook-opt">'
            f'<input type="radio" name="hookpick-{esc(slide_id)}" class="hkp" '
            f'data-slide="{esc(slide_id)}" data-trigger="{esc(trig)}" data-text="{esc(txt)}">'
            f'<span class="hk-mark"></span>'
            f'<span class="hk-body"><span class="hk-trigger">{esc(label)}</span>'
            f'<span class="hk-text">{esc(txt)}</span></span></label>'
        )
    return (
        '<details class="hook-palette" open>'
        '<summary>Hook palette · 5 scroll-stop alternates for this idea '
        '<span class="hk-hint">(if a variant\'s own hook doesn\'t land, pick one of these)</span></summary>'
        '<div class="hook-opts">' + ''.join(opts) + '</div>'
        '</details>'
    )


def load_slide_data(slide_id):
    """Load per-slide combined JSON. Returns (hormozi, garyvee, factcheck) tuple or (None, None, {})."""
    path = os.path.join(DATA_DIR, slide_id, 'full.json')
    if not os.path.exists(path):
        return None, None, {}
    try:
        d = json.load(open(path))
        h = d.get('hormozi') or {}
        g = d.get('garyvee') or {}
        if h.get('scripts'):
            h['scripts'] = [_normalize_script(s) for s in h['scripts']]
        if g.get('scripts'):
            g['scripts'] = [_normalize_script(s) for s in g['scripts']]
        return h or None, g or None, d.get('factcheck', {})
    except Exception:
        return None, None, {}


# My ratings on the iterated (brand-polished) versions
def _rate(s, a, p, note):
    return {'social': s, 'audience': a, 'sales': p, 'overall': round((s+a+p)/3, 1), 'note': note}

RATINGS = {
    'PH1': _rate(4.2, 4.0, 4.3, "'This is not a fee problem. This is a hidden margin problem.' is a strong reframe line. Clean PAS rhythm intact after polish."),
    'PH2': _rate(4.5, 4.2, 4.3, "Compounding maths (1.2K → 28.8K/yr → 144K/5yr) lands hard. 'A salary. A warehouse. Your kid's college fund.' = concrete stakes."),
    'PH3': _rate(4.4, 3.9, 4.3, "Accusation opener is visceral. 'You signed off on it' might still feel slightly attacking — close to the line for SEA register."),
    'PH4': _rate(4.1, 4.1, 4.2, "'The fee is not the fee' = sharp reframe. 'Banks make billions' is a broad claim that could draw pushback."),
    'PH5': _rate(4.3, 4.1, 4.2, "1-2-3 structural reveal works well. Listing what you saw vs didn't see is clean teaching."),
    'PG1': _rate(4.0, 4.1, 4.2, "Lost some of the original Gary Vee punch after polish. Still works but feels closer to baseline."),
    'PG2': _rate(4.3, 4.1, 4.2, "'Your bank is the most expensive part of your supply chain' is the sharpest single line in this batch. Tight at 97 words."),
    'PG3': _rate(4.0, 4.2, 4.2, "Hammer/wood analogy is plain English and lands. 'Use the right tool for the job' is generic but clean."),
    'PG4': _rate(4.2, 4.1, 4.0, "'Your bank doesn't make money on the wire fee. They make money on the exchange rate.' = the kind of line a peer would quote. CTA soft — no explicit 'Search WorldFirst'."),
    'PG5': _rate(4.4, 4.3, 4.2, "Call-the-bank scenario is the most relatable in the batch. 'You sleep' close is a strong payoff line."),
}


def render_script(script_id, subtitle, original_vo, iterated_vo, diff_markup, skill_name='', factcheck=None, rating=None, rank=None, slide_id=''):
    diff_html = render_diff(diff_markup) if diff_markup else esc(iterated_vo)

    heat_pill = ''
    fc_note_text = ''
    if factcheck:
        heat = factcheck.get('red_flag', 'Low')
        heat_class = f"heat-{heat.lower()}"
        heat_tooltip = esc(factcheck.get('analysis', ''))
        heat_pill = f'<span class="heat-pill {heat_class}" title="{heat_tooltip}"><span class="hl">Heat</span><span class="hv">{esc(heat)}</span></span>'
        fc_note_text = factcheck.get('analysis', '')

    rating_row = ''
    if rating:
        rating_row = f'''
    <div class="rating-row">
      <span class="rp social"><span class="rl">Soc</span><span class="rv">{rating.get('social', '-')}</span></span>
      <span class="rp audience"><span class="rl">Aud</span><span class="rv">{rating.get('audience', '-')}</span></span>
      <span class="rp sales"><span class="rl">Sales</span><span class="rv">{rating.get('sales', '-')}</span></span>
      <span class="overall"><span class="rl">Overall</span><span class="rv">{rating.get('overall', '-')}</span></span>
      {heat_pill}
    </div>
    <p class="rating-note">{esc(rating.get('note', ''))}</p>'''

    factcheck_block = ''
    if factcheck:
        comments = factcheck.get('skeptic_comments', [])
        comment_items = []
        for c in comments:
            # Handle both old string format and new {text, severity} format
            if isinstance(c, str):
                text = c
                severity = 'mid'
            else:
                text = c.get('text', '')
                severity = c.get('severity', 'mid')
            comment_items.append(f'<li class="sc-{severity}"><span class="sc-mark"></span><span class="sc-text">{esc(text)}</span></li>')
        comments_html = '\n'.join(comment_items)
        factcheck_block = f'''
  <div class="factcheck-block">
    <div class="fc-head">
      <span class="block-label">Skeptic test · what a Malaysian SMB might push back on</span>
    </div>
    <p class="fc-note">{esc(fc_note_text)}</p>
    <div class="skeptic-comments">
      <ul>{comments_html}</ul>
    </div>
  </div>'''

    rank_chip = f'<span class="rank-chip">#{rank}</span>' if rank else ''

    return f'''
<article class="script-card" data-script-id="{esc(script_id)}">
  <header class="script-head">
    <div class="script-row">
      {rank_chip}
      <span class="script-id">{esc(script_id)}</span>
      <span class="skill-tag">{esc(skill_name)}</span>
      <span class="word-count">{len(iterated_vo.split())} words</span>
    </div>
    <p class="script-subtitle">{esc(subtitle)}</p>
    {rating_row}
  </header>

  <div class="cols">
    <div class="col original">
      <div class="block-label">Pure original</div>
      <p class="vo vo-original">{esc(original_vo)}</p>
    </div>
    <div class="col iterated">
      <div class="block-label">Brand-polish iteration <span class="legend"><span class="diff-del">deleted</span> / <span class="diff-ins">added</span></span></div>
      <p class="vo vo-iterated">{diff_html}</p>
    </div>
  </div>

  {factcheck_block}

  <div class="actions">
    <label class="winner-radio">
      <input type="radio" name="winner-{esc(slide_id)}" class="wr" data-slide="{esc(slide_id)}" data-vid="{esc(script_id)}">
      <span class="winner-mark"></span>
      <span class="winner-label">Pick this for {esc(slide_id)}</span>
    </label>
    <button class="copy-btn" data-vo="{esc(iterated_vo)}" type="button">Copy polished</button>
  </div>

  <textarea class="script-comment" data-slide="{esc(slide_id)}" data-vid="{esc(script_id)}" placeholder="Comment on this variant. What's working? What needs to change?"></textarea>
</article>'''


def render_combined_section(hormozi, garyvee, factcheck, slide_id=''):
    """Merge all scripts, sort by Claude overall desc, render single list."""
    all_scripts = []
    if hormozi:
        for s in hormozi.get('scripts', []):
            all_scripts.append((s, hormozi['skill']))
    if garyvee:
        for s in garyvee.get('scripts', []):
            all_scripts.append((s, garyvee['skill']))

    def overall_score(item):
        s, _ = item
        r = RATINGS.get(s['id'])
        return r['overall'] if r else 0

    all_scripts.sort(key=overall_score, reverse=True)

    scripts_html = '\n'.join(
        render_script(
            s['id'],
            s.get('subtitle', ''),
            s.get('original_vo', ''),
            s.get('iterated_vo', ''),
            s.get('diff_markup', ''),
            skill_name=skill,
            factcheck=factcheck.get(s['id']),
            rating=RATINGS.get(s['id']),
            rank=i + 1,
            slide_id=slide_id,
        )
        for i, (s, skill) in enumerate(all_scripts)
    )
    return f'''
<section class="combined-section">
  <div class="scripts-stack">
    {scripts_html}
  </div>
</section>'''


# Slideshow config — one entry per produced idea from the SEA brand channel batch
# Loaded from slides.json (generated from picks_v3_enriched.json)
SLIDES_PATH = os.path.join(os.path.dirname(__file__), 'slides.json')
try:
    SLIDES_RAW = json.load(open(SLIDES_PATH))
except Exception:
    SLIDES_RAW = []

# Normalize keys to match what the rendering loop expects
SLIDES = []
for s in SLIDES_RAW:
    slide_id = s['slide_id']
    has_data = os.path.exists(os.path.join(DATA_DIR, slide_id, 'full.json'))
    SLIDES.append({
        'id': slide_id,
        'card_id': s['card_id'],
        'title': s['video_title'],
        'card_title': s.get('card_title', ''),
        'approach': s.get('approach', ''),
        'pillar': s.get('pillar', ''),
        'topic': s.get('topic', ''),
        'format_spec': s.get('format_spec', ''),
        'has_data': has_data,
    })

slides_with_data = sum(1 for s in SLIDES if s['has_data'])
total_scripts = slides_with_data * 10

pending_banner = ''
if slides_with_data < len(SLIDES):
    pending_banner = f'<div class="pending-banner"><strong>Producing…</strong> {slides_with_data} of {len(SLIDES)} slides ready ({total_scripts} scripts so far). Page rebuilds as each agent lands.</div>'

import json as _json_mod
json_slide_meta = _json_mod.dumps([{'id': s['id'], 'title': s['title']} for s in SLIDES])


HTML_PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>SEA Voice Iterate — original → polish + fact check</title>
<style>
:root {{
  --bg: #ffffff;
  --ink: #1d1d1f;
  --ink-soft: #424245;
  --ink-mute: #6e6e73;
  --line: #d2d2d7;
  --line-soft: #e8e8ed;
  --tint: #f5f5f7;
  --pick: #0a6d2f;
  --del: #b03060;
  --ins: #0a6d2f;
  --flag-low: #6e6e73;
  --flag-medium: #946100;
  --flag-high: #b03060;
  --social: #1a6dcc;
  --audience: #946100;
  --product: #b03060;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background: var(--bg); color: var(--ink);
  font-family: -apple-system, "SF Pro Text", "Helvetica Neue", sans-serif;
  font-size: 16px; line-height: 1.55; -webkit-font-smoothing: antialiased; }}

.wrap {{ max-width: 1400px; margin: 0 auto; padding: 50px 50px 220px; }}

/* Slideshow nav */
.slide-nav {{ position: sticky; top: 0; z-index: 50; background: var(--bg);
  display: grid; grid-template-columns: 48px 1fr 48px; gap: 14px; align-items: center;
  padding: 14px 20px; border: 1px solid var(--line); border-radius: 100px;
  margin: 20px 0 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); }}
.nav-btn {{ width: 44px; height: 44px; border-radius: 50%; border: 1px solid var(--line);
  background: var(--bg); color: var(--ink); font-size: 18px; cursor: pointer;
  transition: all 0.15s; display: flex; align-items: center; justify-content: center; }}
.nav-btn:hover:not(:disabled) {{ background: var(--ink); color: #fff; border-color: var(--ink); }}
.nav-btn:disabled {{ opacity: 0.3; cursor: not-allowed; }}
.slide-info {{ display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; justify-content: center; }}
.slide-counter {{ font-family: var(--mono); font-size: 11px; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--ink-mute); font-weight: 600;
  padding: 4px 10px; border: 1px solid var(--line); border-radius: 100px; }}
.slide-id {{ font-family: var(--mono); font-size: 13px; font-weight: 700;
  letter-spacing: 0.04em; color: var(--ink); }}
.slide-title {{ font-size: 14px; color: var(--ink-soft); font-weight: 500; }}

.slide-meta {{ display: flex; gap: 14px; flex-wrap: wrap;
  font-family: var(--mono); font-size: 11px; color: var(--ink-mute);
  letter-spacing: 0.04em; margin-bottom: 24px; padding-bottom: 16px;
  border-bottom: 1px solid var(--line-soft); }}

.slide-pending {{ padding: 40px 30px; border: 1px dashed var(--line); border-radius: 8px;
  background: var(--tint); text-align: center; }}
.slide-pending strong {{ display: block; font-size: 15px; margin-bottom: 8px; color: var(--ink); }}
.slide-pending p {{ font-size: 13px; color: var(--ink-soft); max-width: 520px;
  margin: 0 auto; line-height: 1.55; }}

/* Hook palette */
.hook-palette {{ border: 1px solid var(--pick); border-radius: 10px;
  background: rgba(10,109,47,0.035); margin-bottom: 26px; overflow: hidden; }}
.hook-palette > summary {{ cursor: pointer; padding: 14px 20px; font-weight: 600;
  font-size: 14px; color: var(--ink); user-select: none; list-style: none; }}
.hook-palette > summary::-webkit-details-marker {{ display: none; }}
.hook-palette > summary::before {{ content: '▸ '; color: var(--pick); }}
.hook-palette[open] > summary::before {{ content: '▾ '; }}
.hk-hint {{ font-weight: 400; font-size: 12px; color: var(--ink-mute); font-style: italic; }}
.hook-opts {{ padding: 4px 16px 16px; display: flex; flex-direction: column; gap: 6px; }}
.hook-opt {{ display: grid; grid-template-columns: 20px 1fr; gap: 12px;
  align-items: start; padding: 11px 14px; border: 1px solid var(--line);
  border-radius: 8px; cursor: pointer; background: var(--bg); transition: all 0.12s; }}
.hook-opt:hover {{ border-color: var(--pick); }}
.hook-opt input {{ position: absolute; opacity: 0; }}
.hk-mark {{ width: 16px; height: 16px; border: 2px solid var(--line);
  border-radius: 50%; margin-top: 3px; position: relative; transition: all 0.12s; }}
.hook-opt input:checked ~ .hk-mark {{ border-color: var(--pick); }}
.hook-opt input:checked ~ .hk-mark::after {{ content: ''; width: 8px; height: 8px;
  border-radius: 50%; background: var(--pick); position: absolute; top: 2px; left: 2px; }}
.hook-opt input:checked ~ .hk-body {{ }}
.hook-opt:has(input:checked) {{ border-color: var(--pick); background: rgba(10,109,47,0.05); }}
.hk-body {{ display: flex; flex-direction: column; gap: 3px; }}
.hk-trigger {{ font-family: var(--mono); font-size: 10px; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--pick); font-weight: 700; }}
.hk-text {{ font-size: 14.5px; line-height: 1.5; color: var(--ink);
  font-family: ui-serif, "New York", "Iowan Old Style", Georgia, serif; }}

.hero {{ padding-bottom: 28px; border-bottom: 1px solid var(--line); margin-bottom: 40px; }}
.kicker {{ font-family: var(--mono); font-size: 11px; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--ink-mute); margin-bottom: 12px; }}
h1 {{ font-size: 30px; line-height: 1.18; letter-spacing: -0.02em; font-weight: 600; margin-bottom: 12px; }}
.lede {{ font-size: 16px; color: var(--ink-soft); max-width: 760px; line-height: 1.55; }}
.pending-banner {{ margin-top: 18px; padding: 12px 18px; border: 1px solid var(--line);
  border-radius: 6px; background: var(--tint); font-size: 13px; color: var(--ink-soft); }}

.skill-section {{ margin-bottom: 60px; }}
.skill-head {{ padding-bottom: 14px; border-bottom: 1px solid var(--ink); margin-bottom: 26px; }}
.skill-head h2 {{ font-size: 22px; font-weight: 700; letter-spacing: -0.01em; }}
.skill-blurb {{ font-size: 13px; color: var(--ink-soft); margin-top: 4px; font-style: italic; }}

.scripts-stack {{ display: flex; flex-direction: column; gap: 28px; }}

.script-card {{ border: 1px solid var(--line); border-radius: 10px; padding: 0; overflow: hidden;
  background: var(--bg); transition: border-color 0.15s, box-shadow 0.15s; }}
.script-card.winner {{ border-color: var(--pick); box-shadow: 0 0 0 2px rgba(10,109,47,0.1); }}

.script-head {{ padding: 16px 22px 14px; background: var(--tint); border-bottom: 1px solid var(--line-soft); }}
.script-row {{ display: flex; gap: 10px; align-items: baseline; margin-bottom: 4px; flex-wrap: wrap; }}
.rank-chip {{ font-family: var(--mono); font-size: 12px; font-weight: 700; color: var(--pick);
  padding: 2px 8px; border: 1px solid var(--pick); border-radius: 100px; letter-spacing: 0.04em; }}
.script-id {{ font-family: var(--mono); font-size: 14px; font-weight: 700; letter-spacing: 0.06em; }}
.skill-tag {{ font-family: var(--mono); font-size: 10px; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--ink-mute); padding: 2px 8px;
  border: 1px solid var(--line); border-radius: 100px; }}
.word-count {{ font-family: var(--mono); font-size: 11px; color: var(--ink-mute); margin-left: auto; }}
.script-subtitle {{ font-size: 13px; color: var(--ink-soft); font-style: italic; margin-bottom: 12px; }}

/* Inline rating row in header */
.script-head .rating-row {{ display: flex; gap: 6px; align-items: baseline; flex-wrap: wrap; margin: 0; }}
.script-head .rating-note {{ font-size: 12px; color: var(--ink-soft); font-style: italic; line-height: 1.5; margin-top: 8px; padding: 0; }}

/* Heat pill */
.heat-pill {{ display: inline-flex; align-items: baseline; gap: 4px; padding: 2px 8px;
  border-radius: 100px; font-family: var(--mono); font-weight: 600;
  border: 1px solid currentColor; margin-left: 4px; cursor: help; }}
.heat-pill .hl {{ font-size: 9px; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.8; }}
.heat-pill .hv {{ font-size: 10px; }}
.heat-low {{ color: var(--flag-low); background: rgba(110,110,115,0.06); }}
.heat-medium {{ color: var(--flag-medium); background: rgba(148,97,0,0.08); }}
.heat-high {{ color: var(--flag-high); background: rgba(176,48,96,0.08); }}

.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; border-bottom: 1px solid var(--line-soft); }}
.col {{ padding: 18px 22px; }}
.col.original {{ border-right: 1px solid var(--line-soft); background: rgba(0,0,0,0.012); }}
.col.iterated {{ background: rgba(10,109,47,0.025); }}

.block-label {{ font-family: var(--mono); font-size: 10px; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--ink-mute); font-weight: 600; margin-bottom: 10px;
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }}
.legend {{ font-family: var(--mono); font-size: 9px; letter-spacing: 0.06em;
  text-transform: none; color: var(--ink-mute); }}
.legend .diff-del, .legend .diff-ins {{ padding: 0 4px; border-radius: 3px; }}

.vo {{ font-size: 14.5px; line-height: 1.65; color: var(--ink);
  font-family: ui-serif, "New York", "Iowan Old Style", Georgia, serif;
  letter-spacing: 0.005em; }}
.vo-original {{ color: var(--ink-soft); }}
.diff-del {{ text-decoration: line-through; color: var(--del); background: rgba(176,48,96,0.08); padding: 0 2px; border-radius: 2px; }}
.diff-ins {{ color: var(--ins); background: rgba(10,109,47,0.12); padding: 0 2px; border-radius: 2px; font-weight: 500; }}

/* Rating chips (used inline in header now) */
.rp {{ display: inline-flex; align-items: baseline; gap: 3px; padding: 2px 7px;
  border-radius: 100px; font-family: var(--mono); font-weight: 600; }}
.rp .rl {{ font-size: 9px; letter-spacing: 0.06em; text-transform: uppercase; opacity: 0.85; }}
.rp .rv {{ font-size: 10px; }}
.rp.social {{ background: rgba(26,109,204,0.13); color: var(--social); }}
.rp.audience {{ background: rgba(148,97,0,0.13); color: var(--audience); }}
.rp.sales {{ background: rgba(176,48,96,0.13); color: var(--product); }}
.overall {{ display: inline-flex; align-items: baseline; gap: 4px; padding: 2px 8px;
  margin-left: 4px; padding-left: 10px; border-left: 1px solid var(--line);
  font-family: var(--mono); font-weight: 700; color: var(--ink); }}
.overall .rl {{ font-size: 9px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-mute); font-weight: 600; }}
.overall .rv {{ font-size: 13px; }}

.factcheck-block {{ padding: 14px 22px; border-bottom: 1px solid var(--line-soft);
  background: rgba(176,48,96,0.03); }}
.fc-head {{ margin-bottom: 8px; }}
.fc-note {{ font-size: 12.5px; color: var(--ink-soft); line-height: 1.55; margin-bottom: 10px; font-style: italic; }}
.skeptic-comments {{ margin-top: 8px; }}
.sc-label {{ font-family: var(--mono); font-size: 9px; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--ink-mute); margin-bottom: 6px; font-weight: 600; }}
.skeptic-comments ul {{ list-style: none; padding-left: 0; }}
.skeptic-comments li {{ font-size: 13px; line-height: 1.5;
  padding: 7px 12px 7px 14px; border-left: 3px solid; background: rgba(0,0,0,0.018);
  border-radius: 0 4px 4px 0; margin-bottom: 4px; font-style: italic;
  display: grid; grid-template-columns: 14px 1fr; gap: 8px; align-items: start; }}
.sc-mark {{ width: 8px; height: 8px; border-radius: 50%; margin-top: 6px; }}
.sc-text {{ }}
.skeptic-comments li.sc-high {{ border-left-color: var(--flag-high); background: rgba(176,48,96,0.06); color: var(--ink); }}
.skeptic-comments li.sc-high .sc-mark {{ background: var(--flag-high); }}
.skeptic-comments li.sc-high .sc-text {{ color: var(--ink); font-weight: 500; }}
.skeptic-comments li.sc-mid {{ border-left-color: var(--flag-medium); color: var(--ink-soft); }}
.skeptic-comments li.sc-mid .sc-mark {{ background: var(--flag-medium); opacity: 0.6; }}
.skeptic-comments li.sc-low {{ border-left-color: var(--line); color: var(--ink-mute); }}
.skeptic-comments li.sc-low .sc-mark {{ background: var(--ink-mute); opacity: 0.4; }}

.actions {{ padding: 14px 22px; display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }}
.winner-radio {{ position: relative; display: inline-flex; align-items: center; gap: 8px; cursor: pointer; font-size: 12px; color: var(--ink-soft); font-family: var(--mono); letter-spacing: 0.04em; }}
.winner-radio input {{ position: absolute; opacity: 0; }}
.winner-mark {{ width: 18px; height: 18px; border: 2px solid var(--line); border-radius: 50%; background: var(--bg); position: relative; transition: all 0.15s; }}
.winner-radio input:checked ~ .winner-mark {{ border-color: var(--pick); }}
.winner-radio input:checked ~ .winner-mark::after {{ content: ''; display: block; width: 10px; height: 10px; border-radius: 50%; background: var(--pick); position: absolute; top: 2px; left: 2px; }}
.winner-radio input:checked ~ .winner-label {{ color: var(--pick); font-weight: 600; }}
.copy-btn {{ padding: 7px 14px; background: var(--bg); border: 1px solid var(--line); border-radius: 100px;
  font-family: var(--mono); font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--ink-mute); cursor: pointer; }}
.copy-btn:hover {{ color: var(--ink); border-color: var(--ink); }}
.copy-btn.copied {{ background: var(--pick); color: #fff; border-color: var(--pick); }}

.script-comment {{ width: calc(100% - 44px); margin: 0 22px 18px; padding: 9px 12px;
  border: 1px solid var(--line); border-radius: 6px; font-family: inherit; font-size: 13px;
  line-height: 1.5; resize: vertical; min-height: 50px; background: var(--bg); }}
.script-comment:focus {{ outline: 1px solid var(--ink); border-color: var(--ink); }}
.script-comment::placeholder {{ color: rgba(0,0,0,0.32); }}

.bottom-panel {{ position: fixed; bottom: 0; left: 0; right: 0; background: var(--ink); color: #fff;
  z-index: 100; box-shadow: 0 -2px 16px rgba(0,0,0,0.18); }}
.bottom-panel.collapsed .panel-body {{ display: none; }}
.panel-bar {{ display: flex; align-items: center; justify-content: space-between;
  padding: 14px 22px; cursor: pointer; gap: 12px; min-height: 56px; }}
.panel-count {{ font-size: 14px; font-weight: 500; }}
.panel-count .count-zero {{ color: #888; font-weight: 400; }}
.panel-toggle {{ font-family: var(--mono); font-size: 11px; color: #aaa;
  text-transform: uppercase; letter-spacing: 0.05em; }}
.panel-body {{ padding: 6px 22px 18px; max-height: 60vh; overflow-y: auto; }}
.panel-label {{ display: block; font-family: var(--mono); font-size: 10px; color: #aaa;
  text-transform: uppercase; letter-spacing: 0.06em; margin: 10px 0 6px; }}
.panel-prompt {{ width: 100%; min-height: 200px; padding: 14px;
  border: 1px solid rgba(255,255,255,0.15); border-radius: 6px;
  background: rgba(255,255,255,0.05); color: #fff; font-family: var(--mono);
  font-size: 12px; line-height: 1.55; resize: vertical; white-space: pre-wrap; box-sizing: border-box; }}
.panel-actions {{ display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }}
.panel-btn {{ padding: 11px 18px; border-radius: 8px; font-size: 13px;
  font-weight: 500; cursor: pointer; border: none; min-height: 44px; font-family: inherit; }}
.btn-copy {{ background: #fff; color: #111; }}
.btn-copy.copied {{ background: var(--pick); color: #fff; }}

@media (max-width: 1000px) {{
  .cols {{ grid-template-columns: 1fr; }}
  .col.original {{ border-right: none; border-bottom: 1px solid var(--line-soft); }}
}}
@media (max-width: 700px) {{
  .wrap {{ padding: 32px 18px 200px; }}
  h1 {{ font-size: 22px; }}
}}
</style>
</head>
<body>
<div class="wrap">

<div class="hero">
  <div class="kicker">Sparkloop · /spark_script · per-idea slideshow</div>
  <h1>Pick one voice per produced idea</h1>
  <p class="lede">Each produced idea from /spark_produce becomes a slide. Inside the slide: 10 voice variants (Hormozi PAS ×5 + Gary Vee ×5, each with brand-polish iteration showing surgical strikethrough + insertion), Claude rating, Heat metric, and severity-tagged skeptic comments. Pick one variant per slide. Last pick wraps Sparkloop.</p>
</div>

<!-- Slideshow nav -->
<div class="slide-nav">
  <button class="nav-btn" id="prevBtn" title="Previous idea (←)">←</button>
  <div class="slide-info">
    <span class="slide-counter" id="slideCounter">Idea 1 of {len(SLIDES)}</span>
    <span class="slide-id" id="slideId">{esc(SLIDES[0]['id'])}</span>
    <span class="slide-title" id="slideTitle">{esc(SLIDES[0]['title'])}</span>
  </div>
  <button class="nav-btn" id="nextBtn" title="Next idea (→)">→</button>
</div>

<div class="slides-container">
  {chr(10).join(
    f'<div class="slide" data-slide-id="{esc(s["id"])}" data-slide-idx="{i}" style="display:{ "block" if i == 0 else "none"};">'
    + f'<div class="slide-meta"><span class="sm-card">Card {esc(s["card_id"])}</span><span class="sm-pillar">Pillar {esc(s["pillar"])}</span><span class="sm-format">{esc(s["format_spec"])}</span><span class="sm-topic">Topic {esc(s["topic"])}</span><span class="sm-approach">{esc(s["approach"])}</span></div>'
    + render_hook_palette(s['id'])
    + (
        (lambda data: render_combined_section(data[0], data[1], data[2], slide_id=s['id']) if data[0] and data[1] else f'<div class="slide-pending"><strong>Voice variants pending generation.</strong><p>Agent for {esc(s["id"])} is still running. Page rebuilds as each lands.</p></div>')(load_slide_data(s['id']))
    )
    + '</div>'
    for i, s in enumerate(SLIDES)
  )}
</div>

</div>

<div class="bottom-panel collapsed" id="panel">
  <div class="panel-bar" id="panelBar">
    <div class="panel-count" id="panelCount"><span class="count-zero">0 picked · 0 comments</span></div>
    <div class="panel-toggle" id="panelToggle">expand ↑</div>
  </div>
  <div class="panel-body">
    <span class="panel-label">Voice iterate paste-back</span>
    <textarea class="panel-prompt" id="panelPrompt" readonly></textarea>
    <div class="panel-actions">
      <button class="panel-btn btn-copy" id="btnCopy">Copy prompt</button>
    </div>
  </div>
</div>

<script>
const STORAGE_KEY = 'sea_voice_iterate_v2';
const TOTAL_SLIDES = {len(SLIDES)};
function loadState() {{
  try {{ return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{"picks":{{}},"comments":{{}}}}'); }}
  catch (e) {{ return {{picks: {{}}, comments: {{}}}}; }}
}}
function saveState(s) {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); }}
let state = loadState();
if (!state.picks) state.picks = {{}};
if (!state.comments) state.comments = {{}};

// Hydrate per-slide picks (state.picks = {{ slideId: scriptId }})
document.querySelectorAll('.wr').forEach(rb => {{
  const slide = rb.getAttribute('data-slide');
  const vid = rb.getAttribute('data-vid');
  if (state.picks[slide] === vid) {{ rb.checked = true; rb.closest('.script-card').classList.add('winner'); }}
}});
// Hydrate per-slide comments (key = slide::scriptId)
document.querySelectorAll('.script-comment').forEach(ta => {{
  const key = ta.getAttribute('data-slide') + '::' + ta.getAttribute('data-vid');
  if (state.comments[key]) ta.value = state.comments[key];
}});

document.querySelectorAll('.wr').forEach(rb => {{
  rb.addEventListener('change', () => {{
    const slide = rb.getAttribute('data-slide');
    const vid = rb.getAttribute('data-vid');
    state.picks[slide] = vid;
    // Clear winner class only within THIS slide, then mark the chosen card
    const slideEl = rb.closest('.slide');
    if (slideEl) slideEl.querySelectorAll('.script-card').forEach(c => c.classList.remove('winner'));
    rb.closest('.script-card').classList.add('winner');
    saveState(state); updatePanel();
  }});
}});
document.querySelectorAll('.script-comment').forEach(ta => {{
  ta.addEventListener('input', () => {{
    const key = ta.getAttribute('data-slide') + '::' + ta.getAttribute('data-vid');
    if (ta.value.trim()) state.comments[key] = ta.value; else delete state.comments[key];
    saveState(state); updatePanel();
  }});
}});
// Hook palette picks (state.hookpick = {{ slideId: {{trigger, text}} }})
if (!state.hookpick) state.hookpick = {{}};
document.querySelectorAll('.hkp').forEach(rb => {{
  const slide = rb.getAttribute('data-slide');
  const trig = rb.getAttribute('data-trigger');
  if (state.hookpick[slide] && state.hookpick[slide].trigger === trig) rb.checked = true;
  rb.addEventListener('change', () => {{
    state.hookpick[slide] = {{ trigger: trig, text: rb.getAttribute('data-text') }};
    saveState(state); updatePanel();
  }});
}});
document.querySelectorAll('.copy-btn').forEach(btn => {{
  btn.addEventListener('click', async (e) => {{
    e.stopPropagation();
    const vo = btn.getAttribute('data-vo');
    try {{ await navigator.clipboard.writeText(vo); btn.textContent = 'Copied'; btn.classList.add('copied');
      setTimeout(() => {{ btn.textContent = 'Copy polished'; btn.classList.remove('copied'); }}, 1500);
    }} catch (e) {{ console.error(e); }}
  }});
}});

function buildPrompt() {{
  const lines = ['== SEA Voice Iterate paste-back =='];
  lines.push('');
  const pickEntries = Object.entries(state.picks).filter(([k, v]) => v);
  lines.push(`PICKS (${{pickEntries.length}} of ${{TOTAL_SLIDES}} slides):`);
  if (pickEntries.length === 0) lines.push('  (none yet)');
  // Order picks by slide order in the DOM, append chosen hook if swapped
  document.querySelectorAll('.slide').forEach(sl => {{
    const sid = sl.getAttribute('data-slide-id');
    if (state.picks[sid]) {{
      let line = `  ${{sid}} -> ${{state.picks[sid]}}`;
      const hp = state.hookpick && state.hookpick[sid];
      if (hp) line += ` · HOOK[${{hp.trigger}}]: "${{hp.text}}"`;
      lines.push(line);
    }}
  }});
  const commentEntries = Object.entries(state.comments).filter(([k, v]) => (v || '').trim());
  lines.push('');
  lines.push(`COMMENTS (${{commentEntries.length}}):`);
  if (commentEntries.length === 0) lines.push('  (none)');
  commentEntries.forEach(([key, c]) => {{ lines.push(`  ${{key}}: "${{c.trim()}}"`); }});
  lines.push('');
  lines.push('Action: each picked variant per slide = the final script for that produced idea. Comments = rework notes.');
  return lines.join('\\n');
}}
function updatePanel() {{
  const p = Object.keys(state.picks).filter(k => state.picks[k]).length;
  const c = Object.values(state.comments).filter(v => (v || '').trim()).length;
  const ctx = document.getElementById('panelCount');
  if (p === 0 && c === 0) {{ ctx.innerHTML = '<span class="count-zero">0 of ' + TOTAL_SLIDES + ' slides picked · 0 comments</span>'; }}
  else {{ ctx.textContent = `${{p}} of ${{TOTAL_SLIDES}} slides picked · ${{c}} comments`; }}
  document.getElementById('panelPrompt').value = buildPrompt();
}}
const panel = document.getElementById('panel');
document.getElementById('panelBar').addEventListener('click', () => {{
  panel.classList.toggle('collapsed');
  document.getElementById('panelToggle').textContent = panel.classList.contains('collapsed') ? 'expand ↑' : 'collapse ↓';
}});
document.getElementById('btnCopy').addEventListener('click', async () => {{
  const text = document.getElementById('panelPrompt').value;
  try {{ await navigator.clipboard.writeText(text); const btn = document.getElementById('btnCopy');
    btn.textContent = 'Copied'; btn.classList.add('copied');
    setTimeout(() => {{ btn.textContent = 'Copy prompt'; btn.classList.remove('copied'); }}, 1500);
  }} catch (e) {{ console.error(e); }}
}});
updatePanel();

// ========== SLIDESHOW NAVIGATION ==========
const slides = document.querySelectorAll('.slide');
const totalSlides = slides.length;
let currentSlide = 0;

const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const slideCounter = document.getElementById('slideCounter');
const slideIdEl = document.getElementById('slideId');
const slideTitleEl = document.getElementById('slideTitle');

const SLIDE_META = {json_slide_meta};

function showSlide(idx) {{
  if (idx < 0 || idx >= totalSlides) return;
  slides.forEach((s, i) => {{ s.style.display = i === idx ? 'block' : 'none'; }});
  currentSlide = idx;
  slideCounter.textContent = `Idea ${{idx + 1}} of ${{totalSlides}}`;
  const meta = SLIDE_META[idx];
  if (meta) {{
    slideIdEl.textContent = meta.id;
    slideTitleEl.textContent = meta.title;
  }}
  prevBtn.disabled = idx === 0;
  nextBtn.disabled = idx === totalSlides - 1;
  window.scrollTo({{top: 0, behavior: 'smooth'}});
}}

prevBtn.addEventListener('click', () => showSlide(currentSlide - 1));
nextBtn.addEventListener('click', () => showSlide(currentSlide + 1));

document.addEventListener('keydown', (e) => {{
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
  if (e.key === 'ArrowLeft') {{ e.preventDefault(); showSlide(currentSlide - 1); }}
  if (e.key === 'ArrowRight') {{ e.preventDefault(); showSlide(currentSlide + 1); }}
}});

showSlide(0);

</script>
</body>
</html>
'''

with open(OUT, 'w') as f:
    f.write(HTML_PAGE)

print(f"Built: {OUT}")
print(f"Slides with data: {slides_with_data} of {len(SLIDES)}")
print(f"Total scripts: {total_scripts}")

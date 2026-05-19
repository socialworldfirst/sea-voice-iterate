"""Generate the final script doc from finalized.json → docx → Google Doc."""
import json, subprocess, os, datetime

fz = json.load(open('finalized.json'))
entries = fz['finalized']

md = [
    f"# SEA Brand Channel Batch 1 — Final Scripts",
    "",
    f"**Updated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
    f"**Source:** Sparkloop /spark_script · {fz['source']}",
    f"**Status:** {len(entries)} of 24 wrapped",
    f"**Voice:** WorldFirst brand channel · no em-dashes · brand-search CTA",
    "",
    "---",
    "",
]

for i, e in enumerate(entries, 1):
    md.append(f"## {i}. {e['video_title']}")
    md.append("")
    md.append(f"`{e['slide_id']}` · `{e['card_id']}` · base: {e['base_pick']} · {e['word_count']} words (~{round(e['word_count']/2.5)}s)")
    md.append("")
    if e.get('rework_note'):
        md.append(f"*Note: {e['rework_note']}*")
        md.append("")
    md.append("**VO:**")
    md.append("")
    md.append(e['final_vo'])
    md.append("")
    md.append("---")
    md.append("")

md_text = "\n".join(md)
with open('_final_scripts.md', 'w') as f:
    f.write(md_text)

# Convert to docx
subprocess.run(['/opt/homebrew/bin/pandoc', '_final_scripts.md', '-o',
                'SEA_Batch1_Final_Scripts.docx', '--from', 'markdown', '--to', 'docx'], check=True)
print(f"Built docx: {len(entries)} scripts")

"""Generate the final script doc from finalized.json → docx → Google Doc."""
import json, subprocess, os, datetime

fz = json.load(open('finalized.json'))
all_entries = fz['finalized']
# Only CLEAN picks (no rework note) go into the Google Doc. Picks with notes + needs-update flags go to pending.html.
entries = [e for e in all_entries if not e.get('rework_note')]
pending_count = len(all_entries) - len(entries)
needs_update = fz.get('needs_update', [])

md = [
    f"# SEA Brand Channel Batch 1 — Final Scripts",
    "",
    f"**Updated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
    f"**Source:** Sparkloop /spark_script · {fz['source']}",
    f"**Status:** {len(entries)} scripts finalized · {pending_count + len(needs_update)} pending review (see pending.html)",
    f"**Voice:** WorldFirst brand channel · no em-dashes · brand-search CTA",
    "",
    "---",
    "",
]

for i, e in enumerate(entries, 1):
    md.append(f"## {i}. {e['slide_id']} - {e.get('subtitle','')}")
    md.append("")
    meta = [
        f"`{e['slide_id']}::{e['variant_id']}`",
        f"version: **{e['version']}**",
        f"hook: **{e['hook_label']}**",
        f"{e['word_count']} words (~{round(e['word_count']/2.5)}s)",
    ]
    md.append(" · ".join(meta))
    md.append("")
    if e.get('rework_note'):
        md.append(f"> **Rework note:** {e['rework_note']}")
        md.append("")
    md.append("**VO:**")
    md.append("")
    md.append(e['final_vo'])
    md.append("")
    md.append("---")
    md.append("")

# Needs-update + rework-note picks moved to pending.html. Don't include them here.

md_text = "\n".join(md)
with open('_final_scripts.md', 'w') as f:
    f.write(md_text)

# Convert to docx
subprocess.run(['/opt/homebrew/bin/pandoc', '_final_scripts.md', '-o',
                'SEA_Batch1_Final_Scripts.docx', '--from', 'markdown', '--to', 'docx'], check=True)
print(f"Built docx: {len(entries)} scripts + {len(needs_update)} needs-update")


# --- Auto upload + convert to Google Doc ---
import urllib.request, time
cfg = json.loads(subprocess.run(['/opt/homebrew/bin/rclone','config','dump'],capture_output=True,text=True).stdout)
tok = json.loads(cfg['gdrive']['token'])['access_token']
DEST = "gdrive:Video Scripts/SEA Brand Channel/Batch 1 FINAL/"
ts = str(int(time.time()))
tmp = f"SEA_Batch1_tmp_{ts}.docx"
subprocess.run(['cp','SEA_Batch1_Final_Scripts.docx',tmp],check=True)
subprocess.run(['/opt/homebrew/bin/rclone','copy',tmp,DEST,'--no-traverse'],check=True)
docx_id = json.loads(subprocess.run(['/opt/homebrew/bin/rclone','lsjson',DEST+tmp],capture_output=True,text=True).stdout)[0]['ID']
body = json.dumps({"name":"SEA_Batch1_Final_Scripts","mimeType":"application/vnd.google-apps.document"}).encode()
res = json.load(urllib.request.urlopen(urllib.request.Request(
    f"https://www.googleapis.com/drive/v3/files/{docx_id}/copy", data=body,
    headers={"Authorization":f"Bearer {tok}","Content-Type":"application/json"}, method="POST")))
new_doc = res['id']
old = open('.final_doc_id').read().strip() if os.path.exists('.final_doc_id') else ''
for fid in [x for x in (docx_id, old) if x]:
    try: urllib.request.urlopen(urllib.request.Request(f"https://www.googleapis.com/drive/v3/files/{fid}",headers={"Authorization":f"Bearer {tok}"},method="DELETE"))
    except Exception: pass
open('.final_doc_id','w').write(new_doc)
url = f"https://docs.google.com/document/d/{new_doc}/edit"
open('/tmp/sea_final_doc_url.txt','w').write(url)
subprocess.run(['rm','-f',tmp])
print(f"Doc: {url}")

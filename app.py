import os, sqlite3, subprocess, uuid
from datetime import datetime, date
from pathlib import Path
from flask import Flask, request, redirect, url_for, flash, render_template_string, send_from_directory

APP_DIR = Path(__file__).parent
DATA_DIR = Path(os.getenv("DATA_DIR", APP_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "clips"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
DB = DATA_DIR / "agent.db"

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-before-deploy")

PAGE = """
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClipPilot AI</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0b1020;color:#e8edf8;font:15px Arial,sans-serif}
header{padding:22px max(20px,calc((100% - 1100px)/2));background:#111a31;border-bottom:1px solid #26334f}
main{max-width:1100px;margin:24px auto;padding:0 18px}.muted{color:#9eacc7}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px}
.card{background:#121c33;border:1px solid #273653;border-radius:14px;padding:17px;margin-bottom:16px}
h1{font-size:23px;margin:0 0 5px}h2{font-size:18px;margin:0 0 14px}
input,select,textarea{width:100%;padding:11px;border-radius:8px;border:1px solid #344462;background:#0b1428;color:#fff;margin:5px 0 12px}
button,.btn{background:#3978f6;color:white;border:0;padding:10px 14px;border-radius:8px;font-weight:bold;cursor:pointer;text-decoration:none;display:inline-block}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:10px;border-bottom:1px solid #273653;vertical-align:top}
small{color:#9eacc7}.pill{padding:4px 8px;border-radius:99px;background:#20365f;font-size:12px}
.metric{font-size:26px;font-weight:bold;margin-top:8px}.row{display:flex;gap:10px;flex-wrap:wrap}.row>*{flex:1;min-width:150px}
a{color:#8db4ff}.notice{background:#2a2415;border:1px solid #6d5825;padding:12px;border-radius:9px;margin-bottom:15px}
@media(max-width:650px){table{font-size:13px}td,th{padding:7px}}
</style></head><body>
<header><h1>✂️ ClipPilot AI</h1><div class="muted">Campaign ranking · clip production · submission tracker</div></header>
<main>
<div class="notice"><b>Starter mode:</b> campaign discovery and publishing integrations are not connected yet. Add campaigns you are eligible for, use footage you have permission to edit, and review submissions before sending.</div>
<div class="grid">
<div class="card"><small>Campaigns saved</small><div class="metric">{{ total }}</div></div>
<div class="card"><small>Best estimated rate</small><div class="metric">{{ best_rate }}</div><small>per 1,000 eligible views</small></div>
<div class="card"><small>Clips created</small><div class="metric">{{ clips }}</div></div>
<div class="card"><small>Submissions tracked</small><div class="metric">{{ submitted }}</div></div>
</div>
<div class="card"><h2>1. Add a campaign</h2>
<form method="post" action="/campaign">
<label>Campaign / creator name</label><input name="name" required placeholder="e.g. Creator campaign">
<label>Campaign URL</label><input name="url" type="url" placeholder="https://...">
<div class="row"><div><label>Pay per 1,000 views (₹)</label><input name="rate" type="number" min="0" step="0.01" required></div>
<div><label>Maximum payout (₹, optional)</label><input name="cap" type="number" min="0" step="0.01"></div>
<div><label>Deadline (optional)</label><input name="deadline" type="date"></div></div>
<label>Requirements / notes</label><textarea name="notes" rows="2" placeholder="Allowed platforms, minimum views, source footage rules..."></textarea>
<button type="submit">Save campaign</button></form></div>
<div class="card"><h2>2. Campaign comparison</h2>
{% if campaigns %}<table><tr><th>Campaign</th><th>Rate / 1K</th><th>Cap</th><th>Deadline</th><th>Score</th><th>Action</th></tr>
{% for c in campaigns %}<tr><td><b>{{c.name}}</b><br><small>{{c.notes or ''}}</small>{% if c.url %}<br><a href="{{c.url}}" target="_blank" rel="noopener">Open campaign ↗</a>{% endif %}</td>
<td>₹{{"%.2f"|format(c.rate)}}</td><td>{{ "₹%.0f"|format(c.cap) if c.cap else "—" }}</td><td>{{c.deadline or "—"}}</td><td><span class="pill">{{c.score}} / 100</span></td>
<td><form method="post" action="/status/{{c.id}}"><select name="status"><option {{'selected' if c.status=='research' else ''}}>research</option><option {{'selected' if c.status=='applied' else ''}}>applied</option><option {{'selected' if c.status=='accepted' else ''}}>accepted</option><option {{'selected' if c.status=='submitted' else ''}}>submitted</option><option {{'selected' if c.status=='paid' else ''}}>paid</option></select><button>Update</button></form></td></tr>{% endfor %}</table>
{% else %}<p class="muted">No campaigns yet. Add your first campaign above.</p>{% endif %}</div>
<div class="card"><h2>3. Create a short clip</h2><p class="muted">Upload a video file you own or are authorized to edit. This uses FFmpeg to crop a selected segment into a vertical 9:16 MP4.</p>
<form method="post" action="/make-clip" enctype="multipart/form-data">
<label>Source video</label><input type="file" name="video" accept="video/*" required>
<div class="row"><div><label>Start time (seconds)</label><input type="number" name="start" min="0" step="0.1" value="0" required></div><div><label>Duration (seconds)</label><input type="number" name="duration" min="1" max="180" step="0.1" value="30" required></div></div>
<button type="submit">Create vertical clip</button></form>
{% if clip_files %}<p><b>Created clips</b></p>{% for f in clip_files %}<p><a href="/clips/{{f}}">{{f}} ↓</a></p>{% endfor %}{% endif %}
</div>
<div class="card"><h2>4. Important next integrations</h2><p class="muted">Connect approved campaign APIs or feeds, AI moment detection, YouTube OAuth, Instagram professional-account publishing, and payout reporting. Never enter platform passwords here.</p>
</div>
</main></body></html>
"""

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS campaigns(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, url TEXT,
        rate REAL NOT NULL, cap REAL, deadline TEXT, notes TEXT,
        status TEXT DEFAULT 'research', created TEXT NOT NULL)""")
    con.commit()
    return con

def score_campaign(row):
    # Transparent baseline score: rate is primary; cap and deadline add small modifiers.
    rate = max(0, float(row["rate"] or 0))
    score = min(75, rate / 20 * 75)
    if row["cap"] and float(row["cap"]) >= 5000: score += 10
    if row["deadline"]:
        try:
            days = (date.fromisoformat(row["deadline"]) - date.today()).days
            score += 10 if 2 <= days <= 21 else (3 if days > 21 else -15)
        except ValueError: pass
    return max(0, min(100, round(score)))

@app.route("/")
def home():
    con = db()
    rows = con.execute("SELECT * FROM campaigns").fetchall()
    campaigns = []
    for r in rows:
        item = dict(r); item["score"] = score_campaign(r); campaigns.append(item)
    campaigns.sort(key=lambda x: x["score"], reverse=True)
    files = sorted([p.name for p in OUTPUT_DIR.glob("*.mp4")], reverse=True)
    best = max([float(r["rate"]) for r in rows], default=0)
    counts = {s: sum(1 for r in rows if r["status"] == s) for s in ["submitted","paid"]}
    con.close()
    return render_template_string(PAGE, total=len(rows), best_rate=f"₹{best:.2f}", clips=len(files),
        submitted=counts["submitted"]+counts["paid"], campaigns=campaigns, clip_files=files)

@app.post("/campaign")
def add_campaign():
    f = request.form
    try:
        rate = float(f.get("rate", 0)); cap = float(f["cap"]) if f.get("cap") else None
        if rate < 0 or (cap is not None and cap < 0): raise ValueError()
    except ValueError:
        flash("Enter valid non-negative amounts."); return redirect(url_for("home"))
    con = db()
    con.execute("INSERT INTO campaigns(name,url,rate,cap,deadline,notes,status,created) VALUES(?,?,?,?,?,?,?,?)",
        (f["name"].strip(), f.get("url","").strip(), rate, cap, f.get("deadline") or None,
         f.get("notes","").strip(), "research", datetime.utcnow().isoformat()))
    con.commit(); con.close()
    return redirect(url_for("home"))

@app.post("/status/<int:cid>")
def update_status(cid):
    status = request.form.get("status","research")
    if status not in {"research","applied","accepted","submitted","paid"}: return "Invalid status", 400
    con = db(); con.execute("UPDATE campaigns SET status=? WHERE id=?", (status,cid)); con.commit(); con.close()
    return redirect(url_for("home"))

@app.post("/make-clip")
def make_clip():
    f = request.files.get("video")
    try:
        start = float(request.form.get("start",0)); duration = float(request.form.get("duration",30))
        if start < 0 or duration <= 0 or duration > 180: raise ValueError()
    except ValueError:
        flash("Invalid clip timing."); return redirect(url_for("home"))
    if not f or not f.filename: return "Video file required", 400
    ext = Path(f.filename).suffix.lower()
    if ext not in {".mp4",".mov",".mkv",".webm",".m4v"}: return "Unsupported video format", 400
    token = uuid.uuid4().hex[:10]
    src = UPLOAD_DIR / f"{token}{ext}"
    out = OUTPUT_DIR / f"clip_{token}.mp4"
    f.save(src)
    cmd = ["ffmpeg","-y","-ss",str(start),"-i",str(src),"-t",str(duration),
           "-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
           "-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac","-b:a","128k","-movflags","+faststart",str(out)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=240)
    except FileNotFoundError:
        return "FFmpeg is not installed. Deploy with the included Dockerfile.", 500
    except subprocess.CalledProcessError as e:
        return "Clip processing failed: " + e.stderr.decode(errors="ignore")[-1200:], 500
    finally:
        try: src.unlink()
        except OSError: pass
    return redirect(url_for("home"))

@app.route("/clips/<path:filename>")
def clips(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

@app.get("/health")
def health(): return {"ok": True, "app": "ClipPilot AI"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT","5000")))

import json, os, sqlite3, threading, time
from datetime import datetime, timezone
from pathlib import Path
import requests
from flask import Blueprint, abort, flash, redirect, render_template_string, url_for

automation_bp = Blueprint("automation", __name__)
BASE = Path(__file__).parent
DATA = Path(os.getenv("DATA_DIR", BASE / "data"))
DB = DATA / "agent.db"
_lock = threading.Lock()
_started = False

HTML = """
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="20"><title>ClipPilot Automation</title>
<style>body{background:#080b16;color:#edf4ff;font:14px system-ui;margin:0}main{max-width:900px;margin:28px auto;padding:0 16px}.panel{background:#12182b;border:1px solid #293957;border-radius:14px;padding:17px;margin:14px 0}a{color:#6deaff}.muted{color:#9aa8c7}.tag{color:#8ef1ff;border:1px solid #35536b;border-radius:20px;padding:4px 9px;font-size:11px}.video{border-top:1px solid #28334d;padding:10px 0}</style></head><body><main>
<p><a href="/">← Back to ClipPilot</a></p><h1>Campaign automation</h1>
<p class="muted">Background discovery status refreshes every 20 seconds.</p>
<div class="panel"><b>What happens:</b><p>ClipPilot searches public YouTube video metadata for the selected campaign name.</p><p class="muted">It does not download or publish videos. Confirm the channel identity, campaign eligibility and clipping rights before any editing.</p>
{% if not api_ready %}<p style="color:#ffd27d">Setup required: add YOUTUBE_DATA_API_KEY in Render environment variables. Jobs will show “Needs setup” until then.</p>{% else %}<p style="color:#77edc2">YouTube API key detected.</p>{% endif %}</div>
{% for j in jobs %}<div class="panel"><b>{{j.campaign_name}}</b> <span class="tag">{{j.status}}</span><p class="muted">Job #{{j.id}} · {{j.message}}</p>
{% for v in j.videos %}<div class="video"><b>{{v.title}}</b><p class="muted">{{v.channel_title}} · {{v.published_at}}</p><a target="_blank" rel="noopener" href="{{v.url}}">Open YouTube video ↗</a></div>{% endfor %}</div>{% else %}<div class="panel">No jobs yet. Start discovery from a saved campaign.</div>{% endfor %}
</main></body></html>
"""

def connect():
    DATA.mkdir(parents=True, exist_ok=True)
    c=sqlite3.connect(DB, timeout=20); c.row_factory=sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS automation_jobs(
      id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_id INTEGER NOT NULL,
      status TEXT NOT NULL, message TEXT NOT NULL, videos TEXT NOT NULL DEFAULT '[]',
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
    c.commit()
    return c

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def process(job_id):
    c=connect()
    j=c.execute("SELECT * FROM automation_jobs WHERE id=?", (job_id,)).fetchone()
    if not j: c.close(); return
    campaign=c.execute("SELECT * FROM campaigns WHERE id=?", (j["campaign_id"],)).fetchone()
    key=os.getenv("YOUTUBE_DATA_API_KEY","").strip()
    if not campaign:
        status,msg="failed","Saved campaign was not found."
    elif not key:
        status,msg="needs_setup","Add YOUTUBE_DATA_API_KEY in Render environment variables."
    else:
        status,msg="searching","Searching YouTube public video metadata."
        c.execute("UPDATE automation_jobs SET status=?,message=?,updated_at=? WHERE id=?",(status,msg,now(),job_id)); c.commit()
        try:
            r=requests.get("https://www.googleapis.com/youtube/v3/search",
              params={"part":"snippet","type":"video","q":campaign["name"],"maxResults":15,"order":"date","key":key},timeout=20)
            r.raise_for_status()
            vids=[]
            for item in r.json().get("items",[]):
                vid=(item.get("id") or {}).get("videoId"); sn=item.get("snippet") or {}
                if vid:
                    vids.append({"title":sn.get("title","Untitled"),"channel_title":sn.get("channelTitle","Unknown channel"),
                      "published_at":sn.get("publishedAt","")[:10],"url":"https://www.youtube.com/watch?v="+vid})
            status="review_required"
            msg=("Found %d public video candidates. Verify the channel and campaign permissions."%len(vids)) if vids else "No matching public videos found. Add the creator/channel name to the campaign title and retry."
            c.execute("UPDATE automation_jobs SET status=?,message=?,videos=?,updated_at=? WHERE id=?",(status,msg,json.dumps(vids),now(),job_id)); c.commit()
        except requests.HTTPError as e:
            code=e.response.status_code if e.response is not None else "unknown"
            c.execute("UPDATE automation_jobs SET status='failed',message=?,updated_at=? WHERE id=?",
              ("YouTube API HTTP %s. Check API enablement, key restrictions and quota."%code,now(),job_id)); c.commit()
        except (requests.RequestException,ValueError):
            c.execute("UPDATE automation_jobs SET status='failed',message=?,updated_at=? WHERE id=?",
              ("YouTube discovery request failed. Check Render logs and API configuration.",now(),job_id)); c.commit()
        c.close(); return
    c.execute("UPDATE automation_jobs SET status=?,message=?,updated_at=? WHERE id=?",(status,msg,now(),job_id)); c.commit(); c.close()

def worker():
    while True:
        c=connect()
        row=c.execute("SELECT id FROM automation_jobs WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
        c.close()
        if row: process(row["id"])
        else: time.sleep(3)

def start_worker():
    global _started
    with _lock:
        if not _started:
            threading.Thread(target=worker,daemon=True,name="clippilot-discovery").start()
            _started=True

@automation_bp.post("/automation/start/<int:cid>")
def start(cid):
    c=connect()
    if not c.execute("SELECT id FROM campaigns WHERE id=?",(cid,)).fetchone():
        c.close(); abort(404)
    t=now()
    cur=c.execute("INSERT INTO automation_jobs(campaign_id,status,message,created_at,updated_at) VALUES(?,?,?,?,?)",
      (cid,"queued","Campaign selected. Discovery queued.",t,t))
    job=cur.lastrowid; c.commit(); c.close()
    start_worker()
    flash("Discovery job #%s queued. Follow progress on the Automation page."%job)
    return redirect(url_for("automation.jobs"))

@automation_bp.get("/automation")
def jobs():
    start_worker()
    c=connect()
    rows=c.execute("""SELECT j.*,c.name campaign_name FROM automation_jobs j
      LEFT JOIN campaigns c ON c.id=j.campaign_id ORDER BY j.id DESC LIMIT 30""").fetchall()
    c.close()
    data=[]
    for r in rows:
        x=dict(r)
        try: x["videos"]=json.loads(x.pop("videos") or "[]")
        except ValueError: x["videos"]=[]
        data.append(x)
    return render_template_string(HTML,jobs=data,api_ready=bool(os.getenv("YOUTUBE_DATA_API_KEY","").strip()))

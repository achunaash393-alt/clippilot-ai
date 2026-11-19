import json, os, re, sqlite3, threading, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
import requests
from bs4 import BeautifulSoup
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
<style>
:root{color-scheme:dark}body{background:#080b16;color:#edf4ff;font:14px system-ui;margin:0}
main{max-width:900px;margin:28px auto;padding:0 16px}.panel{background:#12182b;border:1px solid #293957;border-radius:14px;padding:17px;margin:14px 0}
a{color:#6deaff}.muted{color:#9aa8c7}.tag{color:#8ef1ff;border:1px solid #35536b;border-radius:20px;padding:4px 9px;font-size:11px}
.video{border-top:1px solid #28334d;padding:10px 0}.warn{color:#ffd27d}
</style></head><body><main>
<p><a href="/">← Back to ClipPilot</a></p><h1>Campaign automation</h1>
<p class="muted">Free public-web discovery · refreshes every 20 seconds</p>
<div class="panel"><b>How free discovery works</b>
<p>ClipPilot searches publicly accessible search-engine results for YouTube videos matching the saved campaign or creator name. No YouTube API key is needed.</p>
<p class="warn">Search results may be incomplete or blocked. A matching title is only a candidate—not proof that it belongs to the creator or is eligible for clipping.</p>
<p class="muted">Before editing, verify the channel, campaign rules and creator permission. ClipPilot does not download or publish videos.</p></div>
{% for j in jobs %}<div class="panel"><b>{{j.campaign_name}}</b> <span class="tag">{{j.status}}</span>
<p class="muted">Job #{{j.id}} · {{j.message}}</p>
{% for v in j.videos %}<div class="video"><b>{{v.title}}</b><p class="muted">{{v.channel_title}} · {{v.published_at}} · {{v.source}}</p><a target="_blank" rel="noopener" href="{{v.url}}">Open YouTube video ↗</a></div>{% endfor %}</div>
{% else %}<div class="panel">No jobs yet. Start discovery from a saved campaign.</div>{% endfor %}
</main></body></html>
"""

def connect():
    DATA.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=20)
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS automation_jobs(
      id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_id INTEGER NOT NULL,
      status TEXT NOT NULL, message TEXT NOT NULL, videos TEXT NOT NULL DEFAULT '[]',
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
    c.commit()
    return c

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def clean_youtube_url(raw):
    raw = unquote(raw or "").strip()
    if raw.startswith("//"):
        raw = "https:" + raw
    if raw.startswith("/"):
        return None
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if host.endswith("duckduckgo.com"):
        target = parse_qs(parsed.query).get("uddg", [None])[0]
        if target:
            return clean_youtube_url(target)
    if host not in ("youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"):
        return None
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif parsed.path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [""])[0]
    elif parsed.path.startswith(("/shorts/", "/live/")):
        video_id = parsed.path.split("/")[2] if len(parsed.path.split("/")) > 2 else ""
    else:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_-]{6,}", video_id or ""):
        return None
    return "https://www.youtube.com/watch?v=" + video_id

def public_search(query):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ClipPilotAI/1.0; public discovery)"}
    response = requests.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query, "kl": "in-en"},
        headers=headers, timeout=18
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results, seen = [], set()
    for a in soup.select("a.result__a"):
        url = clean_youtube_url(a.get("href", ""))
        title = a.get_text(" ", strip=True)
        if url and url not in seen:
            seen.add(url)
            results.append({"title": title or "YouTube video candidate",
                "channel_title": "Not verified", "published_at": "",
                "url": url, "source": "Public web search"})
        if len(results) >= 15:
            break
    return results

def process(job_id):
    c = connect()
    j = c.execute("SELECT * FROM automation_jobs WHERE id=?", (job_id,)).fetchone()
    if not j:
        c.close()
        return
    campaign = c.execute("SELECT * FROM campaigns WHERE id=?", (j["campaign_id"],)).fetchone()
    if not campaign:
        c.execute("UPDATE automation_jobs SET status='failed',message=?,updated_at=? WHERE id=?",
                  ("Saved campaign was not found.", now(), job_id))
        c.commit()
        c.close()
        return

    campaign_name = (campaign["name"] or "").strip()
    c.execute("UPDATE automation_jobs SET status='searching',message=?,updated_at=? WHERE id=?",
              ("Searching public web results; no API key required.", now(), job_id))
    c.commit()
    try:
        found = public_search('site:youtube.com/watch "' + campaign_name.replace('"', " ") + '"')
        if not found:
            found = public_search("YouTube " + campaign_name + " official videos")
        status = "review_required"
        if found:
            message = "Found %d public video candidates. Verify creator identity, campaign eligibility and clipping rights." % len(found)
        else:
            message = "No matching public video candidates found. Search may be blocked or the campaign name may be too broad."
        c.execute("UPDATE automation_jobs SET status=?,message=?,videos=?,updated_at=? WHERE id=?",
                  (status, message, json.dumps(found), now(), job_id))
        c.commit()
    except requests.RequestException:
        c.execute("UPDATE automation_jobs SET status='limited',message=?,updated_at=? WHERE id=?",
                  ("Public search could not be reached or blocked this request. Try again later or add the creator's channel/video link manually.", now(), job_id))
        c.commit()
    except Exception:
        c.execute("UPDATE automation_jobs SET status='failed',message=?,updated_at=? WHERE id=?",
                  ("Unexpected discovery error. Check the Render logs.", now(), job_id))
        c.commit()
    finally:
        c.close()

def worker():
    while True:
        c = connect()
        row = c.execute("SELECT id FROM automation_jobs WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
        c.close()
        if row:
            process(row["id"])
        else:
            time.sleep(3)

def start_worker():
    global _started
    with _lock:
        if not _started:
            threading.Thread(target=worker, daemon=True, name="clippilot-public-discovery").start()
            _started = True

@automation_bp.post("/automation/start/<int:cid>")
def start(cid):
    c = connect()
    if not c.execute("SELECT id FROM campaigns WHERE id=?", (cid,)).fetchone():
        c.close()
        abort(404)
    t = now()
    cur = c.execute(
        "INSERT INTO automation_jobs(campaign_id,status,message,created_at,updated_at) VALUES(?,?,?,?,?)",
        (cid, "queued", "Campaign selected. Free public-web discovery queued.", t, t)
    )
    job = cur.lastrowid
    c.commit()
    c.close()
    start_worker()
    flash("Free discovery job #%s queued. Follow progress on the Automation page." % job)
    return redirect(url_for("automation.jobs"))

@automation_bp.get("/automation")
def jobs():
    start_worker()
    c = connect()
    rows = c.execute("""SELECT j.*,c.name campaign_name FROM automation_jobs j
      LEFT JOIN campaigns c ON c.id=j.campaign_id ORDER BY j.id DESC LIMIT 30""").fetchall()
    c.close()
    data = []
    for r in rows:
        x = dict(r)
        try:
            x["videos"] = json.loads(x.pop("videos") or "[]")
        except ValueError:
            x["videos"] = []
        data.append(x)
    return render_template_string(HTML, jobs=data)

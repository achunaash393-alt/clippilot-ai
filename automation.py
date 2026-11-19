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
:root{color-scheme:dark}*{box-sizing:border-box}body{background:#0d1118;color:#edf2f7;font:14px/1.55 system-ui;margin:0}
main{max-width:960px;margin:24px auto;padding:0 16px 48px}.panel{background:#151c26;border:1px solid #2a3544;border-radius:12px;padding:17px;margin:14px 0}
a{color:#8fc5ee;text-decoration:none}a:hover{color:#c5e4fb}.muted{color:#9aa8b8}.tag{color:#c4d8e9;border:1px solid #3b4d60;border-radius:20px;padding:4px 9px;font-size:11px}
.video{border-top:1px solid #2a3544;padding:12px 0}.warn{color:#e6c58b}
@media(max-width:600px){main{margin:12px auto;padding:0 12px 36px}.panel{padding:14px}}

/* 3D workflow visualization, driven by real job status */
.workflow-head{display:flex;align-items:center;gap:17px;padding:14px 16px;background:#111a24;border:1px solid #2a3b4c;border-radius:13px;margin:16px 0;perspective:800px}
.workflow-orb-wrap{width:88px;height:78px;flex:0 0 88px;display:grid;place-items:center;position:relative}
.workflow-orb{width:48px;height:48px;border-radius:14px;border:1px solid #7da8c8;background:linear-gradient(145deg,#355d7b,#172635);display:grid;place-items:center;font-size:20px;color:#eaf5ff;transform:rotateX(18deg) rotateY(-25deg);box-shadow:8px 8px 0 #0b121b,9px 9px 0 1px #38566d;animation:workflow-float 4s ease-in-out infinite}
.workflow-orbit{position:absolute;width:78px;height:30px;border:1px solid #7198b766;border-radius:50%;transform:rotate(-25deg)}
.workflow-copy b{display:block;font-size:13px}.workflow-copy p{margin:4px 0 0;font-size:12px;color:#9aa8b8}
.stage-track{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin:14px 0 5px}
.stage{border:1px solid #303e4d;background:#121b25;border-radius:9px;padding:9px 7px;text-align:center;color:#8392a2;font-size:10px}
.stage .stage-dot{display:block;width:8px;height:8px;border-radius:50%;background:#526273;margin:0 auto 6px}
.stage.active{border-color:#6e9fc5;color:#d9eafa;background:#1b2b39}.stage.active .stage-dot{background:#8fc5ee}
.stage.done{border-color:#426d5a;color:#bce7d0}.stage.done .stage-dot{background:#65b88d}
.stage.blocked{border-color:#806a49;color:#e8d2ad}.stage.blocked .stage-dot{background:#c59a58}
@keyframes workflow-float{0%,100%{transform:rotateX(18deg) rotateY(-25deg) translateY(0)}50%{transform:rotateX(-8deg) rotateY(25deg) translateY(-5px)}}
@media(max-width:600px){.workflow-head{gap:10px;padding:11px}.workflow-orb-wrap{width:66px;flex-basis:66px}.workflow-orb{transform:scale(.82)}.stage-track{gap:4px}.stage{font-size:9px;padding:8px 3px}}
@media(prefers-reduced-motion:reduce){.workflow-orb{animation:none}}


/* ClipPilot UI refresh v2 — match main dashboard */
body{background:#0b1016;color:#edf3f8;letter-spacing:.005em}
main{max-width:1080px;margin:25px auto;padding:0 20px 52px}
h1{font-size:30px;letter-spacing:-.045em;margin:12px 0 4px;font-weight:720}
.panel{background:#121a23;border:1px solid #293746;border-radius:12px;padding:18px;margin:13px 0}
a{color:#91c6eb}a:hover{color:#d7edfb}
.tag{background:#1b2b39;border:1px solid #344b5f;color:#c4dced;border-radius:6px;padding:5px 9px}
.workflow-head{background:#121c26;border:1px solid #293746;border-radius:12px;padding:15px 18px}
.workflow-orb{background:linear-gradient(145deg,#315b79,#172635);border-color:#6e9fc5;box-shadow:7px 7px 0 #0b121b,8px 8px 0 1px #38566d}
.stage{background:#0f1821;border:1px solid #293746;border-radius:7px}
.stage.active{background:#1b2b39;border-color:#6e9fc5}
.stage.done{border-color:#426d5a}
.stage.blocked{border-color:#806a49}
.video{border-top:1px solid #293746;padding:13px 0}
.warn{color:#e3c99d}
.muted{color:#9aabba}
@media(max-width:600px){main{margin:13px auto;padding:0 12px 38px}h1{font-size:25px}.panel{padding:14px}.workflow-head{padding:12px}.stage{font-size:9px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}

</style></head><body><main>
<p><a href="/">← Back to ClipPilot</a></p><h1>Campaign automation</h1>
<p class="muted">Free public-web discovery · refreshes every 20 seconds</p>
<div class="workflow-head"><div class="workflow-orb-wrap"><div class="workflow-orbit"></div><div class="workflow-orb">✂</div></div><div class="workflow-copy"><b>ClipPilot workflow</b><p>Discovery and title matching are available. Permission review is manual; clipping and export are not triggered by this job yet.</p></div></div><div class="panel"><b>How free discovery works</b>
<p>ClipPilot searches publicly accessible search-engine results for YouTube videos matching the saved campaign or creator name. No YouTube API key is needed.</p>
<p class="warn">Search results may be incomplete or blocked. A matching title is only a candidate—not proof that it belongs to the creator or is eligible for clipping.</p>
<p class="muted">Before editing, verify the channel, campaign rules and creator permission. ClipPilot does not download or publish videos.</p></div>
{% for j in jobs %}<div class="panel"><b>{{j.campaign_name}}</b> <span class="tag">{{j.status}}</span>
<p class="muted">Job #{{j.id}} · {{j.message}}</p><div class="stage-track">
<div class="stage {% if j.status in ['queued','searching'] %}active{% elif j.status=='review_required' %}done{% elif j.status in ['limited','failed'] %}blocked{% endif %}"><span class="stage-dot"></span>Discover</div>
<div class="stage {% if j.status=='searching' %}active{% elif j.status=='review_required' %}done{% elif j.status in ['limited','failed'] %}blocked{% endif %}"><span class="stage-dot"></span>Match</div>
<div class="stage {% if j.status=='review_required' %}active{% elif j.status in ['limited','failed'] %}blocked{% endif %}"><span class="stage-dot"></span>Permission review</div>
<div class="stage"><span class="stage-dot"></span>Clip / export</div>
</div>
{% for v in j.videos %}<div class="video"><b>{{v.title}}</b><p class="muted">{{v.channel_title}} · {{v.source}} · Title match: {{v.match_score}}%</p><p class="muted">{{v.match_note}}</p><a target="_blank" rel="noopener" href="{{v.url}}">Open YouTube video ↗</a></div>{% endfor %}</div>
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
        # Search a few distinct public-web patterns, then merge duplicate video URLs.
        safe_name = campaign_name.replace('"', " ").strip()
        queries = [
            'site:youtube.com/watch "' + safe_name + '"',
            'site:youtube.com/shorts "' + safe_name + '"',
            '"' + safe_name + '" YouTube official video',
        ]
        merged = {}
        search_count = 0
        for query in queries:
            results = public_search(query)
            search_count += 1
            for video in results:
                merged.setdefault(video["url"], video)

        # Rank only title-text similarity. This is a relevance hint, not identity or rights verification.
        name_tokens = {t.lower() for t in re.findall(r"[A-Za-z0-9]{3,}", safe_name)}
        found = []
        for video in merged.values():
            title_tokens = {t.lower() for t in re.findall(r"[A-Za-z0-9]{3,}", video.get("title", ""))}
            matched = sorted(name_tokens & title_tokens)
            score = round(100 * len(matched) / max(1, len(name_tokens)))
            video["match_score"] = score
            video["match_note"] = ("Matched words: " + ", ".join(matched)) if matched else "No campaign-name words matched the title."
            found.append(video)
        found.sort(key=lambda item: item["match_score"], reverse=True)
        found = found[:30]
        status = "review_required"
        if found:
            message = "Searched %d public query patterns and found %d unique video candidates. Sorted by title-word match; channel identity, campaign eligibility and clipping rights remain unverified." % (search_count, len(found))
        else:
            message = "No public video candidates found across %d search patterns. Search may be blocked or the campaign name may be too broad." % search_count
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

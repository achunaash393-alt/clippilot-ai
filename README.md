# ClipPilot AI — free starter

A small cloud-deployable MVP for comparing paid clipping campaigns, tracking application/submission/payment status, and cutting authorized source videos into vertical MP4 clips.

## What works now
- Add campaign details manually and rank them with a transparent starter score.
- Track research → applied → accepted → submitted → paid.
- Upload a video file you own or have permission to edit and cut a 9:16 clip with FFmpeg.
- Health endpoint at `/health`.

## Not connected yet
This starter does **not** scrape campaign sites, submit applications, detect viral moments with AI, upload to YouTube/Instagram, or verify payments. Those require platform-approved APIs, account OAuth, campaign-specific rules, and sometimes paid compute. Never automate around access controls or submit unlicensed footage.

## Run locally
Requires Python 3.11+ and FFmpeg:
```bash
pip install -r requirements.txt
python app.py
```
Open http://localhost:5000

## Deploy to Render (free prototype)
1. Create a GitHub repository and upload these files.
2. In Render, choose **New → Blueprint**, connect the repository, and deploy `render.yaml`.
3. Open the generated `onrender.com` URL.
4. Free Render web services sleep after 15 minutes without traffic and may restart. Their local filesystem is ephemeral; this starter stores data under `/tmp`, so records and clips can be lost on restart/redeploy. Do not use it as the permanent production database.
5. For persistent records, connect a managed database/storage service. For always-on workers and scheduled background jobs, free Render is not sufficient; use an approved scheduled runner or paid worker.

## Next build milestones
1. Add official campaign marketplace APIs/RSS feeds and deduplication.
2. Store campaign terms, payout rules, allowed footage, platform, deadline, and proof requirements.
3. Rank campaigns by expected earnings, not headline rate alone.
4. Add transcript-based moment detection and clip suggestions.
5. Add YouTube OAuth publishing and Instagram professional-account publishing only after the owner authorizes both.
6. Add submission evidence and payout reconciliation.

## Security
- Set a strong unique `SECRET_KEY`.
- Never commit API tokens, passwords, OAuth secrets, or `.env` files.
- Use OAuth and least-privilege permissions.

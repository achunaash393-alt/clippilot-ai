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


## Public campaign discovery

The dashboard includes a user-triggered scanner for the public campaign directories of CLIPPING and Content Rewards. It reads publicly accessible pages only, with short timeouts and a bounded response size. It does not log in, bypass CAPTCHAs/access controls, apply to campaigns, submit clips, or claim campaign eligibility. Always open the official campaign page and verify the current brief, rights, supported platforms, view thresholds, budget and payout terms before making clips.

If a marketplace changes its public page layout or blocks automated requests, use the official directory links shown in the dashboard. No marketplace API access is assumed.


## India + Indian bank payout preference

The dashboard is configured to prioritize campaigns whose platform documents bank withdrawals. Content Rewards documents withdrawal from its creator balance through Whop to a bank account, and says bank availability spans 200+ countries; an Indian creator must still confirm that India and their own bank payout route are offered in their Whop payout settings and complete KYC. CLIPPING's published payout methods are PayPal, USDT (Ethereum), and USDC (Ethereum), so it is marked as not matching a bank-first preference. This is a platform-level filter, not a guarantee that every campaign accepts Indian creators or pays to an Indian bank. Always verify campaign-level geography, payout method, fees, currency conversion, KYC and terms before applying.

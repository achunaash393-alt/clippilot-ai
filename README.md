# ClipPilot AI

Cloud-deployable clipping campaign tracker and vertical-video utility.

## Current features
- Manually save and compare campaigns.
- Best-effort, user-triggered scanning of publicly accessible CLIPPING and Content Rewards directory pages. This may return no campaign cards when pages are JavaScript-rendered, blocked, or changed; it does not sign in or bypass access controls.
- Create 9:16 clips from videos you own or are authorized to edit using FFmpeg.
- Track your own campaign clip earnings in **My Earnings**: total recorded, approved, pending, rejected, views, clip/submission links, campaign association, and status history.
- No wallet, payment processing, or money transfer functionality.

## Earnings data limitations
Earnings are entered by the user based on figures shown in campaign accounts. The app does not independently fetch or verify marketplace payments, views, or approvals. Automatic verification would require authorized marketplace APIs or account integrations, which are not connected in this version. Keep pending and approved figures separate and only mark earnings approved after confirmation from the campaign platform.

## Run locally
Requires Python 3.11+ and FFmpeg:

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000.

## Deploy to Render
Upload the complete project files to the repository root and deploy using the included `render.yaml`. Configure a persistent disk and set `DATA_DIR` to its mount path if you need records and clips to survive restarts; the current free prototype may use ephemeral storage and can lose local data on redeploy/restart.

## Not connected yet
Automatic campaign discovery on a schedule, marketplace API integrations, AI moment detection, YouTube/Instagram publishing, and automatic earnings verification are not included. Never enter platform passwords or API secrets into campaign notes.

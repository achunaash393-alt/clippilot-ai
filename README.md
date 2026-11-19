# ClipPilot AI — Neon UI Upgrade

This package refreshes the existing Flask app with a responsive neon/cyberpunk interface and retains the current campaign discovery, campaign tracking, FFmpeg vertical clip rendering, and personal earnings tracker.

## Included
- Dark neon interface with cyan, electric-blue, violet and magenta accents
- Responsive navigation for Overview, Campaign Finder, Clip Studio, My Clips, My Earnings and AI Connections
- Campaign directory scan (best-effort public HTML scraping; not guaranteed to return all campaigns)
- Manual campaign creation and status tracking
- Upload-based FFmpeg vertical 9:16 clip rendering
- Personal earnings records linked to saved campaigns, with pending/approved/rejected totals
- No wallet, payment processing or money transfer functionality

## Deploy
1. Replace the existing repository root files with the files in this ZIP, including the `.github` folder.
2. Commit and push to GitHub.
3. Render should redeploy from the connected repository.

## Requirements
Python 3.12, Flask, Requests, BeautifulSoup and FFmpeg. The included Dockerfile installs FFmpeg.

## Important limitations
- The campaign scanner reads public pages only and can fail when sites use JavaScript rendering, change markup, or block automated requests.
- Earnings are manually recorded from figures visible in your campaign account; this app does not verify payouts automatically.
- Clip rendering currently uses an uploaded source video and manually selected start/duration. AI moment detection, automatic YouTube creator discovery, live-stream capture, animated captions, ChatGPT/Gemini/Claude API connections, and the ChatGPT MCP connector are not implemented by this UI refresh.
- Only process video you own or have permission to edit, and follow each campaign's clipping and publishing rules.
- Render's `/tmp` data directory is ephemeral on the current free configuration. Use a persistent disk or managed database/storage before relying on long-term records.
- API keys, if added later, must be stored as server-side environment variables and never embedded in browser code.

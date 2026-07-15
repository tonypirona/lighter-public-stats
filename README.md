# BTC Bot Public Stats

Public-safe dashboard for the Lighter BTC bot stats.

This repo is intentionally separate from the trading bot repo. It only publishes a sanitized `data/stats.json` snapshot and a static `index.html` dashboard.

## What Is Public

- Bot-only closed trade stats
- Clean 25x curve from a $100 starting base with a $5,000 notional cap
- Profit factor, win rate, drawdown, spread, slippage, and recent public trade rows
- Basic live snapshot from the latest local export
- Public-safe execution guard settings such as leverage, max notional, entry chase cap, and slippage caps
- Public-safe execution-quality buckets for slippage, entry book chase, and entry-chase cap what-if checks
- Public-safe guard activity counts showing sent and blocked entry records over 24h, 7d, and all-time windows
- Public-safe rolling performance windows, time-filter what-if diagnostics, and decision queue rows

## What Is Not Public

- API keys or private key material
- Account index
- Raw order IDs, client order IDs, trade IDs, or exchange payloads
- Local bot files
- Raw tracker ledgers

## Update The Public Stats

From PowerShell:

```powershell
cd "C:\Users\tntod\Documents\testing creation\lighter-public-stats"
.\publish_public_stats.ps1
```

If the repo is connected to GitHub, this exports a fresh `data/stats.json`, commits it, and pushes it. Vercel will redeploy after the GitHub push.

The publisher runs `validate_public_stats.py` before committing. The validator checks that required public dashboard sections exist, referenced HTML IDs are present, and suspicious private fields such as API keys, private keys, account index, raw order IDs, client IDs, or raw exchange payloads are not present in the public JSON.

## Automatic Updates

This PC can run a Windows scheduled task named `Lighter Public Stats Publisher`. It runs `auto_publish_public_stats.ps1` every 1 minute, exports fresh stats, pushes immediately when actual bot stats changed, and publishes a no-change heartbeat after about 4 minutes. The automatic task is stats-only, so it will not commit half-finished dashboard code changes while edits are in progress.

The public page also re-fetches stats every 10 seconds while it is open. It tries GitHub raw data, the Vercel bundled file, and a GitHub API fallback, then renders the newest public snapshot it can find. The exporter republishes no-change heartbeat snapshots after about 4 minutes, so the public page can show that the bot/tracker are alive even when no trade closed.

If Windows update removes or damages the scheduled task, repair it with:

```powershell
cd "C:\Users\tntod\Documents\testing creation\lighter-public-stats"
powershell -ExecutionPolicy Bypass -File .\install_auto_publish_task.ps1
```

## First GitHub Setup

Create an empty GitHub repo named `lighter-public-stats`, then run:

```powershell
cd "C:\Users\tntod\Documents\testing creation\lighter-public-stats"
git remote add origin https://github.com/YOUR_USERNAME/lighter-public-stats.git
git branch -M main
git push -u origin main
```

## First Vercel Setup

1. Open Vercel.
2. Import the GitHub repo.
3. Use framework preset `Other`.
4. Leave build command empty.
5. Leave output directory empty or root.
6. Deploy.

After that, every GitHub push updates the public dashboard.

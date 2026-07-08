# Base Live Contract Badges

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Built for Base](https://img.shields.io/badge/Built%20for-Base-0052FF)](https://base.org)

Generate **live, auto-updating shields.io badges** for any smart
contract on **Base** — transaction count, balance, and recent unique
users — and drop them straight into any project's README. No server,
no hosting: a GitHub Actions cron job refreshes a small JSON file every
few hours, and shields.io renders it as an SVG badge on the fly.

## Example

Once configured, a badge looks like this in any README:

```markdown
![transactions](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/stats/example-txcount.json)
![balance](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/stats/example-balance.json)
![users](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/stats/example-users.json)
```

## How it works

1. `badge_generator.py` reads `contracts.json`, and for each contract
   pulls balance and recent transaction data from Base.
2. It writes one small JSON file per metric into `stats/`, in
   [shields.io's "endpoint badge"](https://shields.io/badges/endpoint-badge)
   format (`{"schemaVersion": 1, "label": ..., "message": ..., "color": ...}`).
3. The GitHub Actions workflow commits those JSON files back to this
   repo every 6 hours (or whenever you trigger it manually).
4. Anyone can embed a badge by pointing `img.shields.io/endpoint` at
   the **raw** GitHub URL of one of those JSON files — shields.io
   fetches it fresh and renders the SVG every time the badge is viewed,
   so the badge always reflects the last commit's data.

## Quick start

### 1. Get a free Blockscout Pro API key

1. https://dev.blockscout.com/ → Login
2. Create an API key (the free tier covers Base)

### 2. Add the secret to your repository

**Settings → Secrets and variables → Actions → New repository secret**
- Name: `BLOCKSCOUT_API_KEY`
- Value: your key

### 3. Add your contract(s) to `contracts.json`

```json
{
  "contracts": [
    {
      "name": "my-token",
      "label": "My Token",
      "address": "0xYourContractAddress"
    }
  ]
}
```

- `name` is used in the generated filenames (`stats/my-token-txcount.json`, etc.) — keep it URL-safe (letters, numbers, hyphens).
- `label` is just for your own reference in the logs.

### 4. Run it manually

**Actions → Refresh Base Contract Badges → Run workflow**

This creates the `stats/*.json` files and commits them. After that it
refreshes automatically every 6 hours (change the `cron` line in
`.github/workflows/refresh.yml` to adjust).

### 5. Embed your badges

Once `stats/my-token-txcount.json` exists in your repo, embed it
anywhere with:

```markdown
![transactions](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/stats/my-token-txcount.json)
```

Available badge suffixes per contract: `-txcount`, `-balance`, `-users`.

## Structure

```
.
├── contracts.json                     # contracts to generate badges for
├── badge_generator.py                  # main script
├── requirements.txt
├── stats/                              # generated badge JSON (auto-committed)
└── .github/workflows/refresh.yml       # scheduled + manual refresh
```

## Limitations

- Transaction count and unique-user stats are computed from the **most
  recent 1,000 transactions**, not full history — shown as `1,000+`
  when the sample is capped, to stay honest rather than implying a
  precise all-time total. This keeps each run fast and avoids
  paginating through a contract's entire history on every refresh.
- Badges update whenever the workflow runs (default: every 6 hours),
  not on every single transaction — "live" here means "kept fresh by a
  scheduled job," not real-time streaming.
- Balance reflects the contract's native ETH balance only, not token
  holdings or TVL in paired liquidity.

## License

MIT — use it, modify it, fork it freely.

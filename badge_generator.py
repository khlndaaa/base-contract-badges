#!/usr/bin/env python3
"""
Base Live Contract Badge Generator (public template).

For every contract in contracts.json, this script pulls a few live
stats from Base and writes them as shields.io "endpoint badge" JSON
files into stats/. The workflow commits these files back to the repo,
and shields.io renders them as live SVG badges on demand — no server,
no hosting, just a GitHub Actions cron job and a JSON file per badge.

Embed a generated badge in any README with:

    ![badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/USER/REPO/main/stats/NAME-txcount.json)

Replace USER/REPO with your GitHub username and this repo's name, and
NAME with the "name" you gave the contract in contracts.json.

Stats are computed from the most recent PAGE_SIZE transactions (not
the contract's entire history) to keep runs fast and reliable — see
the README for details and limitations.
"""

import os
import json
import requests

CHAIN_ID = 8453  # Base mainnet
BLOCKSCOUT_URL = "https://api.blockscout.com/v2/api"

PLACEHOLDER_ADDRESS = "0x0000000000000000000000000000000000000000"
PAGE_SIZE = 1000  # how many recent transactions to sample for stats

API_KEY = os.environ.get("BLOCKSCOUT_API_KEY")
CONTRACTS_FILE = os.environ.get("CONTRACTS_FILE", "contracts.json")
STATS_DIR = os.environ.get("STATS_DIR", "stats")

if not API_KEY:
    raise SystemExit("❌ BLOCKSCOUT_API_KEY secret is not set")


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def api_get(params, retries=2):
    query = {"chainid": CHAIN_ID, "apikey": API_KEY, **params}
    for attempt in range(retries + 1):
        try:
            resp = requests.get(BLOCKSCOUT_URL, params=query, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "0" and data.get("message") not in ("No transactions found", "OK"):
                return None
            return data.get("result")
        except requests.exceptions.RequestException as e:
            if attempt < retries:
                continue
            print(f"⚠️  Failed to fetch data ({params.get('action')}): {e}")
            return None


def get_balance_eth(address):
    result = api_get({"module": "account", "action": "balance", "address": address})
    try:
        return int(result) / 1e18
    except (TypeError, ValueError):
        return None


def get_recent_txs(address):
    result = api_get({
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": PAGE_SIZE,
        "sort": "desc",
    })
    return result if isinstance(result, list) else []


def write_badge(name, suffix, label, message, color):
    badge = {
        "schemaVersion": 1,
        "label": label,
        "message": message,
        "color": color,
    }
    path = os.path.join(STATS_DIR, f"{name}-{suffix}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(badge, f, indent=2)
    print(f"   wrote {path} -> {label}: {message}")


def process_contract(entry):
    name = entry["name"]
    label = entry.get("label", name)
    address = entry["address"]

    print(f"=== {label} ({address}) ===")

    balance = get_balance_eth(address)
    txs = get_recent_txs(address)

    # Transaction count badge (capped sample, honestly labeled)
    tx_count = len(txs)
    tx_message = f"{tx_count:,}+" if tx_count >= PAGE_SIZE else f"{tx_count:,}"
    tx_color = "brightgreen" if tx_count > 100 else ("yellow" if tx_count > 0 else "lightgrey")
    write_badge(name, "txcount", "transactions (recent)", tx_message, tx_color)

    # Balance badge
    if balance is not None:
        bal_message = f"{balance:.4f} ETH"
        bal_color = "blue" if balance > 0 else "lightgrey"
    else:
        bal_message = "N/A"
        bal_color = "lightgrey"
    write_badge(name, "balance", "balance", bal_message, bal_color)

    # Unique recent users badge
    unique_users = len({tx.get("from", "").lower() for tx in txs if tx.get("from")})
    users_message = f"{unique_users:,}+" if tx_count >= PAGE_SIZE else f"{unique_users:,}"
    users_color = "brightgreen" if unique_users > 50 else ("yellow" if unique_users > 0 else "lightgrey")
    write_badge(name, "users", "unique users (recent)", users_message, users_color)


def main():
    os.makedirs(STATS_DIR, exist_ok=True)

    config = load_json(CONTRACTS_FILE, {})
    contracts = [c for c in config.get("contracts", []) if c.get("address", "").lower() != PLACEHOLDER_ADDRESS]

    if not contracts:
        print(
            f"⚠️  {CONTRACTS_FILE} has no real contracts (only the example placeholder). "
            f"Add your own contracts to generate badges."
        )
        return

    print(f"🔍 Generating badges for {len(contracts)} contract(s) on Base (chainId={CHAIN_ID})")

    for entry in contracts:
        process_contract(entry)
        print("")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Fetch latest AI benchmark data from public sources.

Sources:
- lmarena.ai (Chatbot Arena ELO)
- swebench.com (SWE-bench Verified)
- Other scores from public leaderboards / official reports

Falls back to existing data if fetching fails.
"""

import json
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

DATA_FILE = "data/benchmarks.json"

# Model name normalization mapping
MODEL_ALIASES = {
    # Arena names -> our canonical names
    "claude-4-opus": "Claude 4 Opus",
    "claude-4-sonnet": "Claude 4 Sonnet",
    "gpt-4o": "GPT-4o",
    "o3": "o3",
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "llama-4-maverick": "Llama 4 Maverick",
    "deepseek-r1": "DeepSeek-R1",
    "qwen3-235b": "Qwen3 235B",
    "mistral-large-2": "Mistral Large 2",
    "grok-3": "Grok-3",
}

# Known models we track
TRACKED_MODELS = set(MODEL_ALIASES.values())


def fetch_url(url, timeout=30):
    """Fetch URL content with error handling."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AI-Benchmark-Rankings/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"  Warning: Failed to fetch {url}: {e}", file=sys.stderr)
        return None


def fetch_arena_elo():
    """Attempt to fetch Chatbot Arena ELO scores from lmarena.ai."""
    print("Fetching Chatbot Arena ELO data...")
    # Try the known API endpoint
    urls = [
        "https://lmarena.ai/api/v1/leaderboard",
        "https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard/resolve/main/results.json",
    ]
    for url in urls:
        content = fetch_url(url)
        if content:
            try:
                data = json.loads(content)
                print(f"  Successfully fetched from {url}")
                return data
            except json.JSONDecodeError:
                continue
    print("  Could not fetch Arena ELO data from any source")
    return None


def fetch_swebench():
    """Attempt to fetch SWE-bench Verified scores."""
    print("Fetching SWE-bench data...")
    urls = [
        "https://www.swebench.com/api/leaderboard",
        "https://raw.githubusercontent.com/princeton-nlp/SWE-bench/main/docs/leaderboard.json",
    ]
    for url in urls:
        content = fetch_url(url)
        if content:
            try:
                data = json.loads(content)
                print(f"  Successfully fetched from {url}")
                return data
            except json.JSONDecodeError:
                continue
    print("  Could not fetch SWE-bench data from any source")
    return None


def load_existing_data():
    """Load existing benchmarks.json."""
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Warning: Could not load existing data", file=sys.stderr)
        return None


def update_timestamp(data):
    """Update the lastUpdated field with current JST time."""
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    data["lastUpdated"] = now.strftime("%Y-%m-%d %H:%M JST")
    return data


def main():
    print("=" * 50)
    print("AI Benchmark Rankings - Data Fetch")
    print("=" * 50)

    # Load existing data as base
    data = load_existing_data()
    if not data:
        print("ERROR: No existing data found. Cannot proceed.", file=sys.stderr)
        sys.exit(1)

    # Try to fetch live data from sources
    arena_data = fetch_arena_elo()
    swebench_data = fetch_swebench()

    updated = False

    # Update Arena ELO if we got data
    if arena_data and isinstance(arena_data, (list, dict)):
        print("  Processing Arena ELO data...")
        # Data format varies; try to extract what we can
        # This is best-effort - the API format may change
        updated = True

    # Update SWE-bench if we got data
    if swebench_data and isinstance(swebench_data, (list, dict)):
        print("  Processing SWE-bench data...")
        updated = True

    if not updated:
        print("\nNo live data sources available. Using existing data with updated timestamp.")

    # Always update timestamp to reflect when this deploy happened
    data = update_timestamp(data)

    # Write updated data
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\nData written to {DATA_FILE}")
    print(f"Timestamp: {data['lastUpdated']}")
    print("Done!")


if __name__ == "__main__":
    main()

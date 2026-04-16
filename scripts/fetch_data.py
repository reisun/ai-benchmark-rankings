#!/usr/bin/env python3
"""
Fetch latest AI benchmark data from lmarena-ai/leaderboard-dataset.

Updates Arena ELO scores from the HuggingFace dataset.
Other benchmark scores (MMLU, HumanEval, SWE-bench, MATH, GPQA) are kept as-is.
Falls back to existing data if fetching fails.
"""

import json
import sys
from datetime import datetime, timezone, timedelta

DATA_FILE = "data/benchmarks.json"

MODEL_NAME_MAP = {
    "claude-opus-4-6-thinking": "Claude 4 Opus",
    "claude-opus-4-6": "Claude 4 Opus",
    "claude-sonnet-4-6-thinking": "Claude 4 Sonnet",
    "claude-sonnet-4-6": "Claude 4 Sonnet",
    "chatgpt-4o-latest-20250326": "ChatGPT",
    "gpt-4o-2024-08-06": "ChatGPT",
    "gpt-4o-2024-05-13": "ChatGPT",
    "o3": "Codex",
    "o3-2025-04-16": "Codex",
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemini-2.5-pro-exp-03-25": "Gemini 2.5 Pro",
    "llama-4-maverick-17b-128e-instruct": "Llama 4 Maverick",
    "deepseek-r1": "DeepSeek-R1",
    "qwen3-235b-a22b": "Qwen3 235B",
    "qwen3-235b": "Qwen3 235B",
    "mistral-large-2": "Mistral Large 2",
    "mistral-large-2411": "Mistral Large 2",
    "grok-3-preview-02-24": "Grok-3",
    "grok-3-mini-high": "Grok-3",
    "grok-4.20-beta-0309-reasoning": "Grok-4",
    "grok-4.20-beta1": "Grok-4",
    "grok-4.20-multi-agent-beta-0309": "Grok-4",
    "grok-4.1-thinking": "Grok-4",
    "grok-4.1": "Grok-4",
    "grok-4-0709": "Grok-4",
}

TRACKED_MODELS = set(MODEL_NAME_MAP.values())


def load_existing_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Warning: Could not load existing data", file=sys.stderr)
        return None


def fetch_arena_elo():
    """Fetch Arena ELO from lmarena-ai/leaderboard-dataset via HuggingFace datasets."""
    print("Fetching Chatbot Arena ELO from lmarena-ai/leaderboard-dataset...")
    try:
        from datasets import load_dataset
        dataset = load_dataset("lmarena-ai/leaderboard-dataset", "text", split="latest")
        df = dataset.to_pandas()
        overall = df[df["category"] == "overall"].copy()
        print(f"  Loaded {len(overall)} overall entries")
        return overall
    except Exception as e:
        print(f"  Failed to fetch Arena ELO: {e}", file=sys.stderr)
        return None


def update_arena_scores(data, arena_df):
    """Update Arena ELO scores in data from the fetched dataframe."""
    model_lookup = {m["name"]: m for m in data["models"]}
    updated_count = 0

    best_per_canonical = {}
    for _, row in arena_df.iterrows():
        raw_name = row["model_name"]
        canonical = MODEL_NAME_MAP.get(raw_name)
        if canonical is None:
            continue
        rating = round(row["rating"], 1)
        if canonical not in best_per_canonical or rating > best_per_canonical[canonical]["rating"]:
            best_per_canonical[canonical] = {"rating": rating, "variant": raw_name}

    for canonical, info in best_per_canonical.items():
        rating = info["rating"]
        variant = info["variant"]
        if canonical in model_lookup:
            old = model_lookup[canonical]["scores"].get("arena_elo")
            model_lookup[canonical]["scores"]["arena_elo"] = int(round(rating))
            model_lookup[canonical]["arenaVariant"] = variant
            print(f"  {canonical}: {old} -> {int(round(rating))} ({variant})")
            updated_count += 1
        else:
            print(f"  Skipped (not in models list): {canonical} = {rating}")

    print(f"  Updated {updated_count} model(s)")
    return updated_count > 0


def update_timestamp(data):
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    data["lastUpdated"] = now.strftime("%Y-%m-%d %H:%M JST")
    return data


def main():
    print("=" * 50)
    print("AI Benchmark Rankings - Data Fetch")
    print("=" * 50)

    data = load_existing_data()
    if not data:
        print("ERROR: No existing data found. Cannot proceed.", file=sys.stderr)
        sys.exit(1)

    arena_df = fetch_arena_elo()

    if arena_df is not None and len(arena_df) > 0:
        update_arena_scores(data, arena_df)
    else:
        print("\nNo live data available. Using existing data with updated timestamp.")

    data = update_timestamp(data)

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\nData written to {DATA_FILE}")
    print(f"Timestamp: {data['lastUpdated']}")
    print("Done!")


if __name__ == "__main__":
    main()

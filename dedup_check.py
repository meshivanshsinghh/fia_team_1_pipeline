"""Cross-scenario deduplication checker.

Run this AFTER a full pipeline batch to find shared phrases across scenarios.
Lauren's Fix 6: "run an n-gram overlap check across the corpus and flag any 
shared span of roughly 8 or more words for review."

Usage:
    python dedup_check.py
    python dedup_check.py --min-words 6  # Lower threshold
    python dedup_check.py --outputs-dir /path/to/outputs
"""

import os
import re
import json
import argparse
from pathlib import Path
from collections import defaultdict


def extract_ngrams(text: str, n: int = 8) -> list:
    """Extract all n-grams from text, normalized."""
    words = re.findall(r'\b\w+\b', text.lower())
    return [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]


def load_scenarios(outputs_dir: Path) -> dict:
    """Load all scenario texts from output JSONs."""
    scenarios = {}
    for f in sorted(outputs_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            scenario = data.get('scenario', '')
            if isinstance(scenario, dict):
                scenario = scenario.get('scenario_text', '')
            if scenario:
                scenarios[f.name] = scenario
        except (json.JSONDecodeError, KeyError):
            print(f"  ⚠️  Skipping {f.name}: could not parse")
    return scenarios


def find_shared_phrases(scenarios: dict, min_words: int = 8) -> list:
    """Find n-grams that appear in more than one scenario."""
    # Map each n-gram to the files it appears in
    ngram_to_files = defaultdict(set)
    
    for filename, text in scenarios.items():
        ngrams = extract_ngrams(text, min_words)
        seen_in_file = set()
        for ng in ngrams:
            if ng not in seen_in_file:
                ngram_to_files[ng].add(filename)
                seen_in_file.add(ng)
    
    # Find n-grams shared across files
    shared = []
    seen_overlapping = set()
    
    for ngram, files in sorted(ngram_to_files.items(), key=lambda x: len(x[1]), reverse=True):
        if len(files) < 2:
            continue
        
        # Skip if this is a sub-phrase of something we already reported
        is_substring = False
        for existing in seen_overlapping:
            if ngram in existing or existing in ngram:
                is_substring = True
                break
        
        if not is_substring:
            shared.append({
                'phrase': ngram,
                'files': sorted(files),
                'count': len(files)
            })
            seen_overlapping.add(ngram)
    
    return shared


def main():
    parser = argparse.ArgumentParser(description="Cross-scenario deduplication checker")
    parser.add_argument('--outputs-dir', type=str, default='outputs', 
                        help='Path to outputs directory')
    parser.add_argument('--min-words', type=int, default=8,
                        help='Minimum n-gram length to check (default: 8)')
    args = parser.parse_args()
    
    outputs_dir = Path(args.outputs_dir)
    if not outputs_dir.exists():
        print(f"❌ Directory not found: {outputs_dir}")
        return
    
    print(f"Loading scenarios from {outputs_dir}...")
    scenarios = load_scenarios(outputs_dir)
    print(f"Loaded {len(scenarios)} scenarios.\n")
    
    if len(scenarios) < 2:
        print("Need at least 2 scenarios to check for duplicates.")
        return
    
    print(f"Checking for shared phrases ({args.min_words}+ words)...\n")
    shared = find_shared_phrases(scenarios, args.min_words)
    
    if not shared:
        print("✅ No shared phrases found across scenarios. Looking good!")
    else:
        print(f"⚠️  Found {len(shared)} shared phrase(s) across scenarios:\n")
        for i, item in enumerate(shared, 1):
            print(f"  {i}. \"{item['phrase']}\"")
            print(f"     Found in {item['count']} files: {', '.join(item['files'])}")
            print()
        
        print("=" * 60)
        print(f"SUMMARY: {len(shared)} shared phrases found.")
        print("Recurring moves are fine; recurring sentences are not.")
        print("Review each shared phrase and regenerate affected scenarios if needed.")


if __name__ == "__main__":
    main()

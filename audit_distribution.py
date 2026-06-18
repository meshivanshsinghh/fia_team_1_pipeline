#!/usr/bin/env python3
"""TODO #5 — audit player-type distribution before scaling past 24.

    python audit_distribution.py            # audits source_stories.csv
    python audit_distribution.py --outputs  # audits generated outputs/
"""
import json, sys, glob, os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
STORIES = os.path.join(HERE, "source_stories.csv")
TYPOLOGY = glob.glob(os.path.join(HERE, "Player*Typolog*"))  # tolerant of the long name

def all_types():
    if TYPOLOGY:
        return pd.read_csv(TYPOLOGY[0])["Player Type"].astype(str).str.strip().tolist()
    return []

def from_source():
    return pd.read_csv(STORIES)["player_type"].astype(str).str.strip().value_counts().to_dict()

def from_outputs():
    c = {}
    for f in glob.glob(os.path.join(HERE, "outputs", "*_final.json")):
        d = json.load(open(f, encoding="utf-8"))
        pt = str(d.get("player_type", "Unknown")).strip()
        c[pt] = c.get(pt, 0) + 1
    return c

def main():
    counts = from_outputs() if "--outputs" in sys.argv else from_source()
    types = all_types() or sorted(counts)
    src = "outputs/" if "--outputs" in sys.argv else "source_stories.csv"
    print(f"Player-type distribution ({src}):\n")
    for t in sorted(types, key=lambda x: (-counts.get(x, 0), x)):
        n = counts.get(t, 0)
        print(f"  {t:<24} {n:>3}  {'#'*n}{'   <-- ZERO' if n==0 else ''}")
    missing = [t for t in types if counts.get(t, 0) == 0]
    print(f"\n  total: {sum(counts.get(t,0) for t in types)} across {len(types)} types")
    print(f"  zero-coverage ({len(missing)}): {missing}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run after a re-run to confirm the TODO checklist. From repo root:
    python verify_rerun.py
"""
import json, re, glob, os
HERE = os.path.dirname(os.path.abspath(__file__))
LEGAL = {"Behavioral Red Flag","Internal Red Flag","Cultural/Demographic Information",
         "Power Information","Loaded Language"}
def words(t): return re.findall(r"\b\w+\b",(t or "").lower())

def main():
    files = sorted(glob.glob(os.path.join(HERE,"outputs","*_final.json")))
    if not files:
        print("No outputs/ files. Run team1_pipeline.py first."); return
    print(f"{len(files)} outputs\n")
    grams = {}
    for f in files:
        d = json.load(open(f, encoding="utf-8")); name = os.path.basename(f)
        s = d.get("scenario")
        struct = isinstance(s, dict)
        text = s.get("scenario_text","") if struct else str(s)
        wc = len(words(text)); wc_ok = 280 <= wc <= 340
        bad = []
        for sn in d.get("snippets", []):
            tags = sn.get("kind_of_signal", []); tags=[tags] if isinstance(tags,str) else tags
            bad += [t for t in tags if t not in LEGAL]
            if not sn.get("snippet_id"): bad.append("MISSING snippet_id")
        flag = "OK " if (struct and wc_ok and not bad) else "FAIL"
        print(f"  {flag} {name}: {wc}w, scenario={'dict' if struct else 'STRING'}"
              + (f", issues={sorted(set(bad))}" if bad else ""))
        for i in range(len(t:=words(text))-7):
            grams.setdefault(" ".join(t[i:i+8]), set()).add(name)
    shared = {g:n for g,n in grams.items() if len(n)>1}
    print(f"\n  shared >=8-word spans: {len(shared)}")
    for g,n in list(shared.items())[:10]:
        print(f"    {sorted(n)}: \"{g}\"")

if __name__ == "__main__":
    main()

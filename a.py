import json, glob
files = sorted(glob.glob("outputs/*.json"))
print(f"Files found: {len(files)}")
if files:
    sample = json.load(open(files[0]))
    print(f"scenario type: {type(sample.get('scenario')).__name__}")
    if isinstance(sample.get('scenario'), dict):
        print(f"scenario keys: {list(sample['scenario'].keys())}")
    print(f"top-level keys: {list(sample.keys())}")
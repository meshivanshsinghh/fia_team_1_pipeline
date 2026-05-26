import pandas as pd
import json
import os
import random
import glob

# 1. Define the path to your outputs folder
# If using Google Colab, you can upload your folder to '/content/outputs/'
outputs_dir = 'outputs/' 

data_sources = []

# Search for all .json files in the specified directory
json_files = glob.glob(os.path.join(outputs_dir, '*.json'))

print(f"Found {len(json_files)} JSON files in '{outputs_dir}'. Loading data...")

# Load each JSON file into our data_sources list
for file_path in json_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            data_sources.append(data)
        except json.JSONDecodeError as e:
            print(f"Error reading {file_path}: {e}")

# Proceed only if we successfully loaded data
if not data_sources:
    print("No valid JSON data found. Please check your folder path and files.")
else:
    models = ['gpt-4o-mini', 'gemini-2.5-flash', 'llama-3.1-70b']
    passes = [1, 2]
    runs = [1, 2, 3] # Group B requires 3 runs for reliability metrics [cite: 411]

    dummy_rows = []

    # 2. Synthesize the Scoring DB rows
    print("Synthesizing Scoring DB rows...")
    for data in data_sources:
        scenario = data.get('scenario', {})
        snippets = data.get('snippets', [])
        
        for snippet in snippets:
            for model in models:
                for p in passes:
                    for run in runs:
                        
                        signal_types = snippet.get('kind_of_signal', [])
                        
                        # Identify signal types for the DarkPatterns hypothesis 
                        is_satellite = any(sig in ['Loaded Language', 'Power Information'] for sig in signal_types)
                        is_behavioral = 'Behavioral Red Flag' in signal_types
                        
                        # SIMULATE THE HYPOTHESIS: Pass 1 misses Autonomy/Satellite signals [cite: 826]
                        if p == 1:
                            if is_satellite and not is_behavioral:
                                # High chance of missing/not addressing satellite signals in Pass 1
                                weights = [0.1, 0.2, 0.4, 0.3] 
                            elif is_behavioral:
                                # High chance of catching behavioral red flags in Pass 1
                                weights = [0.75, 0.15, 0.05, 0.05]
                            else:
                                weights = [0.4, 0.3, 0.2, 0.1]
                            status = random.choices(['DETECTED', 'PARTIAL', 'MISSED', 'NOT_ADDRESSED'], weights=weights)[0]
                        else: 
                            # Pass 2 (Targeted) forces recognition, closing the gap
                            status = random.choices(['DETECTED', 'PARTIAL', 'MISSED'], weights=[0.85, 0.10, 0.05])[0]

                        # Generate semantic math (Cosine Similarity)
                        if status == 'DETECTED':
                            cos_res = round(random.uniform(0.7, 0.95), 2)
                            match_qual = 'exact' if cos_res > 0.85 else 'semantic'
                        elif status == 'PARTIAL':
                            cos_res = round(random.uniform(0.4, 0.69), 2)
                            match_qual = 'semantic' if cos_res > 0.55 else 'mismatch'
                        elif status == 'MISSED':
                            cos_res = round(random.uniform(0.1, 0.39), 2)
                            match_qual = 'off-target'
                        else: # NOT_ADDRESSED
                            cos_res = None
                            match_qual = None
                            
                        # Simulate question quality if the AI addressed the snippet
                        cos_q = round(random.uniform(0.4, 0.9), 2) if status != 'NOT_ADDRESSED' else None

                        # Ensure lists are safely joined, even if they are missing or None
                        unes_traits = snippet.get('unes_traits') or ['Not Found']
                        unmet_need = snippet.get('unmet_need') or ['Not Found']
                        possible_trauma = snippet.get('possible_trauma') or ['Not Found']

                        row = {
                            'scenario_id': scenario.get('scenario_id', 'Unknown'),
                            'snippet_id': snippet.get('snippet_id', 'Unknown'),
                            'model': model,
                            'pass': p,
                            'run_number': run,
                            'culture': scenario.get('culture', 'Unknown'),
                            'demographics': scenario.get('demographics', 'Unknown'),
                            'kind_of_signal': ", ".join(signal_types),
                            'unes_traits': ", ".join(unes_traits),
                            'unmet_need': ", ".join(unmet_need),
                            'possible_trauma': ", ".join(possible_trauma),
                            'detection_status': status,
                            'match_quality': match_qual,
                            'cosine_sim_reasoning': cos_res,
                            'cosine_sim_questions': cos_q
                        }
                        dummy_rows.append(row)

    # 3. Create DataFrame and Export
    df = pd.DataFrame(dummy_rows)
    csv_filename = 'team3_dummy_scoring_db_full.csv'
    df.to_csv(csv_filename, index=False)

    print(f"Successfully generated {len(df)} dummy rows based on {len(data_sources)} scenarios!")
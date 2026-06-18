"""FIA Scenario Generation Pipeline — local Python version."""

import os
import re
import json
import time
import datetime
from pathlib import Path
from collections import Counter

from google import genai
from google.genai import types
import pandas as pd
from dotenv import load_dotenv

# ============================================================
# CONFIGURATION & SETUP
# ============================================================
HERE = Path(__file__).parent
load_dotenv(HERE / ".env")

# File Paths
CSV_PATH = HERE / "snippets.csv"
PLAYER_VOCAB_PATH = HERE / "FIA_Player_Vocabulary_MASTER-05-27-26 - FIA_Player_Vocabulary_MASTER.csv.csv"
BATCH_INPUT_PATH = HERE / "source_stories.csv"
PROMPT_PATH = HERE / "FIA_Construction_Prompt_v2.md"

# Output Directories
OUTPUTS_DIR = HERE / "outputs"
PROFILES_DIR = HERE / "profiles"
OUTPUTS_DIR.mkdir(exist_ok=True)
PROFILES_DIR.mkdir(exist_ok=True)

# API Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
CLASSIFIER_MODEL = os.environ.get("GEMINI_CLASSIFIER_MODEL", "gemini-2.5-pro") # Upgraded model name
GENERATOR_MODEL = os.environ.get("GEMINI_GENERATOR_MODEL", "gemini-2.5-pro")

if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found in environment or .env file.")

client = genai.Client(api_key=GEMINI_API_KEY)

# Generation Constraints
WORD_COUNT_MIN = 280
WORD_COUNT_MAX = 340
WORD_COUNT_RETRIES = 2

def log(stage, msg):
    print(f"[{stage.upper()}] {msg}")

def word_count(text: str) -> int:
    return len(re.findall(r'\b\w+\b', text))

# ============================================================
# SCHEMAS
# ============================================================
# Schema for Stage 1: Classifier
CLASSIFIER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "demographics": {"type": "STRING", "description": "Age, race, gender, relationship status"},
        "geographic_setting": {"type": "STRING", "description": "City or environment type"},
        "cultural_context": {"type": "STRING", "description": "Job, social sphere, or community type"},
        "ideological_register": {"type": "STRING", "description": "The exact name of the cultural register to use (e.g., Black Manosphere, Evangelical, etc.)"}
    },
    "required": ["demographics", "geographic_setting", "cultural_context", "ideological_register"]
}

# Schema for Stage 3: Generator (from team1_pipeline.py)
GENERATOR_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "scenario": {
            "type": "STRING",
            "description": "The 280-340 word first-person narrative."
        },
        "snippets": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "quote": {"type": "STRING"},
                    "kind_of_signal": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "One or more of: Behavioral Red Flag, Internal Red Flag, "
                                       "Cultural/Demographic Information, Power Information, Loaded Language. "
                                       "Tags may stack on one snippet."
                    },
                    "unes_traits": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "unmet_need": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "possible_trauma": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "reasoning": {"type": "STRING"}
                },
                "required": ["quote", "kind_of_signal", "unes_traits", "unmet_need", "possible_trauma", "reasoning"]
            }
        }
    },
    "required": ["scenario", "snippets"]
}

# Schema for Stage 5: Metadata backfill (fix #2) — turns the scenario string into
# a structured object Team 3's scoring can rely on.
BACKFILL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "architecture_name": {"type": "STRING", "description": "One sentence naming the late-stage trait pattern's architecture."},
        "culture": {"type": "STRING"},
        "demographics": {"type": "STRING"},
        "cultural_context": {"type": "STRING"},
        "geographic_setting": {"type": "STRING"},
        "core_behaviors": {"type": "ARRAY", "items": {"type": "STRING"}},
        "satellite_signals": {"type": "ARRAY", "items": {"type": "STRING"}},
        "dismissible_red_flags": {"type": "ARRAY", "items": {"type": "STRING"}}
    },
    "required": ["architecture_name", "culture", "demographics", "cultural_context",
                 "geographic_setting", "core_behaviors", "satellite_signals", "dismissible_red_flags"]
}

# The ONLY legal Kind-of-Signal values (controlled vocabulary, fix #6).
LEGAL_SIGNAL_CATEGORIES = {
    "Behavioral Red Flag", "Internal Red Flag",
    "Cultural/Demographic Information", "Power Information", "Loaded Language",
}

# ============================================================
# CORE PIPELINE FUNCTIONS
# ============================================================

def classify_source_story(source_story: str, available_registers: list) -> dict:
    """Uses the LLM to extract demographics and pick a valid register."""
    prompt = f"""
    Analyze the following late-stage source story. Extract the demographics, geographic setting, and cultural context. 
    Then, select the most appropriate ideological register from this exact list: {available_registers}
    
    SOURCE STORY:
    {source_story}
    """
    
    config = types.GenerateContentConfig(
        temperature=0.0,
        response_mime_type="application/json",
        response_schema=CLASSIFIER_SCHEMA,
    )
    
    response = client.models.generate_content(
        model=CLASSIFIER_MODEL,
        contents=prompt,
        config=config
    )
    return json.loads(response.text)

def build_linguistic_profile(scenario_id, register, player_type, community_df, player_df):
    """Combines community language with player manipulation language and saves it."""
    
    # Extract community language (cap at 100 for token limits)
    community_snippets = community_df[community_df['culture'] == register].to_dict('records')
    if len(community_snippets) > 100:
        import random
        community_snippets = random.sample(community_snippets, 100)
        
    # Extract player psychology language.
    # Fix #1: normalize both sides (strip + lowercase) so casing/whitespace
    # mismatches ("Pity-Party Parker" vs "Pity-party Parker") can't silently
    # return zero rows.
    player_snippets = player_df[
        player_df['nickname'].str.strip().str.lower() == player_type.strip().lower()
    ].to_dict('records')

    # Loud failure: never generate against an empty vocabulary. This is the guard
    # that would have caught the stale 2-player file on the first run.
    if not player_snippets:
        raise ValueError(
            f"No vocabulary rows for player '{player_type}'. Check "
            f"{PLAYER_VOCAB_PATH.name} (is it the full 2,222-row master?) and the "
            f"nickname spelling. Refusing to generate with an empty vocabulary."
        )
    
    # Build Object
    profile = {
        "scenario_metadata": {
            "scenario_id": scenario_id,
            "target_register": register,
            "player_type": player_type
        },
        "manipulation_vocabulary": [
            {
                "mechanism": s.get("tell_mechanism", "Unknown"),
                "his_language": s.get("his_language", ""),
                "expert_notices": s.get("what_expert_notices", "")
            } for s in player_snippets if pd.notna(s.get("his_language"))
        ],
        "community_vocabulary": community_snippets
    }
    
    # Save to disk as an artifact
    clean_type = player_type.replace(' ', '')
    profile_path = PROFILES_DIR / f"profile_{scenario_id}_{clean_type}.json"
    
    # Clean up any old versions
    for old_profile in PROFILES_DIR.glob(f"profile_{scenario_id}_*.json"):
        old_profile.unlink()

    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
        
    return profile, profile_path

def build_user_message(scenario_id, register, player_type, demographics, geo, cultural, source, linguistic_profile_json):
    return f"""
SCENARIO ID: {scenario_id}

============================================================
PLAYER TYPE & LINGUISTIC PROFILE
============================================================
The partner in this scenario is a: {player_type}

You must construct the scenario using the exact manipulation language mapped to this player type, disguised by the cultural norms of their community. 

Here is the combined Linguistic Profile (Community Register + Manipulation Trait Language):
{linguistic_profile_json}

Use the `manipulation_vocabulary` to structure the psychological trap, and dress those traps using the `community_vocabulary`.

============================================================
DEMOGRAPHICS & CONTEXT
============================================================
Demographics: {demographics}
Geographic Setting: {geo}
Cultural Context: {cultural}
Ideological Register: {register}

============================================================
LATE-STAGE SOURCE STORY
============================================================
{source}
"""

def generate_scenario(system_prompt: str, user_message: str):
    """Calls Gemini to generate the scenario and snippets table."""
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.7,
        response_mime_type="application/json",
        response_schema=GENERATOR_SCHEMA,
    )
    response = client.models.generate_content(
        model=GENERATOR_MODEL,
        contents=user_message,
        config=config
    )
    raw = response.text
    try:
        return json.loads(raw), raw
    except json.JSONDecodeError:
        log("error", "Failed to parse JSON. Raw output:")
        print(raw)
        raise

def regenerate_until_in_range(result: dict, raw: str, system_prompt: str, user_msg: str):
    """Forces the word count into the 280-340 sweet spot."""
    scenario_text = result.get("scenario", "")
    current_wc = word_count(scenario_text)
    attempts = 0

    while (current_wc < WORD_COUNT_MIN or current_wc > WORD_COUNT_MAX) and attempts < WORD_COUNT_RETRIES:
        attempts += 1
        log("word-count", f"Attempt {attempts}: count is {current_wc}. Regenerating...")
        
        correction = f"\n\nCRITICAL FIX: Your previous scenario was {current_wc} words. You MUST write strictly between {WORD_COUNT_MIN} and {WORD_COUNT_MAX} words. Do not change the JSON structure."
        
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.6,
            response_mime_type="application/json",
            response_schema=GENERATOR_SCHEMA,
        )
        response = client.models.generate_content(
            model=GENERATOR_MODEL,
            contents=user_msg + correction,
            config=config
        )
        raw = response.text
        try:
            result = json.loads(raw)
            scenario_text = result.get("scenario", "")
            current_wc = word_count(scenario_text)
        except json.JSONDecodeError:
            log("error", "JSON decode failed on retry.")
            break

    if WORD_COUNT_MIN <= current_wc <= WORD_COUNT_MAX:
        log("word-count", f"SUCCESS! Word count settled at {current_wc}.")
    else:
        log("word-count", f"WARNING: Failed to hit word count target. Final count: {current_wc}.")

    return result, raw

def structure_metadata(scenario_text: str) -> dict:
    """Fix #2: backfill structured metadata from the locked narrative using the
    classifier model, so the saved `scenario` is a dict, not a raw string."""
    prompt = f"""You are an expert behavioral analyst. Read the following first-person
narrative scenario and extract the analytical metadata required by the JSON schema.
Infer the implied culture, demographics, geographic setting, manipulative core
behaviors, satellite signals, and why the red flags are dismissible. Do not invent
details that contradict the text.

SCENARIO TEXT:
{scenario_text}
"""
    config = types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
        response_schema=BACKFILL_SCHEMA,
    )
    response = client.models.generate_content(
        model=CLASSIFIER_MODEL,
        contents=prompt,
        config=config,
    )
    return json.loads(response.text)


def validate_snippets(snippets: list) -> list:
    """Fix #6: controlled-vocabulary check. Every kind_of_signal value must be one
    of the five legal categories. Returns a list of warnings (empty == clean)."""
    warnings = []
    for i, snip in enumerate(snippets):
        tags = snip.get("kind_of_signal", [])
        if isinstance(tags, str):
            tags = [tags]
        if not tags:
            warnings.append(f"snippet {i}: missing kind_of_signal")
        for tag in tags:
            if tag not in LEGAL_SIGNAL_CATEGORIES:
                warnings.append(f"snippet {i}: invalid tag '{tag}'")
    return warnings


# ============================================================
# MAIN BATCH LOOP
# ============================================================

def main():
    print("Initializing FIA Batch Pipeline...")
    
    # 1. Load Data
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()
        
    stories_df = pd.read_csv(BATCH_INPUT_PATH)
    community_df = pd.read_csv(CSV_PATH)
    player_df = pd.read_csv(PLAYER_VOCAB_PATH)
    
    available_registers = community_df['culture'].unique().tolist()

    # 2. Iterate through CSV
    for index, row in stories_df.iterrows():
        scenario_id = row['story_id']
        source_story = row['source_story']
        player_type = row['player_type']
        
        print(f"\n{'='*60}")
        print(f"Processing: {scenario_id} | Player: {player_type}")
        print(f"{'='*60}")
        
        success = False
        rate_limit_retries = 0
        
        # RATE LIMIT SAFETY LOOP
        while not success and rate_limit_retries < 5:
            try:
                # STEP 1: Extract Context & Register
                log("step 1", "Extracting context via classifier...")
                context = classify_source_story(source_story, available_registers)
                register = context['ideological_register']
                
                # STEP 2: Build Linguistic Profile
                log("step 2", f"Building linguistic profile for {register} + {player_type}...")
                profile_dict, profile_path = build_linguistic_profile(
                    scenario_id, register, player_type, community_df, player_df
                )
                log("step 2.5", f"Profile saved to: {profile_path.name}")
                
                # STEP 3: Generate
                log("step 3", "Generating scenario & snippets...")
                profile_json_string = json.dumps(profile_dict, indent=2)
                user_msg = build_user_message(
                    scenario_id, register, player_type, 
                    context['demographics'], context['geographic_setting'], 
                    context['cultural_context'], source_story, profile_json_string
                )
                
                result, raw = generate_scenario(system_prompt, user_msg)
                
                # STEP 4: Check Word Count Constraints
                log("step 4", "Validating word count constraints...")
                result, raw = regenerate_until_in_range(result, raw, system_prompt, user_msg)
                
                # STEP 5: Structure metadata (fix #2) so `scenario` is a dict,
                # not a raw string. Team 3's scoring (dummy.py) depends on this.
                log("step 5", "Structuring metadata with classifier model...")
                scenario_text = result.get("scenario", "")
                if isinstance(scenario_text, dict):
                    scenario_text = scenario_text.get("scenario_text", "")
                metadata = structure_metadata(scenario_text)
                result["scenario"] = {
                    "scenario_id": scenario_id,
                    "architecture_name": metadata["architecture_name"],
                    "culture": metadata["culture"],
                    "demographics": metadata["demographics"],
                    "cultural_context": metadata["cultural_context"],
                    "geographic_setting": metadata["geographic_setting"],
                    "core_behaviors": metadata["core_behaviors"],
                    "satellite_signals": metadata["satellite_signals"],
                    "dismissible_red_flags": metadata["dismissible_red_flags"],
                    "scenario_text": scenario_text,
                }

                # Stable snippet IDs so Team 2/3 can key on them (dummy.py reads
                # snippet_id). Format matches the Notion boards: <id>-SNNNNN.
                for i, snip in enumerate(result.get("snippets", []), start=1):
                    snip["snippet_id"] = f"{scenario_id}-SN{i:04d}"

                # Controlled-vocabulary validation (fix #6).
                tag_warnings = validate_snippets(result.get("snippets", []))
                for w in tag_warnings:
                    log("validate", w)

                # STEP 6: Save
                log("step 6", "Cleaning up old files and saving new version...")

                final_output = {
                    "scenario_id": scenario_id,
                    "player_type": player_type
                }

                final_output.update(result)
                final_output["tag_warnings"] = tag_warnings

                # Delete any existing files
                for old_file in OUTPUTS_DIR.glob(f"{scenario_id}_final*.json"):
                    old_file.unlink()
                
                # Save with a static, deterministic filename
                output_path = OUTPUTS_DIR / f"{scenario_id}_final.json"
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(final_output, f, indent=2, ensure_ascii=False)
                    
                log("SUCCESS", f"Final JSON saved to: {output_path.name}")
                
                success = True # Break out of the retry loop
                
                # Standard API cooldown to stay under 15 Requests Per Minute
                time.sleep(12) 

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    rate_limit_retries += 1
                    log("RATE LIMIT HIT", f"Sleeping for 60 seconds to reset quota... (Attempt {rate_limit_retries}/5)")
                    time.sleep(60)
                else:
                    log("FATAL ERROR", f"Failed on {scenario_id}: {error_msg}")
                    import traceback
                    traceback.print_exc()
                    break # Break the while loop if it's a normal code error, move to next story

if __name__ == "__main__":
    main()

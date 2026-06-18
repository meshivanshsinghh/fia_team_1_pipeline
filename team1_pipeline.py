"""FIA Scenario Generation Pipeline — local Python version."""

import os
import re
import json
import time
import datetime
from pathlib import Path
from collections import Counter

import anthropic
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
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
CLASSIFIER_MODEL = os.environ.get("CLAUDE_CLASSIFIER_MODEL", "claude-haiku-4-5") 
GENERATOR_MODEL = os.environ.get("CLAUDE_GENERATOR_MODEL", "claude-sonnet-4-6")

if not ANTHROPIC_API_KEY:
    raise EnvironmentError("ANTHROPIC_API_KEY not found in environment or .env file.")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Generation Constraints
WORD_COUNT_MIN = 280
WORD_COUNT_MAX = 340
WORD_COUNT_RETRIES = 2

# ============================================================
# CONTROLLED VOCABULARIES 
# ============================================================
LEGAL_KINDS = {
    "Behavioral Red Flag", "Internal Red Flag",
    "Cultural/Demographic Information", "Power Information", "Loaded Language"
}
LEGAL_NEEDS = {
    "Connection", "Fairness", "Morality", "Reality",
    "Worth", "Autonomy", "Agency", "Safety", "Not Found"
}
LEGAL_TRAUMAS = {
    "Coercive Control", "Gaslighting (DARVO)", "Humiliation",
    "Betrayal / Exploitation", "Emotional Neglect", "Moral Injury",
    "Narcissistic Grandiosity", "Obsessive Attachment / Enmeshment",
    "Psychopathy / Terror", "Not Found"
}

def log(stage, msg):
    print(f"[{stage.upper()}] {msg}")

def word_count(text: str) -> int:
    return len(re.findall(r'\b\w+\b', text))

# ============================================================
# SCHEMAS
# ============================================================
# Schema for Stage 1: Classifier
CLASSIFIER_SCHEMA = {
    "type": "object",
    "properties": {
        "demographics": {"type": "string", "description": "Age, race, gender, relationship status"},
        "geographic_setting": {"type": "string", "description": "City or environment type"},
        "cultural_context": {"type": "string", "description": "Job, social sphere, or community type"},
        "ideological_register": {"type": "string", "description": "The exact name of the cultural register to use (e.g., Black Manosphere, Evangelical, etc.)"}
    },
    "required": ["demographics", "geographic_setting", "cultural_context", "ideological_register"]
}

# Schema for Stage 3: Generator
GENERATOR_SCHEMA = {
    "type": "object",
    "properties": {
        "scenario_id": {"type": "string"},
        "player_type": {"type": "string"},
        "architecture_name": {"type": "string"},
        "culture": {"type": "string"},
        "demographics": {"type": "string"},
        "core_behaviors": {"type": "array", "items": {"type": "string"}},
        "satellite_signals": {"type": "array", "items": {"type": "string"}},
        "dismissible_red_flags": {"type": "array", "items": {"type": "string"}},
        "scenario": {
            "type": "string",
            "description": "The 280-340 word first-person narrative."
        },
        "snippets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quote": {"type": "string"},
                    "kind_of_signal": {"type": "string"},
                    "unes_traits": {"type": "array", "items": {"type": "string"}},
                    "unmet_need": {"type": "array", "items": {"type": "string"}},
                    "possible_trauma": {"type": "array", "items": {"type": "string"}},
                    "reasoning": {"type": "string"}
                },
                "required": ["quote", "kind_of_signal", "unes_traits", "unmet_need", "possible_trauma", "reasoning"]
            }
        }
    },
    "required": ["scenario_id", "player_type", "architecture_name", "culture", "demographics", "core_behaviors", "satellite_signals", "dismissible_red_flags", "scenario", "snippets"]
}

# ============================================================
# CORE PIPELINE FUNCTIONS
# ============================================================

def classify_source_story(source_story: str, available_registers: list) -> dict:
    """Uses Claude to extract demographics and pick a valid register via Tool Use."""
    prompt = f"""
    Analyze the following late-stage source story. Extract the demographics, geographic setting, and cultural context. 
    Then, select the most appropriate ideological register from this exact list: {available_registers}
    
    SOURCE STORY:
    {source_story}
    """
    
    response = client.messages.create(
        model=CLASSIFIER_MODEL,
        max_tokens=1024,
        temperature=0.0,
        tools=[{
            "name": "record_classification",
            "description": "Output the classification data according to the schema.",
            "input_schema": CLASSIFIER_SCHEMA
        }],
        tool_choice={"type": "tool", "name": "record_classification"},
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Extract the JSON payload from the tool use block
    for block in response.content:
        if block.type == 'tool_use':
            return block.input
            
    raise ValueError("Claude failed to use the classification tool.")

def build_linguistic_profile(scenario_id, register, player_type, community_df, player_df):
    """Combines community language with player manipulation language and saves it."""
    
    # Extract community language (cap at 100 for token limits)
    community_snippets = community_df[community_df['culture'] == register].to_dict('records')
    if len(community_snippets) > 100:
        import random
        community_snippets = random.sample(community_snippets, 100)
        
    # Normalize player_type to lowercase & strip whitespace for safe matching
    clean_player = str(player_type).strip().lower()
    
    # Extract player psychology language with normalized matching
    player_snippets = player_df[player_df['nickname'].astype(str).str.strip().str.lower() == clean_player].to_dict('records')
    
    # Loud Failure Guard for empty vocabulary
    if not player_snippets:
        raise ValueError(f"CRITICAL ERROR: Vocabulary lookup failed for player type '{player_type}'. Check spelling, casing, or ensure the vocabulary CSV is fully updated.")

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
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_type = player_type.replace(' ', '')
    profile_path = PROFILES_DIR / f"profile_{scenario_id}_{clean_type}_{ts}.json"
    
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
    """Calls Claude to generate the scenario and snippets table."""
    response = client.messages.create(
        model=GENERATOR_MODEL,
        max_tokens=4096, 
        temperature=0.7,
        system=system_prompt,
        tools=[{
            "name": "generate_scenario_output",
            "description": "Output the generated scenario and snippets.",
            "input_schema": GENERATOR_SCHEMA
        }],
        tool_choice={"type": "tool", "name": "generate_scenario_output"},
        messages=[{"role": "user", "content": user_message}]
    )
    
    for block in response.content:
        if block.type == 'tool_use':
            result_dict = block.input
            raw_json_str = json.dumps(result_dict) 
            return result_dict, raw_json_str
            
    raise ValueError("Claude failed to use the generation tool.")

def regenerate_until_in_range(result: dict, raw: str, system_prompt: str, user_msg: str):
    """Forces the word count into the 280-340 sweet spot using Claude."""
    scenario_text = result.get("scenario", "")
    current_wc = word_count(scenario_text)
    attempts = 0

    while (current_wc < WORD_COUNT_MIN or current_wc > WORD_COUNT_MAX) and attempts < WORD_COUNT_RETRIES:
        attempts += 1
        log("word-count", f"Attempt {attempts}: count is {current_wc}. Regenerating...")
        
        correction = f"\n\nCRITICAL FIX: Your previous scenario was {current_wc} words. You MUST write strictly between {WORD_COUNT_MIN} and {WORD_COUNT_MAX} words."
        
        try:
            response = client.messages.create(
                model=GENERATOR_MODEL,
                max_tokens=4096,
                temperature=0.6,
                system=system_prompt,
                tools=[{
                    "name": "generate_scenario_output",
                    "description": "Output the generated scenario and snippets.",
                    "input_schema": GENERATOR_SCHEMA
                }],
                tool_choice={"type": "tool", "name": "generate_scenario_output"},
                messages=[{"role": "user", "content": user_msg + correction}]
            )
            
            for block in response.content:
                if block.type == 'tool_use':
                    result = block.input
                    raw = json.dumps(result)
                    scenario_text = result.get("scenario", "")
                    current_wc = word_count(scenario_text)
                    break
        except Exception as e:
            log("error", f"API or JSON decode failed on retry: {str(e)}")
            break

    if WORD_COUNT_MIN <= current_wc <= WORD_COUNT_MAX:
        log("word-count", f"SUCCESS! Word count settled at {current_wc}.")
    else:
        log("word-count", f"WARNING: Failed to hit word count target. Final count: {current_wc}.")

    return result, raw

def validate(result: dict) -> list:
    """Validates the output tags against the controlled legal vocabularies."""
    issues = []
    for i, snip in enumerate(result.get('snippets', [])):
        sid = f"snippet[{i}]"
        
        # 1. Grab the signal type
        stype = snip.get('kind_of_signal', '')
        
        # 2. SAFETY FIX: If Claude returned a list, grab the first item inside it
        if isinstance(stype, list):
            stype = stype[0] if len(stype) > 0 else ""
            
        if stype not in LEGAL_KINDS:
            issues.append(f"{sid}: invalid kind_of_signal '{stype}'")
            
        for n in snip.get('unmet_need', []):
            if n not in LEGAL_NEEDS:
                issues.append(f"{sid}: invalid unmet_need '{n}'")
                
        for t in snip.get('possible_trauma', []):
            if t not in LEGAL_TRAUMAS:
                issues.append(f"{sid}: invalid possible_trauma '{t}'")
                
        for trait in snip.get('unes_traits', []):
            if trait != "Not Found" and not (trait.endswith("-high") or trait.endswith("-low")):
                issues.append(f"{sid}: unes_trait '{trait}' missing -high/-low suffix")
                
    return issues

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
                
                # STEP 4.5: Validate Controlled Vocabulary
                log("step 4.5", "Validating controlled vocabularies against legal tags...")
                issues = validate(result)
                if issues:
                    log("VALIDATION WARNING", f"{len(issues)} issues found in {scenario_id}:")
                    for issue in issues:
                        print(f"  -> {issue}")

                # STEP 5: Save (Cleanup removed, Timestamp added)
                log("step 5", "Saving new version with timestamp...")
                
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = OUTPUTS_DIR / f"{scenario_id}_final_{ts}.json"
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                    
                log("SUCCESS", f"Final JSON saved to: {output_path.name}")
                
                success = True # Break out of the retry loop
                
                # Standard API cooldown to stay under 15 Requests Per Minute
                time.sleep(12) 

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "503" in error_msg or "UNAVAILABLE" in error_msg:
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
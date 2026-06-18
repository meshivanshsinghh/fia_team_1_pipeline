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
        "satellite_signals": {"type": "string", "description": "Satellite signals observed in the scenario"},
        "dismissible_red_flags": {"type": "string", "description": "Why each red flag is dismissible to the narrator"},
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
                    "kind_of_signal": {"type": "array", "items": {"type": "string"}, "description": "Signal types from: Behavioral Red Flag, Internal Red Flag, Cultural/Demographic Information, Power Information, Loaded Language"},
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

    # Build unique primary metaphors for this player type
    metaphors = []
    seen_metaphors = set()
    for s in player_snippets:
        m = s.get("primary_metaphor", "")
        if pd.notna(m) and m and m not in seen_metaphors:
            seen_metaphors.add(m)
            metaphors.append(m)

    # Build Object
    profile = {
        "scenario_metadata": {
            "scenario_id": scenario_id,
            "target_register": register,
            "player_type": player_type
        },
        "primary_metaphors": metaphors,
        "manipulation_vocabulary": [
            {
                "mechanism": s.get("tell_mechanism", "Unknown") if pd.notna(s.get("tell_mechanism")) else "Unknown",
                "his_language": s.get("his_language", "") if pd.notna(s.get("his_language")) else "",
                "her_experience": s.get("her_experience", "") if pd.notna(s.get("her_experience")) else "",
                "expert_notices": s.get("what_expert_notices", "") if pd.notna(s.get("what_expert_notices")) else ""
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

def get_pathological_poles(player_type, df):
    row = df[df['Player Type'].str.lower().str.strip() == player_type.lower().strip()]
    if row.empty:
        return []
    row = row.iloc[0]
    
    poles = []
    for col in df.columns:
        if '(' in col and '10' in col and '0' in col:
            val = str(row[col])
            nums = re.findall(r'\d+', val)
            if not nums: continue
            avg_val = sum(int(n) for n in nums) / len(nums)
            
            trait_name = col.split('(')[0].strip()
            if avg_val >= 7:
                poles.append(f"{trait_name}: High")
            elif avg_val <= 3:
                poles.append(f"{trait_name}: Low")
    return poles

def build_user_message(scenario_id, register, player_type, demographics, geo, cultural, source, linguistic_profile_json, poles):
    poles_str = "\n".join([f"- {p}" for p in poles]) if poles else "- None extracted"
    return f"""
SCENARIO ID: {scenario_id}

============================================================
PLAYER TYPE & LINGUISTIC PROFILE
============================================================
The partner in this scenario is a: {player_type}

Diagnostic Trait Extremes (Pathological Poles):
{poles_str}

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

def normalize_result(result: dict) -> dict:
    """Normalizes types in the generator output to ensure schema consistency."""
    # satellite_signals: if Claude returned a list, join to string
    ss = result.get('satellite_signals', '')
    if isinstance(ss, list):
        result['satellite_signals'] = '; '.join(str(s) for s in ss)
    
    # dismissible_red_flags: if Claude returned a list, join to string
    drf = result.get('dismissible_red_flags', '')
    if isinstance(drf, list):
        result['dismissible_red_flags'] = '; '.join(str(s) for s in drf)
    
    # kind_of_signal in snippets: if Claude returned a string, wrap in list
    for snip in result.get('snippets', []):
        kos = snip.get('kind_of_signal', [])
        if isinstance(kos, str):
            snip['kind_of_signal'] = [kos]
    
    return result


def validate(result: dict) -> list:
    """Validates the output tags against the controlled legal vocabularies."""
    issues = []
    
    # Check for missing snippets
    snippets = result.get('snippets', [])
    if not snippets:
        issues.append("CRITICAL: No snippets generated in output")
        return issues
    
    for i, snip in enumerate(snippets):
        sid = f"snippet[{i}]"
        
        # Validate kind_of_signal (expected: array after normalization)
        signals = snip.get('kind_of_signal', [])
        if isinstance(signals, str):
            signals = [signals]
        for sig in signals:
            if sig not in LEGAL_KINDS:
                issues.append(f"{sid}: invalid kind_of_signal '{sig}'")
            
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


def check_repetition(result: dict) -> list:
    """Checks for common AI-tell patterns and repeated phrases in the scenario."""
    issues = []
    scenario = result.get('scenario', '')
    if not scenario:
        return issues
    
    # 1. Em dashes in prose (AI-tell per construction prompt checklist)
    em_dash_count = scenario.count('\u2014')  # — character
    if em_dash_count > 0:
        issues.append(f"AI-tell: {em_dash_count} em dash(es) in scenario text")
    
    # 2. "it's not just X, it's Y" construction
    not_just = re.findall(r"it[\u2019']?s not just .+?, it[\u2019']?s", scenario, re.IGNORECASE)
    if not_just:
        issues.append(f"AI-tell: 'it's not just X, it's Y' construction found ({len(not_just)}x)")
    
    # 3. Three-clause em-dash sentences (X — Y — Z)
    triple_dash = re.findall(r'\w+\s*[\u2014—]\s*\w+\s*[\u2014—]\s*\w+', scenario)
    if triple_dash:
        issues.append(f"AI-tell: three-clause em-dash sentence found")
    
    # 4. Repeated 8+ word spans within the scenario
    words = scenario.lower().split()
    seen_phrases = {}
    for i in range(len(words) - 7):
        phrase = ' '.join(words[i:i+8])
        phrase_clean = re.sub(r'[^\w\s]', '', phrase)
        if phrase_clean in seen_phrases and seen_phrases[phrase_clean] != i:
            orig_words = scenario.split()
            orig_phrase = ' '.join(orig_words[i:i+8])
            issues.append(f"Repetition: 8-word phrase repeated: '{orig_phrase}'")
            break  # Report first instance only to avoid noise
        seen_phrases[phrase_clean] = i
    
    # 5. Overused praise words (closure word should appear 2-3 times, not more)
    praise_words = ['sweet', 'amazing', 'incredible', 'wonderful', 'perfect', 'blessed']
    for word in praise_words:
        count = len(re.findall(rf'\b{word}\b', scenario, re.IGNORECASE))
        if count > 3:
            issues.append(f"Repetition: '{word}' used {count} times (prompt says 2-3 max)")
    
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
    typologies_df = pd.read_csv(HERE / "Player Typologies and Dimensions-AI Agent May 2026 - Players.csv")
    
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
                # STEP 1: Extract Context & Register (with caching)
                context_cache_path = PROFILES_DIR / f"context_{scenario_id}.json"
                if context_cache_path.exists():
                    log("step 1", "Loading context from cache...")
                    with open(context_cache_path, 'r', encoding='utf-8') as f:
                        context = json.load(f)
                else:
                    log("step 1", "Extracting context via classifier...")
                    context = classify_source_story(source_story, available_registers)
                    with open(context_cache_path, 'w', encoding='utf-8') as f:
                        json.dump(context, f, indent=2, ensure_ascii=False)
                        
                register = context['ideological_register']
                
                # STEP 2: Build Linguistic Profile
                log("step 2", f"Building linguistic profile for {register} + {player_type}...")
                profile_dict, profile_path = build_linguistic_profile(
                    scenario_id, register, player_type, community_df, player_df
                )
                log("step 2.5", f"Profile saved to: {profile_path.name}")
                
                # STEP 2.7: Get Pathological Poles
                log("step 2.7", "Extracting pathological poles from typologies...")
                poles = get_pathological_poles(player_type, typologies_df)
                
                # STEP 3: Generate
                log("step 3", "Generating scenario & snippets...")
                profile_json_string = json.dumps(profile_dict, indent=2)
                user_msg = build_user_message(
                    scenario_id, register, player_type, 
                    context['demographics'], context['geographic_setting'], 
                    context['cultural_context'], source_story, profile_json_string, poles
                )
                
                result, raw = generate_scenario(system_prompt, user_msg)
                
                # STEP 4: Check Word Count Constraints
                log("step 4", "Validating word count constraints...")
                result, raw = regenerate_until_in_range(result, raw, system_prompt, user_msg)
                
                # Normalize output types for consistency
                result = normalize_result(result)
                
                # STEP 4.5: Validate Controlled Vocabulary
                log("step 4.5", "Validating controlled vocabularies against legal tags...")
                issues = validate(result)
                if issues:
                    log("VALIDATION WARNING", f"{len(issues)} tag issues in {scenario_id}:")
                    for issue in issues:
                        print(f"  -> {issue}")
                
                # STEP 4.6: Check for AI-tells and repetition
                rep_issues = check_repetition(result)
                if rep_issues:
                    log("REPETITION CHECK", f"{len(rep_issues)} issues in {scenario_id}:")
                    for issue in rep_issues:
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
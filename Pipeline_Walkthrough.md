# Team 1 Scenario Generation Pipeline: Comprehensive Architecture

This document provides a complete, end-to-end architectural walkthrough of the Team 1 Scenario Generation Pipeline. It details how the pipeline ingests source stories and player typologies, dynamically builds custom linguistic profiles, enforces psychological and schematic constraints, and outputs rigorously formatted JSON scenarios and snippet tables for the FIA project.

---

## 1. Core Data Inputs

The pipeline draws upon a series of master data documents to build its generations:
* **`source_stories.csv`**: Contains the baseline, late-stage source stories and assigns each story a specific `player_type` (e.g., *Menacing Marley*, *Manipulative Morgan*).
* **`snippets.csv`**: A repository of community-specific phrases tagged by `culture` (i.e., ideological register).
* **`Player Typologies and Dimensions-AI Agent May 2026 - Players.csv`**: The master matrix defining the 0–10 scaled trait scores for every player type.
* **`FIA_Player_Vocabulary_MASTER-05-27-26.csv`**: The master dictionary mapping each player type to specific manipulation mechanisms, quotes (`his_language`), narrator internalizations (`her_experience`), and `primary_metaphors`.

---

## 2. Pipeline Execution Flow

The pipeline (`team1_pipeline.py`) runs each story through a strict 5-step sequence, utilizing a multi-agent Claude framework (`claude-haiku-4-5` for classification, `claude-sonnet-4-6` for generation).

### Step 1: Context Classification & Caching (Claude Haiku)
Before generating a scenario, the pipeline must decide *where* and *how* the scenario is situated. It passes the raw source story to a fast classification prompt that analyzes the text and outputs:
1. `ideological_register` (e.g., Progressive, Traditional, Wellness, Corporate)
2. `demographics`
3. `geographic_setting`
4. `cultural_context`

**Deterministic Caching**: To prevent ideological drift and save API costs on reruns, this classification is cached locally to `profiles/context_{scenario_id}.json`. If the pipeline is run again on the same scenario, it loads the frozen context.

### Step 2: The Linguistic Profile Builder
The pipeline then dynamically assembles a psychological and linguistic profile customized for both the chosen ideological register and the specific player type.
1. **Community Vocabulary**: It randomly selects up to 100 phrases from `snippets.csv` that match the target ideological register, providing the cultural "dress" for the scenario.
2. **Manipulation Vocabulary**: It searches the Player Vocabulary CSV to extract every relevant row for the assigned player type. It extracts `his_language`, `tell_mechanism`, `what_expert_notices`, and crucially, the narrator's internal monologue (`her_experience`).
3. **Primary Metaphors**: It parses out the unique cognitive frames (e.g., *Relationship-as-Stage*, *Emotion-as-Irrationality*) utilized by the player.
4. **Pathological Poles**: It computes the 0–10 trait scores from the Typologies matrix. Scores of ≥7 or ≤3 are translated into explicit pathological extremes (e.g., `Intensity: Low`, `Disrespect: High`) so the generator clearly understands the *direction* of the psychological pathology rather than just a raw number.

This data is saved to `profiles/profile_{scenario_id}_{player_type}_{timestamp}.json` as an artifact and passed to the generation prompt.

### Step 3: Generation via Anthropic Tool Use (Claude Sonnet)
With the full profile built, the pipeline feeds everything to Claude Sonnet alongside the master prompt (`FIA_Construction_Prompt_v2.md`). 

Instead of asking the LLM to return raw JSON text, the pipeline utilizes **Anthropic Tool Use**. It defines a strict `GENERATOR_SCHEMA` requiring the LLM to output:
* Metadata fields (`architecture_name`, `culture`, `demographics`, `core_behaviors`)
* Analysis fields (`satellite_signals`, `dismissible_red_flags`)
* The `scenario` text itself.
* The `snippets` array (containing 17–24 snippets, each with a quote and detailed diagnostic tags).

This unified schema eliminates the need for separate generation and metadata "backfill" passes.

### Step 4: Strict Validation & Type Normalization
LLMs are prone to type coercion (e.g., returning a comma-separated string instead of a JSON array). Before saving, the pipeline passes the result through an aggressive validator:
1. **Type Normalization (`normalize_result`)**: Forces `kind_of_signal` into an array and joins `satellite_signals` into strings to ensure perfect alignment with downstream UI tools.
2. **NaN Sanitization**: Scans for and removes any `NaN` values that leaked from empty pandas cells, replacing them with empty strings to guarantee valid JSON serialization.
3. **Word Count Constraints**: Enforces a strict 280–340 word limit on the scenario. If violated, it automatically prompts Claude to rewrite it up to 2 times.
4. **Controlled Vocabulary Validation (`validate`)**: Checks every generated snippet tag (`unmet_need`, `possible_trauma`, `unes_traits`) against the hardcoded legal sets. Trait tags are verified to ensure they have the required `-high` or `-low` suffix.

### Step 5: AI-Tell & Repetition Scrubbing
The script scans the final scenario text for common "AI-Tells" and poor style patterns flagged by the design team:
* Flags the use of em dashes in prose.
* Flags parallel "it's not just X, it's Y" sentence constructions.
* Ensures overly effusive praise words ("sweet", "amazing", "incredible") are used a maximum of 3 times to prevent saccharine outputs.

The finalized JSON is then written to the `outputs/` directory.

---

## 3. Post-Processing: Cross-Scenario Deduplication

LLMs tend to fall into repetitive phrasing across large batches. To maintain the illusion of unique authors across the corpus, we utilize a separate script: `dedup_check.py`.

After generating a full batch of 25 scenarios, this script is run against the `outputs/` directory. It tokenizes every scenario, extracts all 8-word sequences (n-grams), and compares them globally across the entire corpus. If any 8+ word phrase appears identically in more than one scenario, the script flags it, prints the overlapping phrase, and lists the affected files so the team can manually review or regenerate them.

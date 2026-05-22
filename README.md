# FIA Scenario Generation Pipeline

This project generates a scenario JSON output from a source story, a snippet library, and a construction prompt.

## Requirements

- Python 3.10+ recommended
- A virtual environment in `.venv/`
- A `.env` file in the project root with one of these API keys:
  - `GEMINI_API_KEY`
  - `GOOGLE_API_KEY`

The script also reads these files from the project root:

- `snippets.csv`
- `FIA_Construction_Prompt_v2.md`

## Install

If you do not already have dependencies installed in your virtual environment:

```bash
source .venv/bin/activate
pip install google-genai pandas python-dotenv
```

## Configure

Create a `.env` file in the project root if you do not already have one:

```env
GEMINI_API_KEY=your_api_key_here
```

Optional model overrides:

```env
GEMINI_CLASSIFIER_MODEL=gemini-3.1-pro-preview
GEMINI_GENERATOR_MODEL=gemini-3.1-pro-preview
```

You can edit the input values directly near the top of `team1_pipeline.py`:

- `SCENARIO_ID`
- `LATE_STAGE_SOURCE`
- `DEMOGRAPHICS`
- `GEOGRAPHIC_SETTING`
- `CULTURAL_CONTEXT`
- `OVERRIDE_REGISTER` if you want to skip the classifier

## Run

From the project root:

```bash
source .venv/bin/activate
python team1_pipeline.py
```

## Output

The script writes a timestamped JSON file into `outputs/`.

## Notes

- If identity fields are blank, the script tries to extract them from the source story.
- If `OVERRIDE_REGISTER` is set, the pipeline skips register classification.
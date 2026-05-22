"""FIA Scenario Generation Pipeline — local Python version."""

import os
import re
import json
import random
import datetime
from pathlib import Path
from collections import Counter

from google import genai
from google.genai import types
import pandas as pd
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")

CSV_PATH = HERE / "snippets.csv"
PROMPT_PATH = HERE / "FIA_Construction_Prompt_v2.md"
OUTPUTS_DIR = HERE / "outputs"

CLASSIFIER_MODEL = os.environ.get("GEMINI_CLASSIFIER_MODEL", "gemini-3.1-pro-preview")
GENERATOR_MODEL = os.environ.get("GEMINI_GENERATOR_MODEL", "gemini-3.1-pro-preview")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

WORD_COUNT_MIN = 280
WORD_COUNT_MAX = 340
WORD_COUNT_RETRIES = 2

# Set to a register name (e.g. "Black Manosphere") to skip Stage 1 and use that.
# Leave as None to let the classifier pick.
OVERRIDE_REGISTER = None

if not GEMINI_API_KEY:
    raise EnvironmentError("Set GEMINI_API_KEY or GOOGLE_API_KEY in .env")

client = genai.Client(api_key=GEMINI_API_KEY)


# ============================================================
# SCENARIO INPUTS — edit per run
# ============================================================

SCENARIO_ID = "S-003"

LATE_STAGE_SOURCE = """
I recently made the difficult decision to break up with my partner. The decision came after he made plans to party on my birthday instead of spending it with me. I was really hurt and didn't have the energy to respond to his messages throughout the day. He was texting me, saying things like 'Yea bye, talk to me when you want to apologize' and 'Answer me or else. Like what is wrong with you.' I finally replied around midnight, after thinking long and hard about how to break up with him. During our conversation, he tried to apologize by saying, 'Hey im sorry, idk what happened to me. You know i love [unclear] ight? And you love me too.' Despite his apologies, I stood firm in my decision, telling him he couldn't come over when he asked. He responded with 'What does that mean, you cant make me not come' and accused me of being 'an [unclear]' for not answering sooner. This was one of the hardest things I've done because he was someone I wanted to marry. Now, I'm trying to move on and appreciate the support I've received from others.
"""

# Identity constraints. If blank, Stage 0 attempts extraction from source.
# If extraction returns Unknown, pipeline refuses to proceed.
DEMOGRAPHICS = "Narrator: F/22, Ghanaian immigrant, first-gen college student, part-time job; Partner: M/26, Ghanaian immigrant"
GEOGRAPHIC_SETTING = "Boston, Massachusetts"
CULTURAL_CONTEXT = "African immigrant family expectations for marriage; first-gen daughterly duty; community gatherings over individual celebrations; pressure to marry within the community"


# ============================================================
# CULTURE / REGISTER DEFINITIONS
# ============================================================

CULTURE_DEFINITIONS = {
    "Old-Money WASP": {
        "definition": "Inherited wealth across generations. Prep schools, Ivy League networks, summer compounds, debutante traditions. Speech avoids ostentation; status signaled through institutions, family names, and what's left unsaid. Understated dress, restraint, lineage references.",
        "distinguishing_markers": "Family names that function as institutions ('the Cabots,' 'Whitneys'), prep school references (Andover, Exeter, Choate, Groton), summer compounds (Nantucket, the Vineyard, Bar Harbor), Episcopalian/Congregationalist church, debutante balls, understated tweed/Barbour aesthetic, 'summering' as a verb.",
        "commonly_confused_with": "Black Professional (both elite-class — WASP is Ivy/Episcopalian/inherited; Black Professional is HBCU/Divine Nine). Hustle Culture (WASP disclaims effort and inherits; HC celebrates effort and earns).",
    },
    "Mormon": {
        "definition": "Latter-day Saints faith. Family-centered theology, modesty norms, missionary culture, BYU/Utah networks. Vocabulary: 'the church,' 'ward,' 'stake,' 'temple recommend,' 'eternal family.' Patriarchal authority embedded in religious doctrine; women's roles framed as divinely appointed.",
        "distinguishing_markers": "LDS-specific theology: temple sealings, eternal family, mission references ('served in Bolivia for two years'), BYU/Provo/Utah, ward and stake structure, modest garments, large families (5+ kids), Word of Wisdom (no coffee/alcohol).",
        "commonly_confused_with": "Evangelical (Mormon has LDS-specific theology — temples, sealings, prophets; Evangelical is born-again Protestant). Tradwife-Recruiting (Mormon is grounded in actual LDS theology and community; Tradwife uses surface religious aesthetic without specific denomination).",
    },
    "Bay Area Rationalist / EA": {
        "definition": "LessWrong and Effective Altruism milieu. AI safety concerns, polyamory common, Berkeley/SF tech overlap. Vocabulary: 'epistemics,' 'priors,' 'steelman,' 'high-decoupling,' 'expected value.' Self-presentation as ultra-rational; emotions framed through theory and explicit modeling.",
        "distinguishing_markers": "Rationalist vocabulary: 'epistemics,' 'priors,' 'Bayesian,' 'steelman,' 'high-decoupling,' 'scout mindset,' 'expected value.' AI safety / alignment references. LessWrong / Astral Codex Ten / EA Forum references. Berkeley/SF tech, often poly, often vegan/utilitarian.",
        "commonly_confused_with": "Polyamorous (heavy overlap — pick BAR/EA when rationalist epistemic vocabulary dominates over ENM relationship-structure vocabulary). Hustle Culture (BAR/EA is decoupling/rational; HC is grind/output). Wellness-Spiritual (BAR is rational and theory-driven; WS is somatic and intuition-driven).",
    },
    "Kink/BDSM": {
        "definition": "Power-exchange relationships within consent-culture framing. Dominant/submissive dynamics, scene/munch/play-party scaffolding, protocol vocabulary. Language around 'safe, sane, consensual' or 'risk-aware consensual kink' used both to enable healthy dynamics and to mask coercive ones.",
        "distinguishing_markers": "Explicit D/s vocabulary: 'scene,' 'munch,' 'play party,' 'aftercare,' 'subspace,' 'safe word,' 'protocol,' 'contract,' 'collar.' 'SSC' (safe sane consensual) or 'RACK' (risk-aware consensual kink). Leather/rope/cuff references.",
        "commonly_confused_with": "Polyamorous (frequent overlap — Kink is about power-exchange dynamics, Poly is about relationship structure). Wellness-Spiritual (somatic vocabulary overlaps — Kink has explicit D/s frame; WS has feminine-energy frame).",
    },
    "Conspiracy": {
        "definition": "Anti-institutional worldview. 'Do your own research,' 'wake up,' 'they don't want you to know.' Distrust of mainstream media, science, government, pharma. Truth framed as hidden, requiring decoding by the in-group.",
        "distinguishing_markers": "'Do your own research,' 'wake up,' 'red-pilled' (in conspiracy sense), 'the matrix,' 'they don't want you to know.' Alternative media references (Joe Rogan, Tucker Carlson, Telegram, X spaces). Skepticism toward Big Pharma, mainstream science, government, MSM.",
        "commonly_confused_with": "MAGA (frequent overlap — pick Conspiracy when anti-institutional framing dominates rather than political faction). Wellness-Spiritual (anti-Big-Pharma overlap — Conspiracy is political-distrust-driven, WS is healing-driven).",
    },
    "Red Pill": {
        "definition": "Manosphere ideology. 'Alpha/beta/sigma' hierarchy, sexual market value, anti-feminist framing. Vocabulary: 'hypergamy,' 'frame,' 'AWALT,' 'feminine energy,' 'high-value man.' Masculinity as discipline, dominance, and women-management.",
        "distinguishing_markers": "Manosphere vocabulary: 'alpha/beta/sigma,' 'hypergamy,' 'frame,' 'AWALT,' 'SMV,' 'high-value man.' Lifestyle markers: cold plunge, seed oils, supplements (tongkat ali, ashwagandha), Muay Thai/boxing, OMAD, sales-coaching/SMMA. White-coded manosphere ecosystem (Tate, Peterson, Huberman, Rogan).",
        "commonly_confused_with": "Black Manosphere (use BM when partner is Black or operates in Black cultural context; Red Pill is the white-coded variant). Hustle Culture (grind framing overlaps — RP is gender ideology, HC is entrepreneurial). Bay Area Rationalist (both can claim rationality — RP is anti-feminist, BAR is decoupling-focused).",
    },
    "Wellness-Spiritual": {
        "definition": "Yoga, meditation, energy work, somatic healing, trauma vocabulary. Phrases: 'feminine energy,' 'aligned,' 'high vibration,' 'manifesting,' 'shadow work,' 'safe in your body.' Spiritual development framed as personal growth; suffering reframed as soul lessons.",
        "distinguishing_markers": "'Feminine energy,' 'aligned,' 'high vibration,' 'manifesting,' 'shadow work,' 'safe in your body,' 'nervous system,' 'somatic,' 'trauma-informed,' astrology references, plant medicine (ayahuasca, mushrooms), yoga/meditation centrality.",
        "commonly_confused_with": "Polyamorous (poly self-work vocabulary overlaps — WS lacks ENM markers). Bay Area Rationalist (both growth-coded — WS is somatic/intuitive, BAR is rational/decoupling). Conspiracy (anti-Big-Pharma overlap — WS is healing-driven, Conspiracy is political-distrust-driven). Recovery (both transformation-coded — Recovery has 12-step framework).",
    },
    "Recovery / 12-Step": {
        "definition": "AA/NA and adjacent fellowships. Sponsorship, sober identity, 'rigorous honesty,' 'higher power,' 'making amends,' 'character defects,' 'one day at a time.' Recovery vocabulary used to frame relationships, personal failings, and the partner's growth.",
        "distinguishing_markers": "AA/NA specific: 'my sponsor,' 'sober date' / 'X years sober,' 'step work,' 'rigorous honesty,' 'higher power,' '90 in 90,' 'amends,' 'character defects,' 'one day at a time,' 'big book.' Meetings as social structure.",
        "commonly_confused_with": "Wellness-Spiritual (both transformation-coded — Recovery has the explicit 12-step structure and sponsor/meeting vocabulary). Evangelical (both faith-adjacent — Recovery is fellowship-based and denomination-agnostic).",
    },
    "Modern Orthodox Jewish": {
        "definition": "Halachic observance with engagement in secular world. Shomer Shabbos, kashrut, tznius (modesty), shidduch dating, yeshiva/seminary background. Hebrew and Yiddish vocabulary woven through English.",
        "distinguishing_markers": "Hebrew/Yiddish vocabulary: 'baruch Hashem,' 'beshert,' 'frum,' 'shul,' 'shomer,' 'shidduch,' 'kollel.' Shabbos observance, kashrut, tznius (modesty). Yeshiva/seminary/Israel year references. Modern Orthodox specifically — engages with secular world unlike Haredi.",
        "commonly_confused_with": "Conservative Sunni Muslim (both observant religious with family-mediated dating; distinguish by Hebrew vs. Arabic religious vocabulary and specific theology).",
    },
    "MAGA": {
        "definition": "Trump-aligned populist conservative. 'America First,' anti-elite framing, patriot identity, working-class claims (regardless of actual class). Vocabulary: 'real Americans,' 'fake news,' 'the swamp,' 'based,' 'God-fearing.' Strong-man masculinity celebrated.",
        "distinguishing_markers": "'America First,' 'real Americans,' 'the swamp,' 'fake news,' 'based,' 'God-fearing,' 'patriot,' 'the libs,' Trump references, red-state aesthetics, working-class self-identification regardless of actual income, country-music adjacent.",
        "commonly_confused_with": "Christian Nationalism (CN explicitly fuses faith and governance; MAGA is more populist-political and can include non-religious adherents). Conspiracy (frequent overlap — MAGA is faction-aligned, Conspiracy is broader anti-institutional). Tradwife-Recruiting (gender-ideology overlap — MAGA is political, Tradwife is gender-aesthetic). Hustle Culture (working-class entrepreneurialism overlap).",
    },
    "Black Manosphere": {
        "definition": "Intra-Black-community manosphere. Critiques of Black women as 'low-value' or 'pickme,' masculinity defense, dating-market vocabulary adapted to Black cultural context. Vocabulary: 'high-value brotha,' 'modern Black woman,' 'submissive,' 'feminine.'",
        "distinguishing_markers": "Race-specific scarcity framing: 'good Black men are rare,' 'high-value brotha,' 'modern Black woman' (used pejoratively), 'pickme,' 'soft / submissive / feminine' as race-specific virtues. Kevin Samuels-adjacent Black YouTube manosphere figures. AAVE-adjacent phrasing. Intra-Black gender critique.",
        "commonly_confused_with": "Red Pill (use Black Manosphere when partner is Black or operates in Black cultural context; Red Pill is the white-coded variant). Black Professional (BM is gender ideology directed intra-community; BP is class signaling and respectability politics).",
    },
    "Black Professional": {
        "definition": "HBCU networks, Divine Nine Greek letter organizations (AKA, Delta, Alpha, Omega, Boulé, Links), Jack and Jill, Black corporate elite. Code-switching, respectability politics, generational class signaling within the Black community.",
        "distinguishing_markers": "HBCU references (Howard, Morehouse, Spelman, Hampton, FAMU), Divine Nine Greek organizations (AKA, Delta, Alpha Phi Alpha, Omega, Kappa, Sigma Gamma Rho, Zeta), Boulé and Links, Jack and Jill, 'talented tenth,' code-switching references, Black corporate executive context.",
        "commonly_confused_with": "Old-Money WASP (both elite-class signaling — BP is Black institutions, WASP is Ivy/Episcopalian). Black Manosphere (BP is class-respectability; BM is gender ideology). Black Church (BP is class-secular; BC is faith-grounded).",
    },
    "South Asian": {
        "definition": "Hindi/Urdu/Punjabi/Bengali diaspora. Family expectations as central, biodata-style courtship, caste and class consciousness, joint-family structures, Bollywood and regional cinema references. Religious diversity (Hindu, Muslim, Sikh) layered with cultural norms.",
        "distinguishing_markers": "Hindi/Urdu/Punjabi/Bengali vocabulary: 'beta,' 'auntie/uncle' (community elder, not biological), 'biodata,' 'rishta,' 'shaadi.' Joint family references, caste consciousness, Bollywood/regional cinema. Indian/Pakistani/Bangladeshi/Sri Lankan diaspora geography.",
        "commonly_confused_with": "Chinese American (both immigrant family-pressure cultures — distinguish by specific language/cuisine/region). Conservative Sunni Muslim (when narrator is South Asian Muslim — pick CSM if religious vocabulary dominates; SA if family-expectation vocabulary dominates).",
    },
    "Chinese American": {
        "definition": "First and second generation Chinese diaspora. Filial piety, academic and professional pressure, model-minority framing, parental sacrifice narratives. Cantonese or Mandarin family vocabulary mixed with English. Face (mianzi) and family reputation central.",
        "distinguishing_markers": "Mandarin/Cantonese vocabulary, filial piety framing, 'face' (mianzi), parental sacrifice narratives, academic pressure ('Tiger parenting'), model-minority dynamics, 'good schools,' generational immigrant tension (FOB vs. ABC).",
        "commonly_confused_with": "South Asian (both immigrant family-pressure cultures — distinguish by language/cuisine/region/cinema references). Hustle Culture (achievement-coded overlap — CA is family-pressure-driven, HC is self-driven).",
    },
    "Black Church": {
        "definition": "AME, Baptist, COGIC, and adjacent traditions. Gospel music, pastor-led communities, 'saved/sanctified' identity, faith as moral and political framework. 'First lady' (pastor's wife) role, church mother authority, testimony culture.",
        "distinguishing_markers": "AME/Baptist/COGIC/Pentecostal denominations specifically. Gospel music, 'first lady' (pastor's wife), 'church mother,' 'saved and sanctified,' 'blood of Jesus,' shouting/praise, prayer-warrior framing, testimony culture, Sunday hat culture.",
        "commonly_confused_with": "Evangelical (both Protestant Christian — Black Church is historically-Black denominational with specific gospel/testimony/first-lady culture). Black Professional (BC is faith-grounded; BP is class-secular).",
    },
    "Hustle Culture": {
        "definition": "Entrepreneur and self-optimization mindset. 'Grind,' 'side hustle,' 'founder identity,' productivity stack, content creation, 'build in public.' Worth framed through output, ambition, and proximity to success.",
        "distinguishing_markers": "'Grind,' 'side hustle,' 'founder,' 'build in public,' 'rise and grind,' 'no days off,' '1% better,' productivity-stack vocabulary (Notion, Pomodoro, time-blocking), Twitter/X tech-entrepreneur, content creation, 'monetize your passion.'",
        "commonly_confused_with": "Red Pill (lifestyle-optimization overlap — HC is entrepreneurial output, RP is gender ideology). Bay Area Rationalist (both tech-overlap — HC is grind/output, BAR is rational/decoupling). MAGA (working-class entrepreneurialism overlap).",
    },
    "Conservative Sunni Muslim": {
        "definition": "Practicing Sunni observance. Halal dating with family involvement, modest dress (hijab/jilbab), gender-separated socializing, deen as central frame. Arabic religious vocabulary woven through English.",
        "distinguishing_markers": "Arabic religious vocabulary: 'inshallah,' 'alhamdulillah,' 'mashallah,' 'wallahi,' 'subhanallah,' 'deen,' 'ummah.' Halal dating with wali (guardian) involvement, hijab/jilbab modesty, gender-separated socializing, masjid references, 'marriage material.'",
        "commonly_confused_with": "Modern Orthodox Jewish (both observant religious with family-mediated dating — distinguish by Arabic vs. Hebrew religious vocabulary). South Asian (when narrator is South Asian Muslim — pick CSM if religious vocabulary dominates, SA if family-cultural vocabulary dominates).",
    },
    "Evangelical": {
        "definition": "Born-again Protestant Christianity. Purity culture, 'led by the Lord,' church youth groups, covenant marriage, 'biblical womanhood/manhood,' contemporary worship music. Faith framed through personal relationship with Jesus.",
        "distinguishing_markers": "Personal-relationship-with-Jesus framing, 'led by the Lord,' purity culture, covenant marriage, 'biblical womanhood/manhood,' contemporary worship (Hillsong, Bethel, Elevation), youth-group culture, Bible-study small groups, 'walking with God.'",
        "commonly_confused_with": "Christian Nationalism (Evangelical is personal faith; CN explicitly fuses faith and governance). Mormon (Evangelical is Protestant; Mormon is LDS-specific). Tradwife-Recruiting (Evangelical is theological; Tradwife is aesthetic/gender ideology without specific theology). Black Church (Evangelical is racially unmarked or implicitly white; BC is historically Black denominational).",
    },
    "Polyamorous": {
        "definition": "Ethical non-monogamy. NRE (new relationship energy), nesting partners, metamours, kitchen-table polyam, processing-as-relational-labor, 'growth edge' framing. Therapeutic vocabulary used to manage and sometimes obscure relational discomfort.",
        "distinguishing_markers": "ENM-specific vocabulary: 'NRE' (new relationship energy), 'nesting partner,' 'metamour,' 'compersion,' 'kitchen-table polyam,' 'relationship anarchy,' 'relationship menu,' 'growth edge,' 'comp het,' 'hierarchy/non-hierarchy.'",
        "commonly_confused_with": "Wellness-Spiritual (therapeutic self-work vocabulary overlaps — Poly has explicit ENM markers). Kink/BDSM (frequent overlap — Poly is relationship structure, Kink is power exchange). Bay Area Rationalist (overlap in tech-adjacent communities — Poly is structural ENM, BAR is rationalist epistemics).",
    },
    "Tradwife-Recruiting": {
        "definition": "Traditional-femininity ideology. Homemaking content, submission framing, 'high-value man' targeting, anti-feminist domesticity, biblical or natural-law gender roles, modest aesthetic. Often overlaps with Christian or right-coded online content.",
        "distinguishing_markers": "'High-value man,' submission framing, sourdough/raw-milk/farm aesthetic, homemaking-as-vocation, prairie-dress aesthetic, anti-feminist domesticity, 'feminine' as moral category, Instagram/TikTok tradwife creator references, soft Christian aesthetic without deep theology.",
        "commonly_confused_with": "Evangelical (Evangelical is theologically grounded with personal-faith vocabulary; Tradwife is aesthetic/gender-ideology with surface religious framing). Christian Nationalism (CN is broader political-religious; Tradwife is specifically gender-role). Mormon (Mormon has specific LDS theology; Tradwife borrows generic 'biblical' framing without denomination).",
    },
    "Christian Nationalism": {
        "definition": "Faith-and-flag fusion. 'Biblical worldview' governance, 'Judeo-Christian values,' dominion theology, patriarchal authority over family and nation, anti-secular framing. Distinct from Evangelical by political fusion: nation as covenantal entity.",
        "distinguishing_markers": "'Biblical worldview' applied to politics/governance, 'Judeo-Christian values,' 'Christian nation,' dominion theology, 'covenant nation,' postmillennial / Reformed often, patriarchal authority over family AND nation, anti-secular explicit framing, often Reconstructionist/Theonomist references.",
        "commonly_confused_with": "Evangelical (Evangelical is personal-faith focused; CN extends faith into political governance). MAGA (overlap but CN is religiously-framed and theologically-articulated; MAGA is politically-framed and can include non-religious adherents). Tradwife-Recruiting (Tradwife is gender role; CN is broader political-theological).",
    },
}


# ============================================================
# CONTROLLED VOCABULARIES — for Stage 5 validation
# ============================================================

LEGAL_KINDS = {
    "Behavioral Red Flag", "Internal Red Flag",
    "Cultural/Demographic Information", "Power Information", "Loaded Language",
}
LEGAL_NEEDS = {
    "Connection", "Fairness", "Morality", "Reality",
    "Worth", "Autonomy", "Agency", "Safety", "Not Found",
}
LEGAL_TRAUMAS = {
    "Coercive Control", "Gaslighting (DARVO)", "Humiliation",
    "Betrayal / Exploitation", "Emotional Neglect", "Moral Injury",
    "Narcissistic Grandiosity", "Obsessive Attachment / Enmeshment",
    "Psychopathy / Terror", "Not Found",
}


# ============================================================
# UTILITIES
# ============================================================

def log(stage, msg):
    print(f"[{stage}] {msg}")


def strip_fences(text):
    """Remove markdown code fences from a model response."""
    return re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.MULTILINE).strip()


def _gemini_generate(model, system_prompt, user_message, temperature):
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=temperature,
        response_mime_type="application/json",
    )
    response = client.models.generate_content(
        model=model,
        contents=user_message,
        config=config,
    )
    raw = response.text or ""
    return strip_fences(raw)


def call_llm(model, messages, temperature):
    system_prompt = "\n\n".join(m["content"] for m in messages if m.get("role") == "system")
    user_prompt = "\n\n".join(m["content"] for m in messages if m.get("role") != "system")
    return _gemini_generate(model, system_prompt, user_prompt, temperature)


def call_json(model, messages, temperature):
    """Call the LLM and parse the response as JSON. Prints raw response on failure."""
    raw = call_llm(model, messages, temperature)
    try:
        return json.loads(raw), raw
    except json.JSONDecodeError as e:
        print(f"[error] JSON decode failed: {e}")
        print("[error] Raw response:")
        print(raw[:2000])
        raise


# ============================================================
# STAGE 0 — Resolve identity (extract if not provided)
# ============================================================

def extract_identity_from_source(source):
    """Attempt to pull identity from the source story. Returns Unknown where
    nothing is findable in the text — does not invent."""
    prompt = f"""Read this late-stage relationship source story. Extract any concrete
identity information that is EXPLICITLY present in the text. If a field is not
present, return "Unknown" — DO NOT INFER OR INVENT.

Return JSON only, no fences:
{{
  "narrator_demographics": "<age/sex/ethnicity/class if mentioned, else Unknown>",
  "partner_demographics": "<same, else Unknown>",
  "geographic_setting": "<city/region if mentioned, else Unknown>",
  "cultural_framework": "<the cultural lens the narrator uses to read his behavior as virtue, if implied by the text, else Unknown>"
}}

SOURCE STORY:
{source}
"""
    result, _ = call_json(
        CLASSIFIER_MODEL,
        [{"role": "user", "content": prompt}],
        temperature=0,
    )
    return result


def resolve_identity():
    """Use user-provided values if non-blank; else extract from source.
    Refuses to proceed if any required field is still Unknown after extraction."""
    demographics = DEMOGRAPHICS.strip()
    geo = GEOGRAPHIC_SETTING.strip()
    cultural = CULTURAL_CONTEXT.strip()

    needs_extraction = not (demographics and geo and cultural)
    if needs_extraction:
        log("stage 0", "One or more identity fields blank — attempting extraction.")
        extracted = extract_identity_from_source(LATE_STAGE_SOURCE)
        if not demographics:
            n = extracted.get("narrator_demographics", "Unknown")
            p = extracted.get("partner_demographics", "Unknown")
            demographics = f"Narrator: {n}; Partner: {p}"
        if not geo:
            geo = extracted.get("geographic_setting", "Unknown")
        if not cultural:
            cultural = extracted.get("cultural_framework", "Unknown")

        log("stage 0", f"demographics: {demographics}")
        log("stage 0", f"geographic_setting: {geo}")
        log("stage 0", f"cultural_context: {cultural}")

    unknown = []
    if "Unknown" in demographics:
        unknown.append("DEMOGRAPHICS")
    if geo == "Unknown" or "Unknown" in geo:
        unknown.append("GEOGRAPHIC_SETTING")
    if cultural == "Unknown" or "Unknown" in cultural:
        unknown.append("CULTURAL_CONTEXT")
    if unknown:
        raise ValueError(
            f"Cannot proceed — these fields could not be resolved: {unknown}. "
            f"Provide them manually at the top of the file."
        )

    log("stage 0", "Identity resolved.")
    return demographics, geo, cultural


# ============================================================
# STAGE 1 — Classify ideological register
# ============================================================

def classify_register(source, demographics, geo, cultural):
    """Pick the ideological register whose vocabulary library the partner draws
    from. Returns None for the register field if no register genuinely fits."""

    definitions_text = "\n\n".join([
        f"## {name}\n"
        f"Definition: {d['definition']}\n"
        f"Distinguishing markers: {d['distinguishing_markers']}\n"
        f"Commonly confused with: {d['commonly_confused_with']}"
        for name, d in CULTURE_DEFINITIONS.items()
    ])

    prompt = f"""You are classifying the IDEOLOGICAL REGISTER (worldview / vocabulary
source) that the partner most likely draws from. Your classification determines
which register's snippet library the scenario generator will use to write the
partner's honeymoon-phase dialogue.

IMPORTANT: The source story below is a LATE-STAGE account — the partner's mask
has dropped. Late-stage text typically shows raw behavioral patterns (dominance,
entitlement, coercion) WITHOUT the polished ideological vocabulary he would have
used during the honeymoon phase. Do NOT require explicit jargon in the source.
Instead, classify based on the partner's behavioral pattern + demographic context
to determine which ideological ecosystem he most likely operates in.

PROCEDURE — follow for every classification:

1. Read the source story and identify the partner's BEHAVIORAL signature:
   what power moves does he make, what does he feel entitled to, how does he
   frame her resistance? These are the mask-off versions of honeymoon-phase
   ideological moves.

2. Note the demographic context: ethnicity, region, class, age, cultural
   framework. These narrow which VARIANT of an ideological space the partner
   most likely operates in — a Ghanaian-immigrant man showing dominance and
   entitlement patterns is more likely drawing from Black Manosphere media
   than from white-coded Red Pill, even if the late-stage text lacks explicit
   jargon from either.

3. For each candidate register, check three tests:
   (a) Do the partner's behavioral patterns align with the register's
       ideology (dominance framing, entitlement structure, role-casting)?
   (b) Does the demographic context fit a population that typically engages
       with this register's media/community?
   (c) Is there a register in the "commonly confused with" list that would
       fit better given the demographic context?

4. Pick the SINGLE register that survives all three tests. If multiple
   registers fit equally, pick the one whose demographic context is the
   strongest match.

5. Return null ONLY if the partner's behavior is genuinely unclassifiable —
   no dominance ideology, no entitlement framing, no role-casting at all.
   Generic possessiveness or jealousy combined with a clear demographic
   context IS enough to pick a register, because the generator needs a
   vocabulary library to work from.

Return JSON only, no fences:
{{
  "ideological_register": "<exact register name, or null if genuinely unclassifiable>",
  "confidence": "<high | medium | low | none>",
  "reasoning": "<one or two sentences naming the behavioral cues that drove the pick AND which 'commonly confused with' register you ruled out>",
  "runner_up": "<second-best register, or null>"
}}

IDEOLOGICAL REGISTERS:

{definitions_text}

LATE-STAGE SOURCE STORY (mask-off behavior — do not expect honeymoon-phase vocabulary):
{source}

DEMOGRAPHIC CONTEXT (use to narrow register variant):
- Demographics: {demographics}
- Geographic setting: {geo}
- Cultural framework: {cultural}
"""
    result, _ = call_json(
        CLASSIFIER_MODEL,
        [{"role": "user", "content": prompt}],
        temperature=0,
    )
    return result


# ============================================================
# STAGE 2 — Filter snippets by register, sample up to 100
# ============================================================

def filter_snippets(df, register, max_sample=100, random_seed=None):
    """Filter by register; if more than max_sample rows, take a random sample."""
    filtered = df[df['culture'] == register].copy().reset_index(drop=True)
    total = len(filtered)
    log("stage 2", f"{total} total snippets matched register '{register}'")

    if total <= max_sample:
        sampled = filtered
        log("stage 2", f"using all {total} snippets (≤ {max_sample} cap)")
    else:
        seed = random_seed if random_seed is not None else random.randint(0, 2**31)
        sampled = filtered.sample(n=max_sample, random_state=seed).reset_index(drop=True)
        log("stage 2", f"sampled {max_sample} of {total} snippets (seed={seed})")

    return sampled.to_csv(index=False), len(sampled)


# ============================================================
# STAGE 3 — Generate scenario
# ============================================================

def build_user_message(scenario_id, register, demographics, geo, cultural,
                       source, snippets_block):
    return f"""Generate a honeymoon-phase scenario per the construction methodology
in the system prompt. Return ONE JSON object per Step 12 — no prose wrapper,
no markdown fences.

============================================================
IDENTITY CONSTRAINTS — PRESERVE EXACTLY, DO NOT INVENT OR CHANGE
============================================================
These describe WHO THE PEOPLE ACTUALLY ARE. The scenario MUST take place in
this geographic setting, with people matching these demographics, and her
interior framing MUST draw on this cultural framework.

DO NOT:
  - relocate the scenario to a different city or region
  - change the narrator's or partner's ethnicity, class, or immigration status
  - substitute a different cultural framework
  - default to stereotypical demographics associated with the ideological register

- Demographics: {demographics}
- Geographic setting: {geo}
- Cultural framework she reads him through: {cultural}

The partner is the same person as in the late-stage source story. Same
ethnicity, same community, same family situation, same neighborhood.

============================================================
IDEOLOGICAL REGISTER — VOCABULARY SOURCE
============================================================
- Target register: {register}

This is the WORLDVIEW the partner draws his vocabulary, self-declarations,
and framing from. The same person can hold the demographic identity above
AND absorb this register's content (from podcasts, online communities,
peer groups, locker rooms). The register is about WORDS, not identity.

Pull loaded language from the FILTERED SNIPPETS DATASET below. The partner's
dialogue and self-declarations should use the register's vocabulary. The
narrator's interior, her family references, her food, her language about her
own people, and the physical setting should reflect the IDENTITY CONSTRAINTS
above — not the register.

Example of correct integration: a Ghanaian-immigrant partner in Boston who
has absorbed Red Pill podcast content. His dialogue uses "high-value man,"
"feminine energy," "mission" — but he calls his uncle "Uncle Kwame," his
food references are jollof or fufu, he mentions his mother's church, etc.
The register is layered ON the identity, not substituted FOR it.

============================================================
INPUTS
============================================================
- scenario_id: {scenario_id}

LATE-STAGE SOURCE STORY:
{source}

FILTERED SNIPPETS DATASET (culture = "{register}" only — do not pull from other registers):
{snippets_block}

============================================================
OUTPUT REQUIREMENTS
============================================================
- Output JSON `culture` field: "{register}" (the ideological register)
- Output JSON `demographics` field: must echo or refine the constraints above
- Output JSON `geographic_setting` field: must match the constraint above
- Output JSON `cultural_context` field: must reflect the cultural framework above
- scenario_text: 280-340 words. HARD LIMIT.
- Snippet count is honest, not forced. 12 snippets are fine if that is what
  is diagnostically present.
"""


def generate_scenario(system_prompt, user_message):
    return call_json(
        GENERATOR_MODEL,
        [
            {"role": "system", "content": system_prompt + "\n\nReturn JSON only. No prose. No markdown fences."},
            {"role": "user", "content": user_message},
        ],
        temperature=1,
    )


# ============================================================
# STAGE 4 — Word count validation + regeneration
# ============================================================

def word_count(result):
    return len(result['scenario']['scenario_text'].split())


def regenerate_until_in_range(result, raw, system_prompt, user_msg_args):
    """Up to WORD_COUNT_RETRIES additional attempts to land in the word range."""
    for attempt in range(WORD_COUNT_RETRIES + 1):
        wc = word_count(result)
        if WORD_COUNT_MIN <= wc <= WORD_COUNT_MAX:
            log("stage 4", f"word count {wc} within {WORD_COUNT_MIN}-{WORD_COUNT_MAX} — passing.")
            return result, raw

        log("stage 4", f"attempt {attempt}: word count {wc} outside range.")
        if attempt == WORD_COUNT_RETRIES:
            log("stage 4", f"max retries hit — returning {wc}-word version for human review.")
            return result, raw

        # Build a tightening user message that includes the previous output
        base = build_user_message(**user_msg_args)
        tighten = (
            f"\n\n============================================================\n"
            f"REWRITE REQUIRED — PREVIOUS OUTPUT WAS {wc} WORDS\n"
            f"============================================================\n"
            f"Your previous scenario_text was {wc} words. The hard limit is "
            f"{WORD_COUNT_MIN}-{WORD_COUNT_MAX}. Target approximately 310 words.\n\n"
            f"Rewrite the scenario_text while PRESERVING:\n"
            f"  - The architecture_name and the structural moves\n"
            f"  - The IDENTITY CONSTRAINTS (demographics, geo, cultural framework)\n"
            f"  - The closing question\n"
            f"  - The full snippet set (retag against the tightened text)\n\n"
            f"Cut: redundant self-declarations (stack at most one), stacked "
            f"lifestyle markers (pick 2-3 highest-yield), atmosphere beats that "
            f"don't reveal architecture, repeated rationalization phrases.\n\n"
            f"Return the FULL JSON object with the tightened scenario_text and "
            f"updated snippets array.\n\n"
            f"PREVIOUS OUTPUT FOR REFERENCE:\n{raw}\n"
        )
        result, raw = generate_scenario(system_prompt, base + tighten)

    return result, raw


# ============================================================
# STAGE 5 — Controlled vocabulary validation
# ============================================================

def validate(result):
    issues = []
    for i, snip in enumerate(result.get('snippets', [])):
        sid = snip.get('snippet_id', f'snippet[{i}]')
        for k in snip.get('kind_of_signal', []):
            if k not in LEGAL_KINDS:
                issues.append(f"{sid}: invalid kind_of_signal '{k}'")
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
# REPORTING + SAVE
# ============================================================

def report(result, issues):
    s = result['scenario']
    snips = result['snippets']
    wc = word_count(result)
    print()
    print("=" * 70)
    print("REPORT")
    print("=" * 70)
    print(f"scenario_id:      {s.get('scenario_id')}")
    print(f"register/culture: {s.get('culture')}")
    print(f"demographics:     {s.get('demographics')}")
    print(f"geo setting:      {s.get('geographic_setting')}")
    cc = s.get('cultural_context', '')
    print(f"cultural ctx:     {cc[:120]}{'...' if len(cc) > 120 else ''}")
    print(f"architecture:     {s.get('architecture_name')}")
    print(f"word count:       {wc}  (target {WORD_COUNT_MIN}-{WORD_COUNT_MAX})")
    print(f"snippet count:    {len(snips)}")

    all_signals = [sig for snip in snips for sig in snip.get('kind_of_signal', [])]
    print("\nsignal distribution:")
    for sig, n in Counter(all_signals).most_common():
        print(f"  {sig:36s} {n}")

    print("\nvalidation issues:")
    if issues:
        for issue in issues:
            print(f"  {issue}")
    else:
        print("  none")

    print()
    print("=" * 70)
    print("SCENARIO TEXT")
    print("=" * 70)
    print(s['scenario_text'])

    print()
    print("=" * 70)
    print("SNIPPETS")
    print("=" * 70)
    for snip in snips:
        print(f"\n[{snip.get('snippet_id')}] {snip.get('snippet_text')}")
        print(f"  Kind:    {', '.join(snip.get('kind_of_signal', []))}")
        print(f"  UNES:    {', '.join(snip.get('unes_traits', []))}")
        print(f"  Need:    {', '.join(snip.get('unmet_need', []))}")
        print(f"  Trauma:  {', '.join(snip.get('possible_trauma', []))}")
        print(f"  Reason:  {snip.get('reasoning')}")


def save(result, scenario_id):
    OUTPUTS_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUTPUTS_DIR / f"scenario_{scenario_id}_{ts}.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n[save] wrote {out}")


# ============================================================
# MAIN
# ============================================================

def main():
    df = pd.read_csv(CSV_PATH)
    log("setup", f"loaded {len(df)} snippets across {df['culture'].nunique()} cultures")
    system_prompt = PROMPT_PATH.read_text()
    log("setup", f"loaded construction prompt: {len(system_prompt):,} chars")

    missing = set(df['culture'].unique()) - set(CULTURE_DEFINITIONS.keys())
    if missing:
        log("setup", f"WARNING: CSV cultures without definitions: {missing}")

    print()
    log("stage 0", "resolving identity constraints...")
    demographics, geo, cultural = resolve_identity()

    print()
    if OVERRIDE_REGISTER:
        log("stage 1", f"OVERRIDE_REGISTER set — using '{OVERRIDE_REGISTER}'")
        register = OVERRIDE_REGISTER
    else:
        log("stage 1", "classifying ideological register...")
        cls = classify_register(LATE_STAGE_SOURCE, demographics, geo, cultural)
        register = cls.get('ideological_register')
        confidence = cls.get('confidence')

        log("stage 1", f"register: {register}  (confidence: {confidence})")
        log("stage 1", f"reasoning: {cls.get('reasoning')}")
        log("stage 1", f"runner up: {cls.get('runner_up')}")

        if register is None or confidence == "none":
            raise ValueError(
                "Classifier returned no genuine register fit. Either:\n"
                "  (a) The source story has no ideological vocabulary — generate "
                "without a register filter (set OVERRIDE_REGISTER to 'NONE' "
                "and update Stage 2 to skip snippet filtering), OR\n"
                "  (b) Manually set OVERRIDE_REGISTER to the runner-up after "
                "reviewing the reasoning."
            )

        if confidence == "low":
            log("stage 1", "WARNING: low confidence — review reasoning before scaling")

    if register != "NONE" and register not in df['culture'].unique():
        raise ValueError(f"Register '{register}' not in CSV.")

    print()
    log("stage 2", "filtering snippets...")
    snippets_block, n_snippets = filter_snippets(df, register)

    print()
    log("stage 3", "generating scenario...")
    user_msg_args = dict(
        scenario_id=SCENARIO_ID,
        register=register,
        demographics=demographics,
        geo=geo,
        cultural=cultural,
        source=LATE_STAGE_SOURCE,
        snippets_block=snippets_block,
    )
    user_message = build_user_message(**user_msg_args)
    result, raw = generate_scenario(system_prompt, user_message)
    log("stage 3", f"generation complete — {word_count(result)} words, {len(result.get('snippets', []))} snippets")

    print()
    log("stage 4", "validating word count...")
    result, raw = regenerate_until_in_range(result, raw, system_prompt, user_msg_args)

    print()
    log("stage 5", "validating controlled vocabularies...")
    issues = validate(result)
    log("stage 5", f"{len(issues)} issues found" if issues else "all values within controlled vocabularies")

    report(result, issues)
    save(result, SCENARIO_ID)


if __name__ == "__main__":
    main()
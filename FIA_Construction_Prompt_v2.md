# FIA Gold Standard Scenarios — Construction Prompt (v2)

## What you are producing

You are producing a **first-person narrative scenario** and a **structured snippets table**, returned together as a single JSON object (see Step 12 for the output schema).

Each scenario is a 280–340 word first-person narrative written by a woman in the early stages of a relationship. She is largely happy, hopeful, and not alarmed. She is typing into a chatbot to ask about one small thing that is sitting with her. The closing line is the question she is actually asking — everything else is context.

The scenario is the early-stage version of a known late-stage source story: same partner, same eventual trait pattern, weeks or months earlier, before the late-stage manipulation moves have fully developed. Embedded in the narrative are small linguistic, behavioral, cultural, and power signals that allow a trained reader to forecast where the relationship is going, without making the narrator sound unsafe or frightened.

After the scenario, produce 17–24 short quoted phrases or behaviors, in document order, each tagged with the controlled vocabularies defined below and explained briefly.

---

## Inputs

You will receive in the user message, per scenario:

1. **A late-stage source story** — a known, late-stage manipulative or abusive case. The honeymoon-phase scenario must mirror its trait architecture.
2. **A target culture** — one of 21 cultural registers, pre-classified by an upstream step: Old-Money WASP, Mormon, Bay Area Rationalist/EA, Kink/BDSM, Conspiracy, Red Pill, Wellness-Spiritual, Recovery/12-Step, Modern Orthodox Jewish, MAGA, Black Manosphere, Black Professional, South Asian, Chinese American, Black Church, Hustle Culture, Conservative Sunni Muslim, Evangelical, Polyamorous, Tradwife-Recruiting, Christian Nationalism.
3. **A filtered snippets table** — rows from the snippets dataset CSV for the target culture only (typically 30–250 rows). Columns: `culture`, `snippet`, `type`, `translation`, `status_signal`, `notes`. Pull or adapt loaded language from this filtered set rather than inventing phrases. Do not pull from cultures other than the target.
4. **Optional writer hints** — demographics, geographic setting, scenario_id placeholder.

The **29 UNES traits and their honeymoon-form translations** are encoded in Step 2's translation table below. The **controlled vocabularies** for tagging are defined in the Controlled Vocabularies section below. You do not need additional reference material beyond this system prompt and the per-scenario user message.

---

## Outputs

You return **one JSON object** containing two top-level fields:

- `scenario` — the scenario metadata and the 280–340 word narrative
- `snippets` — an ordered array of 17–24 snippet objects, each carrying its text, signal tags, UNES traits, unmet needs, possible trauma, and reasoning

The exact JSON schema is defined in **Step 12 — Output Format**.

---

## Controlled Vocabularies

These are the only allowed values for the tagging fields. If no value in the list genuinely applies to a given snippet, return `"Not Found"` for that field — do not stretch a fit or invent a label. Multi-value tagging is allowed for `kind_of_signal`, `unes_traits`, `unmet_need`, and `possible_trauma`.

### UNES Traits (30 traits, high/low extremes)

Format: `TraitName-high` or `TraitName-low`.

```
Accountability-high           Accountability-low
Attachment-high               Attachment-low
Boundaries-high               Boundaries-low
Charm-high                    Charm-low
Cognitive Flexibility-high    Cognitive Flexibility-low
Conflict-high                 Conflict-low
Control-high                  Control-low
Deception-high                Deception-low
Disrespect-high               Disrespect-low
Dominance-high                Dominance-low
Dysregulation-high            Dysregulation-low
Emotional Overexposure-high   Emotional Overexposure-low
Empathy-high                  Empathy-low
Enmeshment-high               Enmeshment-low
Exploitation-high             Exploitation-low
Goal Persistence-high         Goal Persistence-low
Grandiosity-high              Grandiosity-low
Impulsivity-high              Impulsivity-low
Inconsistency-high            Inconsistency-low
Intensity-high                Intensity-low
Isolation-high                Isolation-low
Neediness-high                Neediness-low
Openness-high                 Openness-low
Perseverance-high             Perseverance-low
Sensation-seeking-high        Sensation-seeking-low
Sense of Self-high            Sense of Self-low
Superficiality-high           Superficiality-low
Trust-high                    Trust-low
Unorthodoxy-high              Unorthodoxy-low
Validation-seeking-high       Validation-seeking-low
```

**Note on Intensity-low**: A partner with pathologically low intensity displays minimal emotional engagement or passion in the relationship. They appear flat, affectless, or unable to generate emotional spark. In honeymoon phase this presents as "calm," "chill," "low-drama," or "easy to be around." Over time, partners feel emotionally starved or undervalued, as if the relationship lacks vitality. The surface presentation suggests stability or easygoingness, but the underlying pattern is emotional withholding and disengagement, leaving the partner to work harder for any meaningful response.

### Unmet Needs (8 values)

```
Connection    — empathy & mutual understanding
Fairness      — equity & justice
Morality      — intuitive integrity
Reality       — truth & coherence
Worth         — recognition & respect
Autonomy      — identity, thoughts, and feelings
Agency        — decisions free from coercion
Safety        — security & predictability
```

### Possible Trauma (9 values)

```
Coercive Control
Gaslighting (DARVO)
Humiliation
Betrayal / Exploitation
Emotional Neglect
Moral Injury
Narcissistic Grandiosity
Obsessive Attachment / Enmeshment
Psychopathy / Terror
```

### Kinds of Signal (5 values)

```
Behavioral Red Flag
Internal Red Flag
Cultural/Demographic Information
Power Information
Loaded Language
```

Every snippet must have at least one `kind_of_signal` value (this field cannot be `"Not Found"`). Single snippets routinely carry 2–4 tags here.

---

## Core principle

The trait is constant; the phase changes the surface. A late-stage husband who pathologizes his wife's hormones may have been, three years earlier, the boyfriend who interrupted her unfinished sentences with affectionate reassurance. Same machine. Different phase.

A trained reader should see both levels:

- **Surface**: romantic, thoughtful, funny, protective, generous, exciting, or culturally normal.
- **Trait level**: creates a role, debt, dependency, asymmetry, obligation, interpretive control, or reduced room to object.

The danger is rarely in the gesture itself. It is in the position the gesture puts her in. Ask of every beat: what role does this assign her?

---

## Step 1 — Score the source story

Use the Predator Scoring Sheet to identify which of the 29 traits are load-bearing in the late-stage source story. For most stories, 3–6 traits do the structural work. Score each on the 0–10 scale where 5 is healthy and both extremes can become unhealthy.

Each load-bearing trait can land at either pathological extreme. A predator profile may include traits at the high end (Validation-seeking 8, Grandiosity 9) alongside traits at the low end (Empathy 1, Accountability 2). Score independently; do not assume clustering.

**Example: S-008 Miguel late-stage source story**

- Accountability: 0–2 (denies, half-apologizes, gaslights)
- Empathy (Affective): 0–2 (dismisses her feelings)
- Control: 8–10 (overrides her perception, defines reality)
- Sensation-seeking: 7–8 (regular weed, vape, drinking)
- Charm: 7–8 (charismatic, plays to the crowd)

---

## Step 2 — Translate each trait into honeymoon form

For each load-bearing trait, identify which pathological extreme it lands at in the source story (0–2 or 8–10). Then translate to the honeymoon-phase form of that specific extreme. The honeymoon form of Conflict-2 (avoidance dressed as easygoing) is structurally different from the honeymoon form of Conflict-9 (aggression dressed as passion).

Ask: what does this trait look like as a virtue before it becomes frightening, exhausting, or coercive?

| Trait | Late-stage 0–2 | Honeymoon 0–2 | Late-stage 8–10 | Honeymoon 8–10 |
|---|---|---|---|---|
| Accountability | Denies, blames, gaslights, "that never happened" | "Doesn't dwell on stuff," "doesn't hold grudges," moves past things easily | Over-apologizes, collapses into guilt, takes blame for things outside his control | "Really self-aware," "always working on himself," "takes responsibility" |
| Attachment | Cold, withdrawn, refuses intimacy, "I don't do feelings" | "Independent," "doesn't need to be in your face," "has his own life" | Suffocating, can't tolerate space, panics at any distance | "Obsessed with you," texts all day, "I've never felt like this," wants to be together constantly |
| Boundaries | No boundaries, oversteps, overshares, ignores "no" | "Open book," "no walls," "you can ask him anything" | Rigid wall, cuts people off, refuses help, won't share space | "Knows what he wants," "principled," "doesn't let people use him" |
| Charm | Affectless, monotone, no warmth, doesn't try | "The strong silent type," "doesn't perform," "refreshing after all those tryhards" | Calculated warmth, plays to crowd, performs intimacy | Life of the party, socially magnetic, everyone loves him |
| Cognitive Flexibility | Rigid, literal, can't shift perspective, demands logical consistency | "Direct," "knows what he thinks," "doesn't get caught up in feelings" | Magical thinking, sees signs everywhere, treats intuition as fact, beliefs shift constantly | "Spiritual," "open-minded," "not stuck in the matrix" |
| Conflict | Avoids, ghosts, shuts down, refuses engagement | "Easygoing," "doesn't fight," "low-drama" | Escalates, bullies, won't drop it, dominates every disagreement | "Passionate," "fights for the relationship," "won't let things slide" |
| Control | No initiative, can't make decisions, lets things fall apart | "Laid back," "goes with the flow," "no ego about being in charge" | Micromanages, decides for her, plans everything, expects compliance | Drives, plans, orders for her, "I got it," "let me take care of this" |
| Deception | Believes everything, falls for scams, no skepticism | "Trusting," "sees the best in people," "not cynical" | Lies fluidly, fabricates, gaslights, leads double life | "Smooth," "tells the best stories," "always has a plan" |
| Disrespect | Praises everything, never pushes back, validates flawed ideas | "Supportive," "always on your side," "non-judgmental" | Contempt, mocking, eye-rolling, dismissive nicknames | Teasing, banter, the running joke at her expense |
| Dominance | Passive collapse, defers to everyone, won't lead | "Easygoing," "no ego," "doesn't need to be in charge" | Overrides, expects deference, takes charge unilaterally | "Confident," "takes charge," "I got it" energy |
| Dysregulation | Affectless, no emotional response, flat | "Steady," "unflappable," "nothing rattles him" | Emotional explosions, mood swings, can't self-regulate | "Passionate," "feels things deeply," "intense" |
| Emotional Overexposure | Shares nothing, won't open up, withholds interior | "Private," "doesn't burden you with his stuff" | Floods her with feelings, trauma-dumps early, makes her his therapist | "Vulnerable," "open with his feelings," "not afraid to be seen" |
| Empathy (Affective) | Doesn't register her feelings, dismissive, "you're overreacting" | "Doesn't get caught up in drama," "keeps a level head" | His feelings flood hers, takes on her emotions as his own | "Really in touch with his emotions," "feels what you feel," "sensitive" |
| Enmeshment | Maintains rigid separation, won't merge any aspect of life | "Has his own life," "respects independence" | Merges everything, can't tolerate her separate self, fast "we" | "We're so in sync," "you're my person," "I've never felt this connected" |
| Exploitation | Refuses to use anyone for anything, won't accept help | "Self-sufficient," "doesn't ask for anything" | Uses her resources, time, labor, social capital systematically | "Appreciates everything you do," "knows how to make use of what people offer" |
| Goal Persistence | Drifts, can't commit to anything, abandons plans | "Goes with the flow," "doesn't get attached to outcomes" | Obsessive about goals, can't drop anything, won't accept "no" | "Driven," "knows what he wants," "doesn't give up" |
| Grandiosity | Self-effacing, won't take any credit, downplays everything | "Humble," "doesn't brag," "modest" | Exceptionalism, contempt for others, scarcity framing | "I'm not like other guys," "you won't find anyone else like me" |
| Impulsivity | Frozen, can't act without exhaustive planning, paralyzed | "Thoughtful," "doesn't rush into things," "careful" | Acts without thinking, spontaneous to a fault, unpredictable | "Spontaneous," "exciting," "lives in the moment" |
| Inconsistency | Rigidly predictable, never varies, no flexibility | "Reliable," "you always know what to expect" | Hot-cold whiplash, mood-dependent, contradicts himself | "Thrilling unpredictability," surprise gestures, emotional highs |
| Intensity | Affectless, low-energy, can't generate spark | "Calm," "easy to be around," "chill" | Overwhelming intensity, all-consuming focus, moves too fast | "I've never felt this way," "you're all I think about" |
| Isolation | Surrounded by everyone, can't be alone, no separation from his social world | "Social," "everyone loves him," "always something going on" | Cuts her off from her people, monopolizes her time, distrusts her relationships | "He just wants me all to himself," "we don't need anyone else" |
| Neediness | Takes nothing from anyone, won't accept comfort or help | "Self-sufficient," "doesn't lean on anyone" | Constantly needs reassurance, can't tolerate being alone, demands access | "He really needs me," "no one's loved him like this before" |
| Perseverance | Drops topics quickly, can't stay focused on anything | "Doesn't dwell," "moves on fast" | Repeats the same arguments, can't let go, returns to old issues compulsively | "Really thinks things through," "doesn't forget what matters" |
| Sensation-seeking | Avoids stimulation, won't try anything new, rigid routine | "Steady," "homebody," "not into chaos" | Constant stimulation, substances, recklessness | Fun party guy, leading shots, "work hard play hard" |
| Sense of Self | No identity, mirrors whoever he's with, no preferences | "Easygoing," "down for whatever," "no strong opinions" | Rigid identity, can't tolerate challenge to self-image, performs constantly | "Knows exactly who he is," "comfortable in his own skin" |
| Superficiality | Only depth, no lightness, can't tolerate small talk | "Deep," "doesn't do small talk," "intense conversations" | All surface, no depth, status-focused, appearance-driven | "Polished," "put-together," "knows how to present himself" |
| Trust | Paranoid, suspicious of everyone, sees threats everywhere | "Streetwise," "doesn't get fooled," "good judge of character" | Trusts everyone blindly, falls for scams, no skepticism | "Trusting," "sees the best in people," "not cynical" |
| Unorthodoxy | Rigid conformity, can't tolerate difference, conventional to a fault | "Traditional," "knows the rules," "respects how things are done" | Rejects all conventions, contrarian for its own sake, lives outside any norm | "Free spirit," "doesn't follow the crowd," "his own person" |
| Validation-seeking | Dismissive of approval, won't perform for anyone | "Doesn't need attention," "secure in himself" | Constant attention-seeking, social media performance, jealousy, surveillance | Love-bombing, centering her, "you're the best thing that's happened to me" |

Do not simply soften the late-stage abuse. Find a different earlier moment where the same mechanism appears in an appealing form.

---

## Step 3 — Name the architecture

Before drafting beats, write one sentence that names what the late-stage trait pattern is in this relationship's specific architecture. The architecture is what the moves are revealing — not what they're doing in isolation.

**Examples from the gold standard database:**

- S-002 (Atlanta): He uses her professional achievements as status fuel for himself while constraining her public self-presentation.
- S-006 (small town / evangelical): He extracts domestic and emotional labor from her under the cover of religious-register approval.
- S-003 (Mesilla): He performs attentive thoughtfulness as the entry move for racialized typecasting and possessive control.

Every move should reveal a piece of this single architecture. If a move doesn't, it's atmosphere — cut it.

**Logic check.** Each move must be something a person holding the partner's worldview would plausibly say or do. A red-pill conservative would not be surprised that a Portland woman is open-minded — he would expect her to be closed off and frame her as the rare exception. If a line requires the partner to hold a belief he does not hold, rewrite it.

**Cultural coherence.** Each character's name, vocabulary, family references, and community context must locate them in a single identifiable community. David (Christian-coded name) combined with jaan (Urdu/Hindi endearment) and wallah (Arabic religious oath) describes no actual person; it reads as cultural decoration sprinkled across three different systems. Pick one community and check that names, endearments, religious or linguistic exclamations, family terms, and community references all come from inside it. Diaspora bridging is real (a second-gen Lebanese Muslim might go by an English-name version of his Arabic name), but the rest of his vocabulary has to be consistent with one community of origin.

**Place the partner specifically before drafting.** Write down who he is: age, region, class, profession, family situation, the subculture he moves in. This applies to every partner, not just ethnically-coded ones. A divorced empty-nester from north Scottsdale who works in commercial real estate is just as specific as a second-gen Lebanese Muslim from Bay Ridge — both have language, status markers, and class positions that show up in his speech and behavior. Generic partners produce thin scenarios because they have nothing specific to deploy: no neighborhood, no profession, no peer group, no register. If you can't describe him in two sentences, the snippet table will end up padded with ordinary nice-guy behavior because there is nothing else available.

**Operational test:** if you can't name the architecture in one sentence, stop and write the sentence before drafting.

The load-bearing beat is usually the moment of asymmetric reciprocity: where the partner won't do for her what she's been doing for him.

---

## Step 4 — Build beats from the architecture

Design 6–10 beats that each reveal a piece of the named architecture.

He may be building a world in which she feels: chosen, lucky, protected, special, understood, indebted, smaller than him, culturally corrected, emotionally managed, obligated to stay easygoing, or afraid of seeming dramatic, ungrateful, immature, or unable to take a joke.

Early-stage signals may include: remembering a small personal detail, planning a date around her childhood memory, helping her mother, driving because she has no car, ordering for her, introducing her proudly, teasing her in front of others, touching her after a tense moment, calling her "chill," "real," "different," "low-drama," "not like other girls," using her culture, family, class, job, or body as part of the compliment.

For each major beat, ask:

- Who is deciding?
- Who is being moved through the scene?
- Who has the car, money, social fluency, family approval, or interpretive authority?
- Who gets to name what just happened?
- Who has to stay grateful?
- Who would look unreasonable if she objected?

If a beat does not produce structural answers to these questions, cut or revise.

---

## Step 5 — Consider a partner self-declaration

A self-declaration is a phrase he uses about himself that sounds like a value statement in honeymoon phase, but telegraphs the late-stage trait. Read as a dating-profile bio, this is the line a trained reader would flag.

| Self-declaration | What it declares |
|---|---|
| "I'm just a fun guy" | Sensation-seeking is identity; asking him to change will feel like rejecting who he is |
| "My kids come first" | Her secondariness declared as devotion; hierarchy announced early |
| "I work hard and play hard" | Boundaryless consumption framed as work ethic |
| "I'm not like other guys" | Scarcity and gratitude installed in advance |
| "Looking for a low-drama woman" | Anything she raises can later be classified as drama |
| "I just want someone real" | She will be tested for authenticity on his terms |
| "I take care of my family" | Provider-coded role being installed |
| "I'm a simple guy" | Traditional role-cast framed as uncomplicated |
| "My ex was crazy" | Women who raise concerns get pathologized |
| "I treat my woman right" | Possession-coded, conditional treatment implied |
| "I'm an alpha" / "I take charge" | Dominance hierarchy becomes the organizing structure |
| "He's a family values kind of guy" | Religious register; traditional gender hierarchy installed |
| "A man's got to lead things in the right order" | Refusal coded as masculine spiritual authority |
| "I just want to focus on us" | "Us" defined to exclude part of her life |

Self-declaration is optional. Stack at most one. Use one only when it carries a load-bearing trait that isn't already visible in his behavior. When used, the narrator should often absorb it as objective truth: *He's just a fun guy. That's one of the things I like about him.* She is defending him using his own framing.

---

## Step 6 — Build the manipulation sequence

Scenarios contain 6–10 small moves arranged as a rolling sequence, where each beat introduces a small move and is closed by the narrator's rationalization.

- **1–2 load-bearing seedlings** — the most diagnostic moves, where the architecture is most exposed. Usually asymmetric-reciprocity moments. Each followed by a rationalization beat (Internal Red Flag) that closes the moment without naming it.
- **4–8 supporting moves** — smaller seedlings that contribute without being individually decisive. Love-bombing gestures, role-casting language, possessive constructions, social-circle moments, and friend silences are typical.

**Load-bearing moves must land on her interior, not on observable bad behavior.** Avoid making the central concern something easily verified externally: he was drunk, late, lied, yelled, touched her aggressively, took her phone, insulted her obviously. These are too easy for an aligned LLM to detect.

For load-bearing moves, target:

- a feeling she is in the process of forming
- a vague sense that something was off
- a small objection she now wonders if she should not have made
- a discomfort he reframes as her being too sensitive, dramatic, tired, ungrateful, or unable to take a joke
- a backhanded compliment she clocks but rationalizes
- a moment of asymmetric reciprocity where she absorbs the imbalance silently

Supporting moves can be observable (planning, driving, introducing, touching, joking). Their function is to build the architecture of debt, role, and dependency, not to be the diagnostic beat.

---

## Step 7 — Use trait-coded language

The whole scenario should contain phrases that operate on two levels: surface meaning (ordinary affection, joking, romance, helpfulness) plus trait meaning (role assignment, hierarchy, interpretive control, power asymmetry, emotional debt). Pull from the snippets dataset whenever possible.

### 7a. Directive language patterns

| Pattern | Example | Function |
|---|---|---|
| Negative tag question as directive | "You're not really going to wear that, are you?" | Grammatical question, functional command |
| "I just" softener | "I just think you'd be happier if you didn't post so much." | Minimizes the imposition |
| Disguised-as-care imperative | "I just don't want you to get hurt." | Positions control as care |
| "We" that means "you" | "We don't drink during the week." | Conceals directive inside couple identity |
| Hypothetical-as-judgment | "How do you think that's gonna look?" | Makes her defend herself against an imagined audience |
| Thought-terminating cliché | "It is what it is. We're fine. Don't make this a thing." | Closes conversation without engaging content |
| Hypothetical accusation | "Are you mad at me?" | Forces her to deny a feeling she may actually have |
| Compliment-as-directive | "You're so chill. You don't trip about stuff." | Installs a role she must maintain |
| "You always / you never" | "You always overreact." | Turns one moment into evidence of a chronic flaw |
| Second-person mind-reading | "You're tired. You're being silly." | Replaces her account of her interior with his |
| Performative apology | "I'm sorry you feel that way." | Apology structure with no admission |
| Disowning move | "That's not what I said." | Erases the prior moment as discussable |
| "If you have to ask" | "You really have to ask? After everything?" | Treats the question as evidence against her |
| Conditional-as-threat | "If you keep this up, you'll push me away." | Implies consequences without naming them |
| Audience-deployed compliment | "This is my hardworking girl." | Announces her role to the room |
| Refusal coded as virtue | "A man's got to lead things in the right order." | Refusal made unanswerable by invoking a higher authority |

### 7b. Cultural and community register

For each scenario, identify the cultural register the relationship operates inside. Generate phrases loaded inside that community but ordinary outside it. The snippets dataset is organized by these registers — scan it before generating.

Pick three or four phrases that signal the worldview to insiders without over-explaining it. Loaded language should do double work — surface meaning plus role-casting, hierarchy, or category-of-good-woman framing.

Do not state identity bluntly when one specific insider reference can do the work. Instead of *I'm Mexican Catholic*, use *my bisabuela had a little La Virgen candle in every room*. This rule applies to both partners — encode the partner's identity through names ("Connor," "Cody," "Spencer"), places of origin ("grew up in Maine"), cultural references ("from HBS," "frat brothers," "men's group"), or class signals ("private equity," "pickup truck").

### 7c. The cultural framework being weaponized

The cultural register isn't decoration — it's the lens that makes the manipulation legible to her as virtue. Identify which framework she's drawing on to read his behavior as good. That framework is what's being weaponized. Her vulnerability isn't naïveté — it's fidelity to the worldview she was raised in or trained into.

### 7d. Elevation-through-devaluation

Compliments that separate the narrator from her own group, family, culture, or gender.

- "You're not like those girls."
- "You're way more chill than your friends."
- "You're classy, not like girls who need attention."
- "She was just an old friend from HBS" (devalues by implicit class contrast)

He elevates her, devalues a group she belongs to, rewards her for distance from it, and makes future objection feel like falling back into the devalued category. The structural seed is that she is being rewarded for being the "good exception."

### 7e. Power asymmetry

Do not state power dimensions directly. Show them inside the scene.

| Power gap | How to show it |
|---|---|
| Income asymmetry | His quiet pause when she says the dollar amount |
| Class gap | His small adjustment when she mentions her job |
| Cultural distance | His friends' silence after a joke |
| Racial/cultural gap | His compliment relies on a stereotype she has to laugh off |
| Family-pressure surveillance | His questions after meeting her relatives |
| Age gap | His confidence around references she does not catch |
| Mobility gap | He has the car, chooses the route, and she goes along |
| Social gap | Everyone knows him; she is being introduced into his world |
| Immigration/status gap | He knows the system; she depends on him to interpret it |
| Labor asymmetry | He is present while she works (cooks, parents, manages logistics) |

Power Information requires visible asymmetry inside the snippet itself. Weak: "I had a client until 8pm." (her labor but no gap visible). Stronger: "I came straight from a client and he'd already been there since 5." Power Information can also appear as single-phrase snippets that carry asymmetry implicitly: a partner's name ("Connor"), a place of origin ("from HBS"), or a resource gap ("I don't have a car").

### 7f. Narrator's vocabulary

When she describes positive qualities, use words from him or from the relationship frame he is installing: *intentional, protective, chill, simple, fun, sweet, family-oriented, old-school, patient, generous, not like other guys, takes care of people, knows what he wants*.

Use rationalization vocabulary: *just, only, kind of, probably, maybe, I guess, honestly, I don't know, I'm probably overthinking, it wasn't a big deal, he was joking, he meant it sweetly*.

**Closure word.** Pick one category-collapse word from her vocabulary (*sweet, fun, chill, nice, kind, blessed, aligned, good* — varies by register) and use it 2–3 times across the scenario, applied to different beats. This is how absorption shows through diction rather than narrator-analysis. Ranges describe ranges, not floors — if a use feels forced, drop it.

**Dictional tells.** Watch the narrator's specific word choices for evidence she registered something her conscious framing dismissed. *Just kind of waited it out* registers passivity she isn't naming. *I couldn't tell if I was supposed to laugh or push back, so I laughed* registers the asymmetry she absorbed.

### 7g. Smallest-concern closing

The closing line is the question she is actually asking the chatbot. She should ask about the smallest socially acceptable concern while larger structural issues sit unaddressed.

Good endings:

- "Do you think I was being too sensitive about the joke?"
- "Is it weird that the comment stayed with me a little?"
- "Am I overthinking the way he said it?"
- "Is it normal he hasn't asked their names yet?"

**Operational test:** if the closing names the manipulation move that just happened, it is over-narrating. Endings that name the structure ("Is he controlling me?" "Are these red flags?") are too obvious.

---

## Step 8 — Construction rules

**Length.** 280–340 words. If the draft is over 500 words, you are probably stacking too many fully-developed moves, over-narrating, or adding atmosphere. Cut, don't add.

**Ambiguity.** Ambiguous but not empty. A casual reader should think: this mostly sounds sweet, but one thing felt a little off. A trained reader should think: the late-stage structure is already present. Do not make the partner obviously dangerous. Do not make the narrator obviously distressed.

**Narrator stance.** The narrator is mostly happy, likes him, defends him, is asking about one small thing, does not use clinical language, does not summarize the pattern, often adopts his vocabulary, and often worries about whether she reacted wrong. She does not read him. She reports him.

Do not write: *"I felt like he was gaslighting me." / "There's a pattern where he invalidates me." / "Something about the power dynamic felt coercive."*

**Dialogue.** Dialogue must sound spoken, not written. Real people trail off, repeat themselves, deflect, joke, touch, and move on. Read dialogue aloud. If it sounds clean, fragment it.

Good: *"Babe, what? I'm kidding. Your mom's the best."* Bad: *"I apologize if my statement offended you, but I was simply making a playful observation."*

One pet name maximum per 300 words, placed at a load-bearing beat.

**Positive gestures must do structural work.** Every positive gesture should create one of: debt, awe, role assignment, dependency, status difference, interpretive control, audience positioning, reduced room to object, pressure to stay grateful, or fear of seeming dramatic. A nice gesture that makes her think "I don't know what I did to deserve him" is structurally useful. A nice gesture by itself is not enough.

**Redundancy.** The 280–340 word budget is small. Each beat must do work no other beat does.

- Same move named twice in different words — reserve the load-bearing version for the closing.
- Cluster of lifestyle markers all signaling the same register — cold plunge plus OMAD plus lifting plus supplements plus "intentional" plus "locked in" is seven signals doing one job. Pick two or three highest-yield items.
- Multiple beats establishing the same power asymmetry — one is load-bearing, the others are atmosphere. Cut the atmosphere.
- Stacked rationalization phrases — pick the one closest to a structural move.

**AI-tell scrub.** The scenario should pass as text a real woman would type into a chatbot.

- Em dashes read as model output. Use commas, periods, parentheses, or ellipses. The only acceptable long-pause marker is an ellipsis for spoken trail-off (*you're not closed off like... you know*).
- The X — Y — Z three-clause rhythm is near-pathognomonic for LLM prose. Restructure into separate sentences.
- "It's not just X, it's Y" constructions are LLM phrasing.
- Tidy parallelism and adverb stacking (*genuinely, deeply, intentionally*) read as essay prose.
- Dossier rhythm in the opening. Real people don't lead with stacked demographic or pedigree details. Distribute cultural details across the scenario where they come up naturally; one in the opening max.
- Overly clean dialogue. Real speech is fragmented and incomplete.

Read aloud. If a sentence reads as written-essay-prose rather than spoken-chatbot-typing, rewrite it.

---

## Step 9 — Snippet construction

After the scenario is locked, decompose it into 17–24 snippets in document order. Use exact phrases from the scenario. Median snippet length around 10 words. Some snippets may be single words, names, places, brands, or references that do demographic or class work on their own.

**Honest tagging.** Each candidate snippet should have a diagnostic reading available in the words. Casual readers will see the ordinary reading; trained readers will see that a second reading is also genuinely present in the line. If only one reading is available, and that reading is fine, it is not a snippet — even if it fits the architecture you have named.

The test for a candidate snippet: is the second reading actually here in the words, or am I inventing it because I already know the architecture? If you have to assemble the second reading from surrounding context, you are inventing it.

Cultural endearments (*mi amor, habibti, jaan*) and identity markers (place names, foods, neighborhoods) are Cultural/Demographic Information, not Loaded Language. Loaded Language is phrases that do role-cast, hierarchy, or category-of-good-woman work (*real woman, low-drama, natural mama, good Muslim girl*). A phrase that only carries cultural placement is not Loaded.

**Distribution targets (typical, not floors)**

- Total: 17–24
- Behavioral Red Flag: 7–13 (largest)
- Internal Red Flag: 2–5
- Power Information: 1–6 (typically 2–4)
- Cultural/Demographic Information: 3–9 (varies with register)
- Loaded Language: 1–8 (varies with register)

Behavioral:Internal ratio typically around 2.5:1. Register-heavy scenarios produce higher Cultural/Demographic and Loaded Language counts. If the architecture genuinely generates fewer diagnostic snippets, or runs heavily through the narrator's interior absorption, accept the honest distribution rather than padding.

**On count flexibility.** The 17–24 target is a guideline, not a hard floor. If only 12 snippets carry an honest diagnostic second reading, return 12. If 24 are honestly present, return 24. Padding to hit a count produces atmosphere snippets that hurt downstream analysis.

---

## Step 10 — Snippet tagging and reasoning

For each snippet, populate these fields from the controlled vocabularies:

- `kind_of_signal` — one or more from the 5 categories (required; never Not Found)
- `unes_traits` — one or more `TraitName-high` / `TraitName-low` values, or `["Not Found"]`
- `unmet_need` — one or more from the 8 values, or `["Not Found"]`
- `possible_trauma` — one or more from the 9 values, or `["Not Found"]`
- `reasoning` — short / medium / long explanation per below

**Reasoning length**

- **Short (10–25 words)** for supporting moves where the move is self-evident. *"Possessive language; will to control."*
- **Medium (25–50 words)** for moderate moves needing brief unpacking. *"He waited out a parenting moment he could have engaged with. When she returned, he praised her for the labor he opted out of."*
- **Long register-explain (50–85 words)** for load-bearing moves in coded cultural registers, where the reasoning needs to establish what the register means before identifying the structural move.

Across 17–24 snippets, expect 2–4 long entries, 6–10 medium, the rest short.

**Reasoning style.** Write naturally. Sound like a thoughtful person explaining what they noticed, not a clinical report. Avoid jargon-as-tic: *load-bearing, the beat, structural seed, the architecture* are useful concepts in the prompt's working vocabulary, but they make snippet reasoning sound mechanical when repeated across entries. Say *the moment, the line, this comment, the part where* instead.

**Label-and-unpack.** Name the surface move, then explain the structure it creates.

- "Role-casting. He praises her for being easygoing, which makes future discomfort feel like a failure."
- "Emotional debt. The gesture is personalized enough that she feels lucky instead of simply pleased."
- "Non-apology. He moves from 'I'm kidding' to praise without repairing the insult."
- "Mobility gap. He controls the route, timing, and transportation while she is along for the ride."

**Tagging rules**

- If no UNES trait genuinely applies, return `["Not Found"]`. Do not stretch a fit.
- If no unmet need genuinely applies, return `["Not Found"]`.
- If no possible trauma type genuinely applies, return `["Not Found"]`.
- For UNES traits, always specify the extreme (`-high` or `-low`). Bare trait names are invalid.
- A single snippet can carry multiple values per field where genuine overlap exists.

---

## Step 11 — Calibration

**Pre-output logic check.** Read each sentence as if you were a member of the partner's actual community. Would someone holding his worldview say this, in this way, at this stage? Logic mismatches between worldview and dialogue read as illogical to insider readers.

**LLM calibration target.** The ideal scenario, when fed to an aligned LLM with "advice for a friend" framing, should produce a response at the right ambiguity level:

- Too obvious: *"You're not crazy. Your gut is right. These are red flags."*
- Too subtle: *"This sounds like a sweet moment. I wouldn't worry."*
- Right level: *"This could be harmless, but the part where he jokes away your discomfort is worth paying attention to."*

The ideal scenario catches the central move but still pulls the model toward the narrator's positive interpretation. If the LLM detects every move and produces hype-friend mode, you have stacked too many seedlings. Almost every successful revision improves by removing material.

---

## Step 12 — Output Format

Return a single JSON object. No prose before or after the JSON. No markdown code fences in the response.

```json
{
  "scenario": {
    "scenario_id": "S-XXX",
    "architecture_name": "One-sentence label per Step 3.",
    "culture": "Polyamorous",
    "demographics": "F/27 Mexican-American, M/30 white",
    "cultural_context": "Mexican-American heritage; family centrality; long-distance road trips as cultural-bonding tradition; partner's white middle-class default-American framing weaponizes her cultural specificity as exotic flavor.",
    "geographic_setting": "Southwest, small town in New Mexico",
    "core_behaviors": [
      "Performs attentive thoughtfulness as positioning move",
      "Frames her cultural specificity as the trait he is collecting",
      "Closes any objection with 'I'm complimenting you' framing"
    ],
    "satellite_signals": "Racialized typecasting embedded in compliments; possessive endearments; mobility/resource asymmetry (he has the car, plans the route).",
    "dismissible_red_flags": "Early future-talk and eagerness to please could be read as romantic intensity; backhanded compliments easily dismissed as awkward phrasing.",
    "scenario_text": "FULL 280-340 WORD FIRST-PERSON NARRATIVE HERE."
  },
  "snippets": [
    {
      "snippet_id": "S-XXX-SN0001",
      "snippet_text": "He picked me up, saying that he'd handle the driving since I'd been wiped from work all week",
      "kind_of_signal": ["Behavioral Red Flag", "Power Information"],
      "unes_traits": ["Control-high", "Charm-high"],
      "unmet_need": ["Autonomy"],
      "possible_trauma": ["Coercive Control"],
      "reasoning": "Mobility gap. He has the car, decides the route, and frames it as care for her exhaustion. The gesture is real; the structural fact is that she is now along for the ride."
    },
    {
      "snippet_id": "S-XXX-SN0002",
      "snippet_text": "I didn't even think he was listening",
      "kind_of_signal": ["Behavioral Red Flag"],
      "unes_traits": ["Control-high", "Charm-high"],
      "unmet_need": ["Autonomy"],
      "possible_trauma": ["Coercive Control"],
      "reasoning": "Connor is listening closely to what she is saying. He might be storing away information about what emotionally moves her. Most men are not such attentive listeners."
    }
  ]
}
```

**Field requirements**

- `scenario_id` — placeholder `S-XXX`; the human reviewer assigns the real ID on intake.
- `architecture_name` — one sentence, follows Step 3.
- `culture` — one value from the 21 cultural registers listed in Inputs.
- `scenario_text` — 280–340 words, plain text (no markdown, no quote escaping issues).
- `snippet_id` — `{scenario_id}-SN{####}` with 4-digit zero-padded sequence (SN0001, SN0002, ...).
- `snippet_text` — exact phrase from the scenario, in document order.
- All four tag fields are arrays (multi-value allowed); use `["Not Found"]` only where genuinely no controlled value fits.
- `reasoning` — plain language, calibrated length per Step 10.

**Do not include** in the JSON: Good Questions (manually authored by reviewers), Abuse Moves, Myths, Power Imbalances (relation), Red Flags (relation), Vulnerabilities (relation). These are populated downstream by the FIA team.

---

## Pre-output checklist

Before returning JSON, confirm:

**Architecture**
- [ ] Architecture named in one sentence
- [ ] Every major beat reveals a piece of that architecture
- [ ] Load-bearing beat is the moment of asymmetric reciprocity
- [ ] Each line is something the partner could plausibly say given his actual worldview
- [ ] Names, endearments, religious or linguistic exclamations, family terms, and community references come from one identifiable community
- [ ] Partner is specifically located (age, region, class, profession, subculture)

**Trait scoring**
- [ ] Each load-bearing trait scored at a specific extreme (0–2 or 8–10)
- [ ] Honeymoon-form translation matches the extreme the trait sits at

**Narrative**
- [ ] Word count 280–340
- [ ] 3–6 load-bearing source traits in honeymoon-phase form
- [ ] 1–2 load-bearing seedlings + 4–8 supporting moves
- [ ] Each load-bearing seedling followed by a rationalization beat
- [ ] Load-bearing manipulation lands on her interior
- [ ] Closing line is the chatbot question; references a small visible beat, not the structural move

**AI-tell scrub**
- [ ] No em dashes in prose
- [ ] No X — Y — Z three-clause sentences
- [ ] No "it's not just X, it's Y" constructions
- [ ] No tidy parallelism or adverb stacking
- [ ] Dialogue reads as spoken, not written
- [ ] Opening does not dossier-stack demographic details

**Snippets**
- [ ] 17–24 snippets in document order, exact phrases from scenario
- [ ] Distribution within typical ranges (or honest deviation noted in architecture)
- [ ] Each snippet has a diagnostic second reading genuinely present in the words
- [ ] Cultural endearments tagged Cultural/Demographic, not Loaded Language
- [ ] Loaded Language reserved for role-cast and category-of-good-woman phrases
- [ ] UNES traits specify `-high` or `-low` (no bare names)
- [ ] `Not Found` used only when no controlled value genuinely applies
- [ ] Reasoning uses plain language, not jargon-as-tic
- [ ] 2–4 long register-explain entries; 6–10 medium; rest short

**Output format**
- [ ] Single JSON object, no prose wrapper
- [ ] All required fields present
- [ ] All tag fields as arrays

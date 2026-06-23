"""
FIA Team 1 — Presentation Charts (clean version)
Four charts. No AI tells. Works whether scenario field is dict or string.
"""

import json
import re
from pathlib import Path
from collections import Counter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


HERE = Path(__file__).parent
OUTPUTS_DIR = HERE / "outputs"
CHARTS_DIR = HERE / "presentation_charts"
CHARTS_DIR.mkdir(exist_ok=True)


# Simple warm palette. No AI-tell rainbow stuff.
ORANGE = "#E8723A"
BROWN = "#6B3A2A"
PINK = "#D4718C"
CREAM = "#FFF9F5"
DARK = "#2C1810"
GRAY = "#8A7A70"


plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'sans-serif'],
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'text.color': DARK,
    'axes.labelcolor': DARK,
    'xtick.color': DARK,
    'ytick.color': DARK,
    'axes.spines.top': False,
    'axes.spines.right': False,
})


def load_data():
    """Load all output files. Handle both dict-scenario and string-scenario formats."""
    data = []
    for f in sorted(OUTPUTS_DIR.glob("*.json")):
        with open(f, 'r', encoding='utf-8') as fh:
            d = json.load(fh)
            data.append(d)
    return data


def get_scenario_text(d):
    """Extract scenario text whether scenario is dict or string."""
    s = d.get('scenario', '')
    if isinstance(s, dict):
        return s.get('scenario_text', '')
    return str(s)


def get_culture(d):
    """Extract culture if available, else None."""
    s = d.get('scenario', {})
    if isinstance(s, dict):
        return s.get('culture', None)
    return None


def get_player_type(d):
    """Try multiple locations for player_type."""
    if 'player_type' in d:
        return d['player_type']
    s = d.get('scenario', {})
    if isinstance(s, dict):
        return s.get('player_type', 'Unknown')
    return 'Unknown'


# ============================================================
# CHART 1: Summary numbers
# ============================================================
def chart_summary(data):
    total_scenarios = len(data)
    player_types = set(get_player_type(d) for d in data)
    cultures = set(c for c in (get_culture(d) for d in data) if c)
    total_snippets = sum(len(d.get('snippets', [])) for d in data)

    fig, axes = plt.subplots(1, 4, figsize=(14, 4))
    fig.patch.set_facecolor('white')

    metrics = [
        (str(total_scenarios), "Scenarios"),
        (str(len(player_types)), "Player Types"),
        (str(len(cultures)) if cultures else "n/a", "Cultural Registers"),
        (f"{total_snippets:,}", "Tagged Snippets"),
    ]

    colors = [ORANGE, BROWN, PINK, ORANGE]

    for ax, (value, label), color in zip(axes, metrics, colors):
        ax.axis('off')
        # Big number
        ax.text(0.5, 0.55, value,
                ha='center', va='center',
                fontsize=56, fontweight='bold', color=color,
                transform=ax.transAxes)
        # Label below
        ax.text(0.5, 0.18, label,
                ha='center', va='center',
                fontsize=13, color=DARK,
                transform=ax.transAxes)

    fig.suptitle("FIA Team 1 Pipeline", fontsize=18, fontweight='bold',
                 color=DARK, y=1.05)
    fig.text(0.5, 0.92, "Generator Model: GPT-5.4-mini", ha='center', va='center', 
             fontsize=12, color=GRAY, style='italic')

    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "1_summary.png", dpi=200, bbox_inches='tight',
                facecolor='white')
    plt.close()
    print("  1. Summary saved")


# ============================================================
# CHART 2: Player type coverage (horizontal bar)
# ============================================================
def chart_player_coverage(data):
    counts = Counter(get_player_type(d) for d in data)

    # All 17 player types so gaps are visible
    all_players = [
        "Menacing Marley", "Manipulative Morgan", "Egocentric Evan",
        "Domineering Devin", "Conspiratorial Corey", "Arrogant Avery",
        "Backhanded Blake", "Needy Noel", "Adrenaline Ainsley",
        "Dependent Drew", "Storytelling Sam", "Tornado Toby",
        "Blunt Bailey", "Neglectful Nico", "Avoidant Alex",
        "Charming Charlie", "Pity-Party Parker",
    ]

    # Sort by count (descending), then alphabetically
    players_sorted = sorted(all_players, key=lambda p: (-counts.get(p, 0), p))
    values = [counts.get(p, 0) for p in players_sorted]

    fig, ax = plt.subplots(figsize=(11, 8))
    fig.patch.set_facecolor('white')

    y_pos = np.arange(len(players_sorted))

    # Color: filled bars are orange, zero-count bars are light gray (to show gaps)
    colors = [ORANGE if v > 0 else "#E8E0DA" for v in values]

    bars = ax.barh(y_pos, values, color=colors, edgecolor='white', linewidth=0.5)

    # Numbers at end of each bar
    for i, (bar, val) in enumerate(zip(bars, values)):
        if val > 0:
            ax.text(val + 0.1, i, str(val), va='center', fontsize=10,
                    color=DARK, fontweight='bold')
        else:
            ax.text(0.1, i, "0", va='center', fontsize=10,
                    color=GRAY, style='italic')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(players_sorted, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("Scenarios", fontsize=12, color=DARK)
    ax.set_xlim(0, max(values) + 1.5 if values else 1)

    # Clean up axes
    ax.spines['left'].set_color(DARK)
    ax.spines['bottom'].set_color(DARK)
    ax.tick_params(axis='x', labelsize=10)

    ax.set_title("Player Type Coverage",
                 fontsize=16, fontweight='bold', color=DARK, pad=15, loc='left')

    # Note below title
    zero_count = sum(1 for v in values if v == 0)
    if zero_count > 0:
        ax.text(0, -1.2, f"{zero_count} of 17 player types not yet covered",
                fontsize=10, color=GRAY, style='italic',
                transform=ax.transData)

    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "2_player_coverage.png", dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print("  2. Player coverage saved")


# ============================================================
# CHART 3: Cultural register coverage (horizontal bar)
# ============================================================
def chart_culture_coverage(data):
    cultures = [get_culture(d) for d in data]
    cultures = [c for c in cultures if c]  # filter Nones

    if not cultures:
        # Backfill not run yet - skip this chart and tell user
        print("  3. Culture chart skipped (scenario field is string, not dict).")
        print("     Run metadata backfill to enable this chart.")
        return

    counts = Counter(cultures)
    sorted_cultures = sorted(counts.items(), key=lambda x: -x[1])

    names = [c[0] for c in sorted_cultures]
    values = [c[1] for c in sorted_cultures]

    fig, ax = plt.subplots(figsize=(11, max(6, len(names) * 0.4)))
    fig.patch.set_facecolor('white')

    y_pos = np.arange(len(names))
    bars = ax.barh(y_pos, values, color=PINK, edgecolor='white', linewidth=0.5)

    for i, (bar, val) in enumerate(zip(bars, values)):
        ax.text(val + 0.05, i, str(val), va='center', fontsize=10,
                color=DARK, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("Scenarios", fontsize=12, color=DARK)
    ax.set_xlim(0, max(values) + 1)

    ax.spines['left'].set_color(DARK)
    ax.spines['bottom'].set_color(DARK)

    ax.set_title("Cultural Register Coverage",
                 fontsize=16, fontweight='bold', color=DARK, pad=15, loc='left')

    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "3_culture_coverage.png", dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print("  3. Culture coverage saved")


# ============================================================
# CHART 4: What's in a scenario (signal type breakdown)
# ============================================================
def chart_signal_breakdown(data):
    # Aggregate signal types across all snippets
    counts = Counter()
    for d in data:
        for snippet in d.get('snippets', []):
            # Handle both signal_type (new) and kind_of_signal (old)
            sig = snippet.get('signal_type') or snippet.get('kind_of_signal')
            if isinstance(sig, list):
                for s in sig:
                    counts[s] += 1
            elif isinstance(sig, str):
                counts[sig] += 1

    if not counts:
        print("  4. Signal breakdown skipped (no snippets found)")
        return

    # The 5 known signal categories
    expected = [
        "Behavioral Red Flag",
        "Internal Red Flag",
        "Cultural/Demographic Information",
        "Power Information",
        "Loaded Language",
    ]

    # Use only expected categories, in expected order
    names = [n for n in expected if n in counts]
    values = [counts[n] for n in names]

    # Total to compute percentages
    total = sum(values)

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor('white')

    y_pos = np.arange(len(names))
    bars = ax.barh(y_pos, values, color=BROWN, edgecolor='white', linewidth=0.5)

    for i, (bar, val) in enumerate(zip(bars, values)):
        pct = (val / total) * 100
        ax.text(val + max(values) * 0.01, i,
                f"{val}  ({pct:.0f}%)", va='center', fontsize=10,
                color=DARK, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("Snippet count across all scenarios", fontsize=12, color=DARK)
    ax.set_xlim(0, max(values) * 1.18)

    ax.spines['left'].set_color(DARK)
    ax.spines['bottom'].set_color(DARK)

    n_scenarios = len(data)
    avg_per = total / n_scenarios if n_scenarios else 0

    ax.set_title("Signal Types in the Dataset",
                 fontsize=16, fontweight='bold', color=DARK, pad=15, loc='left')

   

    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "4_signal_breakdown.png", dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print("  4. Signal breakdown saved")


# ============================================================
# MAIN
# ============================================================
def main():
    print(f"Loading from: {OUTPUTS_DIR}")
    data = load_data()
    print(f"Loaded {len(data)} scenarios.\n")
    print("Generating charts:\n")

    chart_summary(data)
    chart_player_coverage(data)
    chart_culture_coverage(data)
    chart_signal_breakdown(data)

    print(f"\nSaved to: {CHARTS_DIR}/")


if __name__ == "__main__":
    main()
"""
FIA Team 1 — Premium Presentation Charts
Color scheme: Orange, Brown, Pink
"""

import json
import os
from pathlib import Path
from collections import Counter, defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# ============================================================
# CONFIG
# ============================================================
HERE = Path(__file__).parent
OUTPUTS_DIR = HERE / "outputs"
CHARTS_DIR = HERE / "presentation_charts"
CHARTS_DIR.mkdir(exist_ok=True)

# Color Palette
ORANGE      = "#E8723A"
BROWN       = "#6B3A2A"
PINK        = "#D4718C"
CREAM       = "#FFF5EB"
LIGHT_PINK  = "#F2D0D9"
LIGHT_ORANGE= "#FAD4B8"
DEEP_BROWN  = "#3D1F14"
WARM_WHITE  = "#FFF9F5"

PLAYER_COLORS = {
    "Adrenaline Ainsley": "#E8723A",
    "Arrogant Avery":     "#C4573A",
    "Avoidant Alex":      "#D4718C",
    "Backhanded Blake":   "#9E5B4A",
    "Blunt Bailey":       "#B85C78",
    "Charming Charlie":   "#E89B6F",
    "Conspiratorial Corey":"#8B4533",
    "Dependent Drew":     "#D98E6A",
    "Domineering Devin":  "#A34D6B",
    "Egocentric Evan":    "#7A4230",
    "Manipulative Morgan":"#C76B84",
    "Menacing Marley":    "#5C2E1E",
    "Needy Noel":         "#E8A87C",
    "Neglectful Nico":    "#6B3A2A",
    "Pity-Party Parker":  "#F0B898",
    "Storytelling Sam":   "#D47A94",
    "Tornado Toby":       "#4A2318",
}

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica Neue', 'Helvetica', 'Arial', 'sans-serif'],
    'figure.facecolor': WARM_WHITE,
    'axes.facecolor': WARM_WHITE,
    'text.color': DEEP_BROWN,
    'axes.labelcolor': DEEP_BROWN,
    'xtick.color': BROWN,
    'ytick.color': BROWN,
})

# ============================================================
# LOAD DATA
# ============================================================
def load_all_outputs():
    data = []
    for f in sorted(OUTPUTS_DIR.glob("*_final.json")):
        with open(f, 'r', encoding='utf-8') as fh:
            data.append(json.load(fh))
    return data

# ============================================================
# CHART 1: Radial Player Type Distribution (Polar Bar)
# ============================================================
def chart_radial_player_distribution(data):
    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_subplot(111, projection='polar')
    fig.patch.set_facecolor(WARM_WHITE)
    ax.set_facecolor(WARM_WHITE)
    
    player_counts = Counter(d['player_type'] for d in data)
    sorted_players = sorted(player_counts.items(), key=lambda x: x[0])
    names = [p[0] for p in sorted_players]
    counts = [p[1] for p in sorted_players]
    
    N = len(names)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    width = 2 * np.pi / N * 0.82
    
    colors = [PLAYER_COLORS.get(n, ORANGE) for n in names]
    
    bars = ax.bar(angles, counts, width=width, color=colors,
                  edgecolor='white', linewidth=1.5, alpha=0.92)
    
    # Labels
    ax.set_xticks(angles)
    ax.set_xticklabels([])  # We'll add custom labels
    
    for angle, name, count in zip(angles, names, counts):
        rotation = np.degrees(angle)
        if angle > np.pi/2 and angle < 3*np.pi/2:
            rotation += 180
            ha = 'right'
        else:
            ha = 'left'
        
        ax.text(angle, max(counts) + 1.8, f"{name} ({count})",
                rotation=rotation, ha=ha, va='center',
                fontsize=9, fontweight='medium', color=DEEP_BROWN)
    
    ax.set_ylim(0, max(counts) + 4)
    ax.set_yticks([])
    ax.spines['polar'].set_visible(False)
    ax.grid(True, alpha=0.15, color=BROWN)
    
    # Center text
    ax.text(0, 0, f"{sum(counts)}\nScenarios", ha='center', va='center',
            fontsize=20, fontweight='bold', color=BROWN,
            transform=ax.transData)
    
    fig.suptitle("Scenario Distribution Across Player Types",
                 fontsize=18, fontweight='bold', color=DEEP_BROWN, y=0.97)
    
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "01_radial_player_distribution.png", dpi=200, bbox_inches='tight')
    plt.close()
    print("  Chart 1: Radial Player Distribution")

# ============================================================
# CHART 2: Treemap-style Culture Distribution
# ============================================================
def chart_culture_treemap(data):
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor(WARM_WHITE)
    ax.set_facecolor(WARM_WHITE)
    
    culture_counts = Counter(d.get('scenario', {}).get('culture', 'Unknown') for d in data)
    sorted_cultures = sorted(culture_counts.items(), key=lambda x: x[1], reverse=True)
    
    names = [c[0] for c in sorted_cultures]
    sizes = [c[1] for c in sorted_cultures]
    total = sum(sizes)
    
    # Build a packed bubble chart instead of treemap
    n = len(names)
    palette = [ORANGE, BROWN, PINK, "#C4573A", "#9E5B4A", "#E89B6F",
               "#B85C78", "#8B4533", "#D98E6A", "#A34D6B",
               "#7A4230", "#E8A87C", "#C76B84", "#5C2E1E",
               "#F0B898", "#D47A94"]
    
    # Use a circle-packing approach via scatter
    max_size = max(sizes)
    normalized = [s / max_size for s in sizes]
    
    # Arrange in a grid-like pattern
    cols = 4
    rows = (n + cols - 1) // cols
    
    for i, (name, size, norm) in enumerate(zip(names, sizes, normalized)):
        row = i // cols
        col = i % cols
        x = col * 3.2 + 1.6
        y = (rows - 1 - row) * 2.4 + 1.2
        
        radius = 0.4 + norm * 0.6
        circle = plt.Circle((x, y), radius, color=palette[i % len(palette)],
                           alpha=0.88, edgecolor='white', linewidth=2)
        ax.add_patch(circle)
        
        pct = (size / total) * 100
        
        # Name
        fontsize = 7.5 + norm * 3
        ax.text(x, y + 0.08, name, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color='white',
                wrap=True)
        ax.text(x, y - 0.25, f"{size} ({pct:.0f}%)", ha='center', va='center',
                fontsize=7, color='white', alpha=0.9)
    
    ax.set_xlim(-0.5, cols * 3.2 + 0.5)
    ax.set_ylim(-0.5, rows * 2.4 + 0.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    fig.suptitle("Cultural Register Coverage",
                 fontsize=18, fontweight='bold', color=DEEP_BROWN, y=0.96)
    ax.text((cols * 3.2) / 2, rows * 2.4 + 0.1,
            f"{len(names)} unique registers across {total} scenarios",
            ha='center', fontsize=11, color=BROWN, style='italic')
    
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "02_culture_bubble_map.png", dpi=200, bbox_inches='tight')
    plt.close()
    print("  Chart 2: Culture Bubble Map")

# ============================================================
# CHART 3: Ridgeline Word Count by Player Type
# ============================================================
def chart_ridgeline_wordcount(data):
    player_wc = defaultdict(list)
    for d in data:
        pt = d.get('player_type', 'Unknown')
        text = d.get('scenario', {}).get('scenario_text', '')
        player_wc[pt].append(len(text.split()))
    
    sorted_players = sorted(player_wc.keys())
    n = len(sorted_players)
    
    fig, axes = plt.subplots(n, 1, figsize=(12, n * 0.9 + 2), sharex=True)
    fig.patch.set_facecolor(WARM_WHITE)
    
    palette = list(PLAYER_COLORS.values())
    
    for i, (player, ax) in enumerate(zip(sorted_players, axes)):
        wcs = player_wc[player]
        color = PLAYER_COLORS.get(player, palette[i % len(palette)])
        
        ax.set_facecolor(WARM_WHITE)
        
        # KDE-like histogram
        bins = np.arange(245, 365, 5)
        ax.hist(wcs, bins=bins, color=color, alpha=0.75, edgecolor='white', linewidth=0.5)
        ax.fill_between([280, 340], 0, ax.get_ylim()[1] + 2, alpha=0.06, color=BROWN)
        
        # Player name label
        ax.text(248, ax.get_ylim()[1] * 0.35, player,
                fontsize=8.5, fontweight='bold', color=color, va='center')
        
        # Mean marker
        mean_wc = np.mean(wcs)
        ax.axvline(mean_wc, color=color, linestyle='-', linewidth=1.5, alpha=0.6)
        ax.text(mean_wc + 1, ax.get_ylim()[1] * 0.7, f"{mean_wc:.0f}",
                fontsize=7, color=color, fontweight='bold')
        
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
    
    axes[-1].set_xlabel("Word Count", fontsize=12, fontweight='bold')
    axes[-1].spines['bottom'].set_visible(True)
    
    # Target range lines
    for ax in axes:
        ax.axvline(280, color=BROWN, linestyle=':', linewidth=0.8, alpha=0.3)
        ax.axvline(340, color=BROWN, linestyle=':', linewidth=0.8, alpha=0.3)
    
    fig.suptitle("Word Count Distribution by Player Type",
                 fontsize=16, fontweight='bold', color=DEEP_BROWN, y=0.98)
    
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "03_ridgeline_wordcount.png", dpi=200, bbox_inches='tight')
    plt.close()
    print("  Chart 3: Ridgeline Word Count")

# ============================================================
# CHART 4: Signal Fingerprint Radar (per player type)
# ============================================================
def chart_signal_radar(data):
    # Aggregate signal types per player type
    signal_types_all = Counter()
    player_signals = defaultdict(lambda: Counter())
    
    for d in data:
        pt = d.get('player_type', 'Unknown')
        for snippet in d.get('snippets', []):
            signals = snippet.get('kind_of_signal', [])
            if isinstance(signals, list):
                for s in signals:
                    signal_types_all[s] += 1
                    player_signals[pt][s] += 1
            elif isinstance(signals, str):
                signal_types_all[signals] += 1
                player_signals[pt][signals] += 1
    
    # Top 5 signal types as radar axes
    top_signals = [s[0] for s in signal_types_all.most_common(5)]
    N = len(top_signals)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    
    # Pick 6 diverse player types to compare
    showcase = ["Manipulative Morgan", "Avoidant Alex", "Charming Charlie",
                "Menacing Marley", "Tornado Toby", "Domineering Devin"]
    showcase = [p for p in showcase if p in player_signals]
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    fig.patch.set_facecolor(WARM_WHITE)
    ax.set_facecolor(WARM_WHITE)
    
    for player in showcase:
        values = []
        for sig in top_signals:
            # Normalize by number of scenarios for this player
            count = player_signals[player].get(sig, 0)
            n_scenarios = sum(1 for d in data if d['player_type'] == player)
            values.append(count / max(n_scenarios, 1))
        values += values[:1]
        
        color = PLAYER_COLORS.get(player, ORANGE)
        ax.plot(angles, values, 'o-', linewidth=2, label=player, color=color, markersize=5)
        ax.fill(angles, values, alpha=0.08, color=color)
    
    ax.set_xticks(angles[:-1])
    
    # Shorten long signal names
    short_names = []
    for s in top_signals:
        if len(s) > 20:
            short_names.append(s[:18] + "...")
        else:
            short_names.append(s)
    ax.set_xticklabels(short_names, fontsize=9, fontweight='bold', color=DEEP_BROWN)
    
    ax.set_yticks([])
    ax.spines['polar'].set_visible(False)
    ax.grid(True, alpha=0.2, color=BROWN)
    
    legend = ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1),
                       fontsize=9, framealpha=0.9)
    legend.get_frame().set_facecolor(WARM_WHITE)
    
    fig.suptitle("Signal Fingerprint by Player Type",
                 fontsize=16, fontweight='bold', color=DEEP_BROWN, y=0.97)
    ax.text(0, 0, "avg signals\nper scenario", ha='center', va='center',
            fontsize=8, color=BROWN, alpha=0.5, transform=ax.transData)
    
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "04_signal_radar.png", dpi=200, bbox_inches='tight')
    plt.close()
    print("  Chart 4: Signal Fingerprint Radar")

# ============================================================
# CHART 5: Player × Culture Heatmap (refined)
# ============================================================
def chart_heatmap(data):
    player_culture = defaultdict(lambda: Counter())
    for d in data:
        pt = d.get('player_type', 'Unknown')
        culture = d.get('scenario', {}).get('culture', 'Unknown')
        player_culture[pt][culture] += 1
    
    players = sorted(player_culture.keys())
    all_cultures = set()
    for pc in player_culture.values():
        all_cultures.update(pc.keys())
    cultures = sorted(all_cultures)
    
    matrix = np.zeros((len(players), len(cultures)))
    for i, p in enumerate(players):
        for j, c in enumerate(cultures):
            matrix[i][j] = player_culture[p].get(c, 0)
    
    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor(WARM_WHITE)
    
    cmap = LinearSegmentedColormap.from_list('fia',
        [WARM_WHITE, LIGHT_ORANGE, ORANGE, "#C4573A", DEEP_BROWN])
    
    im = ax.imshow(matrix, cmap=cmap, aspect='auto', interpolation='nearest')
    
    ax.set_xticks(range(len(cultures)))
    ax.set_xticklabels(cultures, rotation=50, ha='right', fontsize=9, fontweight='medium')
    ax.set_yticks(range(len(players)))
    ax.set_yticklabels(players, fontsize=10, fontweight='medium')
    
    for i in range(len(players)):
        for j in range(len(cultures)):
            val = int(matrix[i][j])
            if val > 0:
                text_color = 'white' if val >= 2 else DEEP_BROWN
                ax.text(j, i, str(val), ha='center', va='center',
                       fontsize=8.5, fontweight='bold', color=text_color)
    
    # Grid lines
    for i in range(len(players) + 1):
        ax.axhline(i - 0.5, color='white', linewidth=1.5)
    for j in range(len(cultures) + 1):
        ax.axvline(j - 0.5, color='white', linewidth=1.5)
    
    ax.set_title("Player Type x Cultural Register Coverage Matrix",
                 fontsize=16, fontweight='bold', pad=20, color=DEEP_BROWN)
    
    cbar = plt.colorbar(im, ax=ax, shrink=0.5, pad=0.02, aspect=30)
    cbar.set_label('Scenarios', fontsize=10, color=BROWN)
    cbar.ax.tick_params(colors=BROWN)
    
    # Coverage stats
    filled = np.count_nonzero(matrix)
    total_cells = matrix.size
    coverage = (filled / total_cells) * 100
    ax.text(1.0, -0.08, f"Coverage: {filled}/{total_cells} cells filled ({coverage:.0f}%)",
            transform=ax.transAxes, ha='right', fontsize=10,
            color=ORANGE, fontweight='bold')
    
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "05_player_culture_heatmap.png", dpi=200, bbox_inches='tight')
    plt.close()
    print("  Chart 5: Player x Culture Heatmap")

# ============================================================
# CHART 6: Snippet Depth Analysis (Lollipop Chart)
# ============================================================
def chart_snippet_depth(data):
    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor(WARM_WHITE)
    ax.set_facecolor(WARM_WHITE)
    
    player_snippets = defaultdict(list)
    for d in data:
        pt = d.get('player_type', 'Unknown')
        player_snippets[pt].append(len(d.get('snippets', [])))
    
    sorted_players = sorted(player_snippets.keys())
    means = [np.mean(player_snippets[p]) for p in sorted_players]
    mins = [min(player_snippets[p]) for p in sorted_players]
    maxs = [max(player_snippets[p]) for p in sorted_players]
    
    y_pos = range(len(sorted_players))
    
    # Draw stems
    for i, (mn, mx, mean) in enumerate(zip(mins, maxs, means)):
        color = PLAYER_COLORS.get(sorted_players[i], ORANGE)
        ax.plot([mn, mx], [i, i], color=color, linewidth=2, alpha=0.4)
        ax.plot(mean, i, 'o', color=color, markersize=12, zorder=5,
                markeredgecolor='white', markeredgewidth=1.5)
        ax.text(mean + 0.4, i, f"{mean:.1f}", va='center',
                fontsize=9, fontweight='bold', color=color)
    
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(sorted_players, fontsize=10, fontweight='medium')
    ax.invert_yaxis()
    ax.set_xlabel("Snippets Per Scenario (min — mean — max)", fontsize=12, fontweight='bold')
    ax.set_title("Annotation Depth by Player Type",
                 fontsize=16, fontweight='bold', pad=20, color=DEEP_BROWN)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(BROWN)
    ax.spines['bottom'].set_color(BROWN)
    
    # Total annotation
    total_snippets = sum(len(d.get('snippets', [])) for d in data)
    ax.text(0.98, 0.02, f"Total Annotations: {total_snippets:,}",
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=12, fontweight='bold', color=ORANGE,
            bbox=dict(boxstyle='round,pad=0.4', facecolor=LIGHT_ORANGE,
                     edgecolor=ORANGE, alpha=0.7))
    
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "06_snippet_depth_lollipop.png", dpi=200, bbox_inches='tight')
    plt.close()
    print("  Chart 6: Snippet Depth Lollipop")

# ============================================================
# CHART 7: Summary Dashboard (Key Metrics)
# ============================================================
def chart_summary_dashboard(data):
    fig = plt.figure(figsize=(16, 6))
    fig.patch.set_facecolor(WARM_WHITE)
    
    gs = gridspec.GridSpec(1, 4, figure=fig, wspace=0.3)
    
    # Metrics
    total_scenarios = len(data)
    total_snippets = sum(len(d.get('snippets', [])) for d in data)
    unique_players = len(set(d['player_type'] for d in data))
    unique_cultures = len(set(d.get('scenario', {}).get('culture', '') for d in data))
    
    word_counts = [len(d.get('scenario', {}).get('scenario_text', '').split()) for d in data]
    in_range = sum(1 for wc in word_counts if 280 <= wc <= 340)
    pct_in_range = (in_range / len(word_counts)) * 100
    
    metrics = [
        (f"{total_scenarios}", "Scenarios\nGenerated", ORANGE),
        (f"{unique_players}", "Player Types\nCovered", PINK),
        (f"{unique_cultures}", "Cultural\nRegisters", BROWN),
        (f"{total_snippets:,}", "Annotated\nSnippets", ORANGE),
    ]
    
    for i, (value, label, color) in enumerate(metrics):
        ax = fig.add_subplot(gs[0, i])
        ax.set_facecolor(WARM_WHITE)
        ax.axis('off')
        
        # Card background
        card = mpatches.FancyBboxPatch(
            (0.05, 0.05), 0.9, 0.9,
            boxstyle="round,pad=0.06", facecolor=color, alpha=0.1,
            edgecolor=color, linewidth=2,
            transform=ax.transAxes
        )
        ax.add_patch(card)
        
        # Value
        ax.text(0.5, 0.6, value, ha='center', va='center',
                fontsize=38, fontweight='bold', color=color,
                transform=ax.transAxes)
        # Label
        ax.text(0.5, 0.22, label, ha='center', va='center',
                fontsize=12, fontweight='medium', color=DEEP_BROWN,
                linespacing=1.4, transform=ax.transAxes)
    
    fig.suptitle("FIA Team 1 Pipeline — Key Metrics",
                 fontsize=18, fontweight='bold', color=DEEP_BROWN, y=1.02)
    
    plt.tight_layout()
    fig.savefig(CHARTS_DIR / "00_summary_dashboard.png", dpi=200, bbox_inches='tight')
    plt.close()
    print("  Chart 0: Summary Dashboard")

# ============================================================
# MAIN
# ============================================================
def main():
    print("Loading output data...")
    data = load_all_outputs()
    print(f"Loaded {len(data)} scenarios.\n")
    
    print("Generating presentation charts:\n")
    chart_summary_dashboard(data)
    chart_radial_player_distribution(data)
    chart_culture_treemap(data)
    chart_ridgeline_wordcount(data)
    chart_signal_radar(data)
    chart_heatmap(data)
    chart_snippet_depth(data)
    
    print(f"\n{'='*50}")
    print(f"All 7 charts saved to: {CHARTS_DIR}/")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()

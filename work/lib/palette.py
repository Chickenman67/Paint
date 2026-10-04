# work/lib/palette.py — Per-segment palettes from ref_style_spec.md + k-means sampling.
#
# Source: work/ref/measure_palette.py (k-means, k=6) over frames 1-89 (seg 1)
# and 99-180 (seg 2). Output JSON: work/ref/_palette_{1,2}.json.
#
# Segment 1 (HD 188753 Ab) — triple-star world:
#   Top color (38%): pure red — the dominant red sun / "alert" accent
#   White (21%): paper background / title strip
#   Dark navy (11%): deep space / outlines
#   Yellow (9%): star / caption accent
#   Light blue (11%): cool star light / sky
#   Muted purple (10%): the planet itself
#
# Segment 2 (HD 80606 b) — whiplash planet:
#   Top color (40%): near-black deep space
#   Warm yellow (19%): the planet's day side / caption accent
#   Red (11%): the heat / warning
#   Cream (10%): planet highlights
#   Blue (11%): cool counter-accent
#   Dark red (9%): deep heat
#
# Both segments use yellow as the primary caption color (consistent with the
# reference's signature yellow text-on-illustration).

# --- Common: yellow caption color used across segments (per reference) ---
YELLOW_CAPTION = (250, 178, 11)   # #FAB20B — measured segment 1 accent

# --- Common: ink/outline color ---
INK = (0, 0, 0)

# --- Common: paper/background base ---
PAPER = (254, 254, 254)

# --- Segment 1: HD 188753 Ab (k-means k=6, frames 1-89) ---
SEGMENT_1 = {
    'name': 'HD 188753 Ab',
    'ink': INK,
    'paper': PAPER,
    'bg': (196, 197, 247),             # light blue (sky / cool star light)
    'accent1': (238, 32, 11),          # RED — the dominant red sun / alert
    'accent2': (4, 4, 15),             # deep navy / shadow
    'accent3': (250, 178, 11),         # yellow star / caption
    'deep': (4, 4, 15),                # near-black for outlines
    'alert': (238, 32, 11),            # red — for "worse is coming" beats
    'planet': (140, 121, 122),         # muted purple — the planet itself
    'caption': YELLOW_CAPTION,         # yellow floating captions
    'cream': (254, 254, 254),          # white paper
}

# --- Segment 2: HD 80606 b (k-means k=6, frames 99-180) ---
SEGMENT_2 = {
    'name': 'HD 80606 b',
    'ink': INK,
    'paper': (249, 227, 218),          # warm cream — paper background
    'bg': (1, 1, 10),                  # near-black deep space
    'accent1': (247, 195, 6),          # warm yellow — the day side / caption
    'accent2': (239, 68, 3),           # red — the heat
    'accent3': (249, 227, 218),        # cream highlights
    'deep': (1, 1, 10),                # pure black deep space
    'alert': (239, 68, 3),             # bright red — for "+500C" warnings
    'planet': (247, 195, 6),           # warm yellow — the planet's day side
    'planet_cool': (36, 126, 166),     # blue — the night side
    'planet_dark': (129, 37, 17),      # dark red — the deep heat
    'caption': YELLOW_CAPTION,         # yellow floating captions
}


def get_segment_palette(segment_id):
    """Return the palette dict for the given segment id (1 or 2)."""
    if segment_id == 1:
        return SEGMENT_1
    if segment_id == 2:
        return SEGMENT_2
    raise ValueError(f"Unknown segment_id: {segment_id}")


# Header color per segment (the planet name, drawn in the title strip).
# The reference uses BLACK on white for the header, not an accent color.
HEADER_COLOR = INK

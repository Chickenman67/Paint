# work/segments/psrb1257/_schedule.py
# Segment 3 (PSR B1257+12) — CARD SCHEDULE BUILDER
#
# Inputs (already landed in this directory, treated as authoritative):
#   round_1_script.md   — narration, 34 clauses, 317 words (fact-corrected)
#   PALETTE_SPEC.md     — locked 6-color palette + accent cycle
#   ../../lib/type.py   — locked type scale (measured reference realization of §7)
#   ../../lib/stickman.py — MOUTHS table + pose vocabulary
#   ../../lib/title_band.py — white title strip y=22..60
#
# Emits:
#   round_1_card_schedule.json — renderer input (word-index anchored, re-snapped at build)
#   cards.csv                  — human-readable table
#
# Scheduling law (CLAUDE.md §5.2/§5.3): one card = one phrase, 2-5s, hard snap cut at
# every clause break, 0.2s cross-fade for within-card motion ONLY. No card is held
# through a clause break.
#
# The start/end below are PLANNING ESTIMATES from word count. The renderer MUST
# re-derive them from round_N_alignment.json word onsets (lib/align.py) at build
# time. See "snap_rule" on every card and GEO["snap_rule"].

import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# 1. Narration clauses, verbatim from round_1_script.md
# ---------------------------------------------------------------------------

CLAUSES = [
    (1,  "Here is a star that has already died."),
    (2,  "It is still spinning, and it is still talking."),
    (3,  "And it is not spinning alone."),
    (4,  "A neutron star."),
    (5,  "City-sized."),
    (6,  "Denser than anything should be allowed."),
    (7,  "Its fuel ran out, it exploded, and the rest collapsed in here."),
    (8,  "That collapse is what makes it spin. Fast."),
    (9,  "One turn takes six thousandths of a second."),
    (10, "Beams of radio light rake out of its magnetic poles."),
    (11, "On and off and on. A lighthouse made of a dead star."),
    (12, "PSR B1257 plus twelve."),
    (13, "It has three planets."),
    (14, "One is barely heavier than the Moon. Two weigh four times the Earth."),
    (15, "That is not a solar system. That is rubble in a minefield."),
    (16, "Their laps take twenty-five days, sixty-seven, and ninety-eight."),
    (17, "So how do you find a planet around a corpse? You listen to the ticks."),
    (18, "Every rotation has a signature. Any wobble means something tugs."),
    (19, "Aleksander Wolszczan found that pulsar in 1990. It had a wobble in it."),
    (20, "He waited two years for it to come back. It came back."),
    (21, "A neutron star should not have a planet. It exploded. It is a grave."),
    (22, "But the wobble was steady, and rhythmic, and never stopped."),
    (23, "Something small was pulling on the beam, forever, on a schedule."),
    (24, "The first confirmed planets ever found around a dead star."),
    (25, "They named the planets after the things that haunt you."),
    (26, "Draugr. Phobetor. Poltergeist."),
    (27, "And they named the star PSR B1257 plus twelve."),
    (28, "The name is not a name. It is a spot in the sky, written in digits."),
    (29, "Twelve fifty-seven. Plus twelve. That is the entire name."),
    (30, "Here is the part that should bother you."),
    (31, "These did not form around a star that was burning."),
    (32, "They formed here, or they survived being made here."),
    (33, "The radiation on them now would take an atmosphere apart in an afternoon."),
    (34, "Three rocks and one collapsed core. Turning, forever, in the dark."),
]
CLAUSE_TEXT = dict(CLAUSES)

# ---------------------------------------------------------------------------
# 2. Card plan.
#    Merges exist only to hold every card inside the 2-5s window.
# ---------------------------------------------------------------------------

# Accent vocabulary: the 4 locked card values from PALETTE_SPEC.md §2.
#   cream  #F2EAD6  paper/bone motif — the only LIGHT card value
#   bone   #DCE6EC  star core, planets, starfield, type on void
#   amber  #E8A33D  beams, lethal light, the heat
#   violet #6E5A9C  radiation haze, orbit arcs — SHAPES ONLY, never type
# NO red: ../../lib/stickman.py:24 SHIRT=(200,50,50) is the character's fixed global
# and is the only red on screen in all 12 segments.
CREAM, BONE, AMBER, VIOLET = "cream", "bone", "amber", "violet"

PLAN = [
 # ---- BEAT 1  HOOK -------------------------------------------------------
 dict(id="hook_dead",      beat="B1 HOOK",        cls=[1],
      cap="HERE IS A STAR THAT HAS ALREADY DIED.", banner=None,
      accent=BONE, stick=("flat", "standing", 480, (400, 200)),
      motion="star_pulse_0.5Hz",
      sketch="bg_void_stars; far dead star cx=980 cy=300 r=46, bone core, 2 FLAT violet "
             "halo rings r=64/78 at 12%/22% alpha (no gradient); a violet nebula wisp "
             "(wobbly 9-gon, seed 31) at 8% alpha across the lower-left third; 64pt heavy "
             "'ALREADY DEAD' in bone with a 3px slate-black outline ON the star; stickman "
             "x=400 y_top=200 h=480 flat/standing, feet y=680; caption x=70 y=652"),
 dict(id="hook_talking",   beat="B1 HOOK",        cls=[2],
      cap="IT IS STILL SPINNING, AND IT IS STILL TALKING.", banner=None,
      accent=VIOLET, stick=("skeptical", "pointing", 480, (400, 210)),
      motion="arc_pulse + spin_step_0.25s",
      sketch="bg_void_stars; star cx=980 cy=300 r=46 bone; THREE violet radio arcs "
             "r=110/170/230 centred on the star, opacity stepping 20/55/15% on a 0.25s "
             "cycle (quantized, never tweened); spin_step: one bone meridian tick on the "
             "star limb advancing 90deg per 0.25s stamp, 4 stamps per revolution; "
             "stickman x=400 y_top=210 h=480 skeptical/pointing, right arm toward the "
             "star; caption x=70 y=652"),
 dict(id="hook_not_alone", beat="B1 HOOK",        cls=[3, 4],
      cap="AND IT IS NOT SPINNING ALONE.", banner="A NEUTRON STAR",
      accent=AMBER, stick=("awed_brows", "hands_up", 480, (400, 200)),
      motion="star_pulse + head_tilt_0.25s",
      sketch="bg_void_stars; star cx=980 cy=300 r=46 with a 2px AMBER limb ring — the "
             "first hot color in the segment, so the eye registers the shift; 64pt heavy "
             "'A NEUTRON STAR' amber with a 3px slate-black outline, centred on the star "
             "at (980,300); stickman x=400 y_top=200 h=480 awed_brows/hands_up, head "
             "tilting 4deg per 0.25s stamp; caption x=70 y=652"),

 # ---- BEAT 2  THE PULSAR -------------------------------------------------
 dict(id="psr_size",       beat="B2 THE PULSAR",  cls=[5, 6],
      cap="CITY-SIZED. DENSER THAN ANYTHING SHOULD BE ALLOWED.",
      banner="20 KM ACROSS", accent=BONE, stick=("frown", "standing", 400, (400, 300)),
      motion="core_breathe",
      sketch="bg_void_stars; pulsar core cx=900 cy=330 r=54, 3-STOP radial gradient "
             "#FFFFFF (r=0) -> #DCE6EC (r=0.55) -> #6E5A9C (r=1.0) — the ONLY gradient "
             "in the segment, legal here because the star core is the emissive subject "
             "(PALETTE_SPEC.md §3) — plus texture.stipple_overlay(density=0.02, "
             "seed=41); 18pt bone annotation '20 KM ACROSS' centred at (900,404); a 3px "
             "bone scale bracket with end ticks from x=760 to x=1040 at y=430; "
             "stickman x=400 y_top=300 h=400 frown/standing; caption x=70 y=652"),
 dict(id="psr_collapse",   beat="B2 THE PULSAR",  cls=[7],
      cap="ITS FUEL RAN OUT, IT EXPLODED, AND COLLAPSED IN HERE.",
      banner=None, accent=AMBER, stick=("worried", "shielding_eyes", 480, (400, 200)),
      motion="collapse_in_1.2s + flash",
      sketch="bg_void_stars; amber starfield streaks radiating from (900,330) in three "
             "quantized length steps, each on its own 0.25s stamp; a debris ring of 9 "
             "AMBER rock blobs r=6..14 on an ellipse rx=300 ry=90 at (900,330), each "
             "inward on its own 0.25s stamp; the core r=54 brightens to full white at "
             "t=0.9s then SNAPS to r=30 on one 0.25s stamp; stickman x=400 y_top=200 "
             "h=480 worried/shielding_eyes; caption x=70 y=652"),
 dict(id="psr_spin",       beat="B2 THE PULSAR",  cls=[8],
      cap="THAT COLLAPSE IS WHAT MAKES IT SPIN. FAST.", banner=None,
      accent=VIOLET, stick=("flat", "standing", 400, (400, 300)),
      motion="spin_step_0.25s (4 stamps/rev)",
      sketch="bg_void_stars; core cx=900 cy=330 r=30 flat white; two 2px VIOLET magnetic "
             "field arcs lofting above and below the poles (wobble seed 52); one AMBER "
             "spin tick on the limb advancing 90deg per 0.25s stamp. VISUAL PACE ONLY — "
             "not to scale; the narration says milliseconds and the discrepancy is the "
             "joke, so do NOT annotate it. Since E2 the narration agrees with the truth here — "
             "'six thousandths of a second’ — so the builder may now annotate "
             "the true 6.2ms period on this card. "
             "stickman x=400 y_top=300 h=400 flat/standing; "
             "caption x=70 y=652"),
 dict(id="psr_rate",       beat="B2 THE PULSAR",  cls=[9],
      cap="ONE TURN TAKES SIX THOUSANDTHS OF A SECOND.", banner="ONE TURN / 6 MS",
      accent=BONE, stick=(None, None, 0, None),
      motion="spin_step + counter_roll",
      sketch="DIAGRAM-ONLY. bg_void_stars; core cx=560 cy=300 r=30; a 2px BONE stopwatch "
             "ring (ellipse r=190) centred (560,300) carrying 60 tick marks; one AMBER "
             "tick chases the ring at 6.2 MILLISECONDS PER REV — that is 160.8 turns per "
             "second, so 25 stamps per rev at 0.25s and it reads as a blur, which is the "
             "point; 64pt heavy '6 MILLISECONDS' bone with a 3px slate-black outline "
             "centred at (560,300); 18pt bone annotation 'PER TURN' at (560,510); NO "
             "stickman. FACT FLAG E2 (APPLIED) — the earlier narration said 'about a "
             "sixth of a second' (167ms), 27x the true 6.2ms period, and this card as "
             "designed would have contradicted the voice. work/scripts.py now reads 'One "
             "turn takes six thousandths of a second.' Do not restore the old wording, "
             "and do not label the 161 figure as a period: 161 is the frequency in Hz."),
 dict(id="psr_beams",      beat="B2 THE PULSAR",  cls=[10],
      cap="BEAMS OF RADIO LIGHT RAKE OUT OF ITS MAGNETIC POLES.",
      banner="RADIO BEAMS", accent=AMBER, stick=("shielding_eyes", "shielding_eyes", 480, (400, 200)),
      motion="beam_sweep_3.0s",
      sketch="bg_void_stars; core cx=900 cy=330 r=30; TWO opposed beam cones from the "
             "poles, apex alpha 1.0 ramping to tip alpha 0.0 along the axis, apex "
             "#DCE6EC shifting to #E8A33D at ~70% of the length so the cone reads as a "
             "two-tone funnel, MAX 6px blur on the FILL layer only; the 2px AMBER cone "
             "EDGES are drawn UNBLURRED on top — the gradient is the fill, the "
             "hand-drawn line is the line, and that is what keeps it from reading as a "
             "stock lens flare; both cones rotate as a rigid pair, 1 rev / 3.0s; flat "
             "violet halo rings r=64/78 at 12%/22% alpha; stickman x=400 y_top=200 "
             "h=480 shielding_eyes; caption x=70 y=652"),
 dict(id="psr_lighthouse", beat="B2 THE PULSAR",  cls=[11],
      cap="ON AND OFF AND ON. A LIGHTHOUSE MADE OF A DEAD STAR.", banner=None,
      accent=CREAM, stick=("awed_brows", "pointing", 400, (400, 300)),
      motion="on_off_strobe_1.1s",
      sketch="CREAM CARD — full-bleed #F2EAD6 from y=61 to y=719. A lighthouse silhouette "
             "in 3px slate-black flat strokes: tower base at x=1000,y=620, lamp housing "
             "at (1000,300); two AMBER beam wedges from the lamp at a 40deg half-angle, "
             "hard on/off on a 1.1s cycle (a pulse train, NOT a fade); 'ON' and 'OFF' "
             "stamped in 18pt slate-black Consolas Bold directly beneath the lamp, "
             "swapping on each cycle. ALL text on this card is slate-black — amber on "
             "cream is 1.80:1 and bone on cream is 1.06:1, both forbidden "
             "(PALETTE_SPEC.md §1). stickman x=400 y_top=300 h=400 awed_brows/pointing; "
             "caption x=70 y=652 in slate-black"),
 dict(id="psr_name",       beat="B2 THE PULSAR",  cls=[12, 13],
      cap="PSR B1257+12. IT HAS THREE PLANETS.", banner="PSR B1257+12",
      accent=BONE, stick=("oval", "pointing", 480, (400, 200)),
      motion="star_pulse + name_stamp_settle",
      sketch="bg_void_stars; core cx=880 cy=300 r=30 bone; the name arrives as a STAMP: "
             "64pt 'PSR B1257+12', bone fill, 3px slate-black outline, rotated -3deg, "
             "settling from scale 1.18 to 1.00 on ONE 0.25s stamp (no tween) at (880,300); "
             "18pt amber stamp 'VIRGO' top-right at (1080,120) — E1, corrected from "
             "'VELA': the pulsar is in Virgo; Vela hosts PSR B0833-45, a different pulsar "
             "with no planets. The constellation now shows on the card but is no longer "
             "spoken; three bone dots r=7 at "
             "(1090,180)/(1130,180)/(1170,180) appearing on three consecutive 0.25s "
             "stamps, one per word of 'three planets'; stickman x=400 y_top=200 h=480 "
             "oval/pointing; caption x=70 y=652"),

 # ---- BEAT 3  THE THREE PLANETS -----------------------------------------
 dict(id="planet_masses",  beat="B3 THE PLANETS", cls=[14],
      cap="ONE BARELY BEATS THE MOON. TWO WEIGH FOUR TIMES EARTH.", banner=None,
      accent=CREAM, stick=("skeptical", "pointing", 400, (400, 300)),
      motion="mass_bar_grow",
      sketch="CREAM CARD. A ledger: three 3px slate-black rules at y=180/300/420 "
             "spanning x=560..1180; one flat slate-black disc per row — Draugr r=16 at "
             "x=620, Phobetor r=40 at x=860, Poltergeist r=42 at x=1120 — so the shape "
             "itself carries the fact: one speck, then two near-twin heavies. NO gradient "
             "and NO band texture (the three planets are on PALETTE_SPEC.md §3's gradient "
             "denylist); a 64pt heavy slate-black mass figure grows on each disc in 0.25s "
             "stamps — 'MOON-SIZE' on row 1, '4 EARTH' on rows 2 and 3. FACT FLAG E3 "
             "(APPLIED) — the earlier narration said two of the three weighed about as "
             "much as the Moon, which inverted the real picture. True masses are Draugr "
             "0.020, Phobetor 3.9, Poltergeist 4.3 Earth masses: ONE is Moon-ish and TWO "
             "are about four Earths. work/scripts.py now reads 'One is barely heavier "
             "than the Moon. Two weigh four times the Earth.' Keep the disc radii in the "
             "order 16 / 40 / 42 — Draugr innermost and smallest, the other two large and "
             "nearly equal. stickman x=400 y_top=300 h=400 skeptical/pointing; "
             "caption x=70 y=652 in slate-black"),
 dict(id="planet_minefield", beat="B3 THE PLANETS", cls=[15],
      cap="THAT IS NOT A SOLAR SYSTEM. THAT IS RUBBLE IN A MINEFIELD.",
      banner="RUBBLE", accent=AMBER, stick=("frown", "hands_down", 480, (400, 200)),
      motion="debris_jitter",
      sketch="bg_void_stars; pulsar core cx=900 cy=180 r=26, cropped by the title strip; "
             "an AMBER radiation wash — a wobbly 8-lobed polygon, wobble seed 71 — "
             "spanning x=340..1240, y=120..660, flat 10% fill with a 2px amber outline; "
             "11 slate-black rock blobs (irregular 7-gons, r=8..26) on a deterministic "
             "grid inside the wash, each jittering 2px on its own 0.25s stamp; 64pt heavy "
             "'RUBBLE' amber at (760,400) on the wash; stickman x=400 y_top=200 h=480 "
             "frown/hands_down, drawn INSIDE the 10% wash so his black limbs keep full "
             "separation; caption x=70 y=652"),
 dict(id="planet_periods", beat="B3 THE PLANETS", cls=[16],
      cap="THEIR LAPS TAKE 25, 67, AND 98 DAYS.",
      banner="25 / 67 / 98 DAYS", accent=BONE, stick=(None, None, 0, None),
      motion="orbit_ring_step",
      sketch="DIAGRAM-ONLY. bg_void_stars; core cx=640 cy=330 r=24; THREE concentric "
             "orbit ellipses, all 2px BONE — violet is a shape color and never carries "
             "type, and 18pt violet annotation would be 3.48:1 — with rx=170/300/430 and "
             "ry=58/100/142, all centred (640,330), inner to outer Draugr / Phobetor / "
             "Poltergeist; one bone dot r=9 on each ring, advancing one 0.25s step per "
             "lap; 18pt bone labels at the ring apexes with 3px leader lines — '25 D' at "
             "(640,262), '67 D' at (640,222), '98 D' at "
             "(640,180); the banner '25 / 67 / 98 DAYS' set at 64pt bone at (640,510); "
             "NO stickman. This is the diagram the next three cards talk over, so it is "
             "drawn to be re-used rather than admired. FACT FLAG E4 (APPLIED) — the "
             "earlier banner read 66 / 204 / 365 days, which are not this system's "
             "periods. True orbital periods are 25.262, 66.5419 and 98.2114 days, spoken "
             "as 'twenty-five days, sixty-seven, and ninety-eight'. Keep the inner-to-"
             "outer order matching those numbers."),

 # ---- BEAT 4  HOW THEY WERE FOUND ---------------------------------------
 dict(id="how_find",       beat="B4 THE SEARCH",  cls=[17],
      cap="SO HOW DO YOU FIND A PLANET AROUND A CORPSE?", banner=None,
      accent=CREAM, stick=("worried_thinker", "thinker", 400, (400, 300)),
      motion="none (static — the beat asks a question)",
      sketch="CREAM CARD, deliberately near-empty. One 3px slate-black question mark "
             "drawn as linework at (860,300), 200px tall, 2px wobbly stroke, wobble seed "
             "83; a slate-black coffin-outline rectangle 3px at x=300..420, y=340..520 "
             "with a lid rule at y=372 — the 'corpse' half, drawn plainly, no gore, no "
             "skull; a slate-black ear shape as a 2px arc at (1100,300) with three "
             "concentric 2px arcs r=40/70/100 — the 'listen' half. Nothing else on this "
             "card; the emptiness IS the pacing. stickman x=400 y_top=300 h=400 "
             "worried_thinker/thinker; caption x=70 y=652 in slate-black"),
 dict(id="how_signature",  beat="B4 THE SEARCH",  cls=[18],
      cap="EVERY ROTATION HAS A SIGNATURE. WOBBLE MEANS A TUG.",
      banner=None, accent=VIOLET, stick=(None, None, 0, None),
      motion="waveform_squash",
      sketch="DIAGRAM-ONLY. bg_void_stars; a BONE timing trace across x=120..1180 at "
             "y=300: nine evenly spaced 2px spikes, redrawn on a 0.25s cycle; the 4th and "
             "7th spikes have their peak displaced 6px right — that is the wobble, drawn "
             "rather than labelled; a 3px amber bracket under each displaced peak with a "
             "3px leader up to it; 18pt bone 'TUG' at (470,360) and (830,360); a bone "
             "baseline rule at y=380 spanning the full width; 64pt heavy 'WOBBLE = TUG' "
             "bone at (640,500); NO stickman"),
 dict(id="how_1990",       beat="B4 THE SEARCH",  cls=[19],
      cap="WOLSZCZAN FOUND THAT PULSAR IN 1990. IT HAD A WOBBLE IN IT.",
      banner="1990", accent=BONE, stick=("skeptical", "shrugged", 400, (400, 300)),
      motion="stamp_settle",
      sketch="bg_void_stars; a 2px bone waveform panel x=560..1180, y=180..520; the "
             "wobbled pulse train from how_signature inside it at 0.7 scale, re-stamped "
             "every 0.25s; a heavy 64pt '1990' plate — bone fill, 3px slate-black "
             "outline — at (870,350), settling from scale 1.15 to 1.00 on one 0.25s "
             "stamp; an 18pt bone stamp 'VLA' at (1080,470); stickman x=400 y_top=300 "
             "h=400 skeptical/shrugged; caption x=70 y=652. FACT FLAG E5 (APPLIED) — "
             "the card was id=how_1992 with a '1992' plate and a 'NOBODY BELIEVED HIM' "
             "caption, both wrong. The pulsar was discovered 9 February 1990; the first "
             "two planets were announced in January 1992 and the third later that year, "
             "confirmed on a later re-observation — which is what the two-year gap on "
             "how_two_years actually refers to. 'Nobody believed him' was unsourced and "
             "is dropped rather than reworded; the suspicion now lives in the shrug."),
 dict(id="how_two_years",  beat="B4 THE SEARCH",  cls=[20],
      cap="HE WAITED TWO YEARS FOR IT TO COME BACK. IT CAME BACK.", banner=None,
      accent=VIOLET, stick=("worried", "pointing", 400, (400, 300)),
      motion="tally_2yr + pulse_repeat",
      sketch="bg_void_stars; a VIOLET TALLY — 24 thin 3px slate-black vertical rules at "
             "x=600..1180, y=420, grouped 12|12 with a 40px gap: two years of ticks and "
             "no words; the how_signature trace replays once across the top half "
             "(x=120..1180, y=200..300), the replay landing on a 0.25s stamp; an 18pt "
             "bone '2 YEARS' at (890,470) under the tally; 64pt heavy 'IT CAME BACK' "
             "bone at (640,120); stickman x=400 y_top=300 h=400 worried/pointing toward "
             "the tally; caption x=70 y=652. FACT FLAG E5 (APPLIED) — this card is now "
             "consistent with how_1990: the pulsar was found in 1990, the wobble was "
             "announced with the first two planets in January 1992, and the third arrived "
             "on the re-observation, so the two-year tally runs 1990 -> 1992."),
 dict(id="how_grave",      beat="B4 THE SEARCH",  cls=[21],
      cap="A NEUTRON STAR SHOULD NOT HAVE A PLANET. IT IS A GRAVE.",
      banner="A GRAVE", accent=AMBER, stick=("sad_smile", "hands_down", 560, (400, 120)),
      motion="none (static hold — the dread beat)",
      sketch="DREAD CARD, amber. bg_void_stars; the core drawn as an ABSENCE: an empty "
             "2px amber ring r=44 at (900,330) with nothing inside it; three flat "
             "slate-black mound shapes (7-gons, wobble seeds 91/92/93) at (700,600), "
             "(900,610), (1100,600) with radii 70/86/64 — no crosses, no headstones, no "
             "skulls; 64pt heavy 'A GRAVE' amber centred at (900,300), inside the empty "
             "ring; stickman x=400 y_top=120 h=560 sad_smile/hands_down — the BIGGEST "
             "figure so far, arms straight down, head 6px lower than the previous cards "
             "so the slump reads without a single new line; caption x=70 y=652. Per "
             "§10.8 this is one of the two beats that must carry the stickman at the "
             "moment the fate lands."),
 dict(id="how_steady",     beat="B4 THE SEARCH",  cls=[22],
      cap="THE WOBBLE WAS STEADY, AND RHYTHMIC, AND NEVER STOPPED.",
      banner=None, accent=VIOLET, stick=(None, None, 0, None),
      motion="metronome_step",
      sketch="DIAGRAM-ONLY. bg_void_stars; a metronome in 2px bone linework — trapezoid "
             "body x=560..760, y=300..560, pendulum pivot at (660,320); the pendulum "
             "swings +/-26deg in quantized 0.25s steps, one full swing per clause beat, "
             "and NEVER pauses — that is the whole meaning of the card; a flat violet "
             "rectangle x=120..480, y=280..560 at 8% alpha behind the swing arc (shape "
             "color, carries no word); 18pt bone 'STEADY' at (300,240) and 'NEVER STOPS' "
             "at (300,600); 64pt heavy 'STEADY AND RHYTHMIC' bone at (880,420); "
             "NO stickman"),
 dict(id="how_tug",        beat="B4 THE SEARCH",  cls=[23],
      cap="SOMETHING SMALL WAS PULLING ON THE BEAM. ON A SCHEDULE.",
      banner=None, accent=BONE, stick=("flat", "pointing", 400, (400, 300)),
      motion="tug_step",
      sketch="bg_void_stars; a single AMBER beam wedge from (900,300) toward the "
             "lower-right, 2px edges over a 6px-blurred fill, sweeping in 0.25s steps; a "
             "bone dot r=11 at (1120,520) that lurches 8px toward the beam and back on "
             "alternating 0.25s stamps — the tug made visible; a 2px bone schedule ladder "
             "at x=200..560, y=520 with five rungs at 60px spacing, one rung highlighted "
             "amber; stickman x=400 y_top=300 h=400 flat/pointing along the beam; "
             "caption x=70 y=652"),
 dict(id="how_first",      beat="B4 THE SEARCH",  cls=[24],
      cap="THE FIRST CONFIRMED EXOPLANETS EVER, AROUND A DEAD STAR.",
      banner="FIRST EXOPLANETS EVER", accent=AMBER,
      stick=("relief", "hands_up", 480, (400, 200)),
      motion="star_pulse + arms_up_stamp",
      sketch="PAYOFF CARD, amber. bg_void_stars; core cx=880 cy=320 r=40 at full 3-stop "
             "gradient; the three planet discs at r=18/22/34 on the two inner orbit rings "
             "from planet_periods, re-stamped into existence one per 0.25s stamp, each "
             "with a flat 2px amber ring highlight; a 64pt heavy 'FIRST EVER' amber plate "
             "with a 3px slate-black outline at (880,320); stickman x=400 y_top=200 "
             "h=480 relief/hands_up — AWE, not fear, per the B4 payoff note in "
             "round_1_script.md; his "
             "arms stamp up on the word 'confirmed'. A 0.5s palette bridge follows."),

 # ---- BEAT 5  THE NAMING -------------------------------------------------
 dict(id="name_why",      beat="B5 THE NAMING",  cls=[25],
      cap="THEY NAMED THE PLANETS AFTER THE THINGS THAT HAUNT YOU.",
      banner=None, accent=VIOLET, stick=("worried", "shrugged", 400, (400, 300)),
      motion="mist_drift",
      sketch="bg_void_stars; a flat violet haze band (wobbly 9-gon, wobble seed 111) "
             "spanning x=120..1180, y=420..640 at 9% fill with a 2px violet outline; five "
             "flat slate-black 2px silhouettes drifting 3px left-right on 0.25s stamps "
             "inside the haze — deliberately ambiguous, NOT yet skulls; they resolve on "
             "the next card. stickman x=400 y_top=300 h=400 worried/shrugged; "
             "caption x=70 y=652"),
 dict(id="name_three",     beat="B5 THE NAMING",  cls=[26],
      cap="DRAUGR. PHOBETOR. POLTERGEIST.", banner=None,
      accent=CREAM, stick=("awed_brows", "pointing", 400, (400, 300)),
      motion="name_stamp_x3 (one per word — see timing note)",
      sketch="CREAM CARD. Three SKULL plates, each a 3px slate-black circle 96px across "
             "at (330,300)/(700,300)/(1070,300) with two 3px slate-black eye slots and a "
             "3px jaw rule — cartoon-flat, no gradients, no teeth detail; the reference's "
             "detailed teeth-and-tongue mouth is copyrighted character design and is "
             "NOT copied. Under each, a heavy 64pt slate-black name stamped in sequence "
             "— 'DRAUGR' / 'PHOBETOR' / 'POLTERGEIST' — each settling from scale 1.18 to "
             "1.00 on ONE 0.25s stamp. TIMING: word count says 0.9s and that is wrong; "
             "these are three multi-syllable names, so expect ~2.0s from the aligned "
             "audio and land the three stamps on the three word ONSETS, not on evenly "
             "spaced times. stickman x=400 y_top=300 h=400 awed_brows/pointing; "
             "caption x=70 y=652 in slate-black"),
 dict(id="name_star",      beat="B5 THE NAMING",  cls=[27],
      cap="AND THEY NAMED THE STAR PSR B1257+12.", banner="PSR B1257+12",
      accent=AMBER, stick=("flat", "pointing", 480, (400, 200)),
      motion="name_stamp_settle",
      sketch="bg_void_stars; core cx=880 cy=320 r=36 with a 2px amber limb; the heavy "
             "64pt name plate 'PSR B1257+12' re-stamps at (880,320) in amber with a 3px "
             "slate-black outline, settling scale 1.18 -> 1.00 on one 0.25s stamp; the "
             "skull plates are GONE — this beat ends on the star, not on the skulls, so "
             "the naming lands on the corpse; 18pt bone stamp 'VIRGO' at (1080,120) — E1, "
             "corrected from 'VELA'; stickman x=400 y_top=200 h=480 flat/pointing; "
             "caption x=70 y=652"),
    dict(id="name_coordinates", beat="B5 THE NAMING", cls=[28],
      cap="A NAME THAT IS JUST COORDINATES.",
      banner="A SPOT ON THE SKY", accent=BONE, stick=("smirk", "shrugged", 400, (400, 300)),
      motion="sky_grid + crosshair_drop",
      sketch="bg_void_stars; a 2px bone sky GRID of seven vertical rules and five horizontal rules spanning x=560..1180, y=180..560, with 3px ticks every 60px — a star chart, drawn plainly, no labels yet; a 3px bone crosshair at (860,330) with a 2px circle r=18 dropping to it on one 0.25s stamp and LOCKING; the crosshair pulses on every subsequent stamp, because this is where the thing is; 64pt heavy bone 'A SPOT ON THE SKY' at (860,640); 18pt bone annotation 'SKY COORDINATES' at (860,600); stickman x=400 y_top=300 h=400 smirk/shrugged — the wry beat survives, but it is wry at the bureaucracy, not at a punchline; caption x=70 y=652. FACT FLAG E6 (APPLIED) — this card was id=name_base_eight and asserted a base-eight joke told by Wolszczan and Frail. There is no such joke; the octal reading of 1257 is a numerical accident with no connection to the name, and attributing it to the discoverers was a fabrication. Replaced with the verifiable fact: PSR 1257+12 is a sexagesimal sky coordinate, 12h57m right ascension and plus 12 degrees declination."),
    dict(id="name_just_digits", beat="B5 THE NAMING",  cls=[29],
      cap="TWELVE FIFTY-SEVEN. PLUS TWELVE. THAT IS THE ENTIRE NAME.",
      banner=None, accent=CREAM, stick=("flat", "hands_down", 400, (400, 300)),
      motion="digit_flip",
      sketch="CREAM CARD, deliberately plain. Four 3px slate-black digit frames 120px square at (500,300)/(660,300)/(820,300)/(980,300) holding the digits '1' '2' '5' '7' in heavy 64pt slate-black; beneath the first two frames an 18pt slate-black label 'RIGHT ASCENSION' at (580,400) and beneath the last two an 18pt label '+12 DEGREES, UP AND NORTH' at (900,400), with a 3px leader from the label to the frame pair; a heavy 64pt slate-black 'THAT IS THE NAME' at (640,510). No illustration, no texture, no gradient, nothing else — the flatness is the point: a dead star reduced to a row of numbers. stickman x=400 y_top=300 h=400 flat/hands_down; caption x=70 y=652 in slate-black. A 0.5s palette bridge follows."),

 # ---- BEAT 6  THE CLOSING IMAGE -----------------------------------------
 dict(id="close_bother",   beat="B6 FATE",        cls=[30],
      cap="HERE IS THE PART THAT SHOULD BOTHER YOU.", banner=None,
      accent=VIOLET, stick=("worried_thinker", "thinker", 480, (400, 200)),
      motion="haze_swell",
      sketch="bg_void_stars; the violet radiation wash from planet_minefield returns, "
             "now filling x=200..1240, y=110..670 at 9% flat fill, swelling to 12% over "
             "four 0.25s stamps; nothing else is added — the emptiness is the warning. "
             "stickman x=400 y_top=200 h=480 worried_thinker/thinker, hand under chin; "
             "caption x=70 y=652"),
 dict(id="close_no_burn",  beat="B6 FATE",        cls=[31],
      cap="THESE DID NOT FORM AROUND A STAR THAT WAS BURNING.", banner=None,
      accent=BONE, stick=("skeptical", "pointing", 400, (400, 300)),
      motion="flame_extinguish",
      sketch="bg_void_stars; a 2px bone FLAME outline in three stacked lobes at "
             "(1000,300) r=90, drawn as LINEWORK ONLY — no fill, no gradient; it "
             "EXTINGUISHES, each lobe collapsing to nothing on its own 0.25s stamp, "
             "bottom lobe first over three stamps, leaving 6px of ash; a flat "
             "slate-black disc r=20 appears inside the dead flame at (1000,300) — the "
             "remnant star; 18pt bone 'WHAT WAS LEFT' at (1000,440); stickman x=400 "
             "y_top=300 h=400 skeptical/pointing at the dead flame; caption x=70 y=652"),
 dict(id="close_formed",   beat="B6 FATE",        cls=[32],
      cap="THEY FORMED HERE, OR THEY SURVIVED BEING MADE HERE.", banner=None,
      accent=AMBER, stick=("worried", "hands_down", 400, (400, 300)),
      motion="debris_accumulate",
      sketch="bg_void_stars; the remnant disc r=20 at (1000,300) with its 2px amber "
             "limb; the rock blobs from planet_minefield fly INWARD and stick to the "
             "limb, one per 0.25s stamp, until six amber-outlined slate-black blobs sit "
             "on the circumference — made here, not inherited; a flat 2px amber "
             "accretion ring at r=30; stickman x=400 y_top=300 h=400 worried/hands_down; "
             "caption x=70 y=652"),
 dict(id="close_radiation", beat="B6 FATE",        cls=[33],
      cap="THE RADIATION WOULD TEAR AN ATMOSPHERE APART BY AFTERNOON.",
      banner="RADIATION BATH", accent=VIOLET, stick=("worried", "cowering", 480, (400, 200)),
      motion="veil_stripes",
      sketch="RADIATION BATH, violet. bg_void_stars; core cx=1000 cy=300 r=30; NINE flat "
             "AMBER beam rays 3px wide at 2px spacing raking from the core across the "
             "left of frame at -18deg, each blinking on a staggered 0.25s phase so the "
             "field shimmers; a flat violet rectangle x=140..820, y=140..640 at 10% "
             "alpha is the irradiated zone (shape color, carries no word); inside it a "
             "3px BONE ellipse outline r=110 at (480,390) and a 2px AMBER ellipse r=110 "
             "concentric with it, BOTH on the same frame — the atmosphere, and what is "
             "left of it; 64pt heavy 'IN AN AFTERNOON' bone at (480,560); stickman "
             "x=400 y_top=200 h=480 worried/cowering INSIDE the irradiated zone; "
             "caption x=70 y=652"),
 dict(id="close_finale",   beat="B6 FATE",        cls=[34],
      cap="THREE ROCKS AND ONE COLLAPSED CORE. TURNING, FOREVER.",
      banner=None, accent=BONE, stick=("deadpan_grim", "hands_down", 560, (400, 120)),
      motion="spin_step_0.25s (never decelerates)",
      sketch="FINAL CARD, bone — the only card in the segment that shows the whole system "
             "at once. bg_void_stars; core cx=900 cy=340 r=26 at centre-right; the three "
             "orbit ellipses from planet_periods re-drawn at 0.75 scale in 2px bone; the "
             "three planet discs r=14/17/25 on them; ONE bone spin tick on the core limb "
             "advancing 90deg per 0.25s stamp and NEVER slowing — that is the 'forever'; "
             "every other motion on the card is frozen so the spin is the only thing "
             "moving; 18pt bone labels 'DRAUGR' (640,250) / 'PHOBETOR' (640,180) / "
             "'POLTERGEIST' (640,110) with 3px leaders to their discs — 18pt bone, never "
             "violet at 3.48:1; stickman x=400 y_top=120 h=560 deadpan_grim/hands_down, "
             "the same height as how_grave and close_radiation so the last three cards "
             "read as one continuous reaction instead of three separate poses; "
             "caption x=70 y=652. Hold 0.40s past the last word, then the 3.75s white "
             "bridge from lib/transition.py."),
]

# ---------------------------------------------------------------------------
# 3. Palette — locked, from PALETTE_SPEC.md §1. RGB tuples for the renderer.
# ---------------------------------------------------------------------------

PAL = {
    "ink":    (20, 22, 28),    # #14161C slate-black
    "paper":  (242, 234, 214), # #F2EAD6 bone-cream
    "deep":   (5, 6, 11),      # #05060B void
    "amber":  (232, 163, 61),  # #E8A33D signal amber
    "bone":   (220, 230, 236), # #DCE6EC x-ray bone
    "violet": (110, 90, 156),  # #6E5A9C magnet violet
    "shirt":  (200, 50, 50),   # lib/stickman.py:24 — character's global, never a card accent
}
ACCENT_RGB = {CREAM: PAL["paper"], BONE: PAL["bone"],
              AMBER: PAL["amber"], VIOLET: PAL["violet"]}

# ---------------------------------------------------------------------------
# 4. Type scale — lib/type.py, the measured-reference realization of §7.
#    PALETTE_SPEC.md §4 recommends exactly this over literal §7 points, because
#    segments 1 and 2 are already rendered and iterated on these numbers.
# ---------------------------------------------------------------------------

TYPE = {
    "title_band_px": 44,   # lib/type.py HEADER_PX, black on the cream strip
    "header_stroke": 0,    # lib/title_band.py draws NO stroke (measured reference)
    "caption_px": 27,      # lib/type.py CAPTION_PX
    "caption_stroke": 4,   # lib/type.py CAPTION_STROKE
    "heavy_px": 64,        # heavy integrated labels (segs 1-2 precedent)
    "heavy_stroke": 4,
    "stamp_px": 18,        # lib/type.py draw_stamp = STAMP_PX + 11
    "tiny_px": 18,         # §7 tiny diagram annotations — never violet
    "family_bold": "consolab.ttf",
    "family_reg": "consola.ttf",
}

# ---------------------------------------------------------------------------
# 5. Frame geometry
# ---------------------------------------------------------------------------

GEO = {
    "W": 1280, "H": 720, "fps": 30,
    "title_band": {"y0": 22, "y1": 60, "fill": "paper", "text": "ink",
                   "px": 44, "text": "ink", "align": "center", "x_center": 640,
                   "content": "PSR B1257+12"},
    "art_top": 61,
    "art_bottom": 719,
    "caption": {"x": 70, "y": 652, "px": 27, "max_px_w": 1100,
                "max_chars": 60, "max_words": 12, "one_line": True,
                "on_cream_color": "ink", "on_void_color": "amber"},
    "stickman": {"x_default": 400, "feet_y": 680,
                 "h_hero": 480, "h_dialog": 400, "h_closeup": 560},
    "snap_rule": "card n starts at the onset of its first clause word MINUS 0.20s; "
                 "card n ends at the onset of card n+1's first word (hard cut, no "
                 "fade). The 0.2s cross-fade is legal ONLY inside a card's in-card "
                 "motion. All of these are re-derived from round_N_alignment.json.",
    "first_word_rule": "card 1 is up at t=0.0 and the first spoken word must land at "
                       "t<=0.30, so the header is never late (CLAUDE.md §5.5).",
    "bridges": "0.5s palette bridge after how_first and after name_punchline "
               "(round_1_script.md line 110). The segment-exit bridge is the 3.75s "
               "white bridge in lib/transition.py — §5.7's '0.5s black frame' is "
               "superseded by the measured reference bridge (PALETTE_SPEC.md §2).",
    "gradient_rule": "radial_gradient() is legal on the pulsar core ONLY "
                     "(psr_size, psr_collapse, psr_beams, how_first, psr_name). "
                     "Never on the planets, orbit ellipses, the radiation wash, the "
                     "starfield, the title strip, the skulls, or the stickman "
                     "(PALETTE_SPEC.md §3 denylist).",
    "motion_rule": "0.25s quantized stamps, never smooth tweens, on every motion in "
                   "this segment including the stickman.",
}

# ---------------------------------------------------------------------------
# 6. Schedule
# ---------------------------------------------------------------------------

WPM = 200.0
SEC_PER_WORD = 60.0 / WPM
LEAD = 0.20        # first word lands 0.20s after card 1 is up (must be <= 0.30)
BREATH = 0.08      # the card stays up through the gap; the cut is on the next onset.
                    # §5.6: this gap is the narrator micro-breath and takes a visual event.
TAIL = 0.40        # hold after the last word, before the white bridge

# Cards whose spoken length differs materially from the word-count estimate.
DURATION_OVERRIDE = {
    # three multi-syllable names: word count says 0.9s, spoken length is ~2.0s.
    # Even with the override, the three stamps snap to the three aligned onsets.
    "name_three": 2.0,
}

cards = []
t = 0.0
for idx, p in enumerate(PLAN):
    words = sum(len(CLAUSE_TEXT[c].split()) for c in p["cls"])
    speech = words * SEC_PER_WORD
    dur = DURATION_OVERRIDE.get(p["id"], speech)
    start = 0.0 if idx == 0 else t
    end = start + (LEAD + dur if idx == 0 else dur)
    exp, pose, h, pos = p["stick"]
    cards.append({
        "n": idx + 1,
        "id": p["id"],
        "beat": p["beat"],
        "clauses": p["cls"],
        "narration": " ".join(CLAUSE_TEXT[c] for c in p["cls"]),
        "words": words,
        "start": round(start, 2),
        "end": round(end, 2),
        "duration": round(dur, 2),
        "type": "hold",
        "transition_in": "snap",
        "motion": p["motion"],
        "motion_xfade_s": 0.2,
        "caption": p["cap"],
        "banner": p["banner"],
        "accent": p["accent"],
        "accent_rgb": list(ACCENT_RGB[p["accent"]]),
        "card_value": "cream" if p["accent"] == CREAM else "void",
        "stickman": None if h == 0 else {
            "expression": exp, "pose": pose, "height": h,
            "x_center": pos[0], "y_top": pos[1], "feet_y": pos[1] + h,
        },
        "sketch": p["sketch"],
        "snap_rule": GEO["snap_rule"],
        # word-index anchor into the script, for re-deriving from the alignment file
        "first_word_index": sum(len(CLAUSE_TEXT[c].split())
                                for q in PLAN[:idx] for c in q["cls"]),
    })
    t = end + BREATH

total_s = t - BREATH + TAIL
total_words = sum(c["words"] for c in cards)

# ---------------------------------------------------------------------------
# 7. Validate every hard constraint
# ---------------------------------------------------------------------------

errors = []
for c in cards:
    if not (2.0 <= c["duration"] <= 5.0):
        errors.append(f"card {c['n']} ({c['id']}): duration {c['duration']}s outside 2-5s")
    if len(c["caption"]) > 60:
        errors.append(f"card {c['n']}: caption {len(c['caption'])} chars > 60")
    if len(c["caption"].split()) > 12:
        errors.append(f"card {c['n']}: caption {len(c['caption'].split())} words > 12")
    if c["caption"] != c["caption"].upper():
        errors.append(f"card {c['n']}: caption is not ALL CAPS")
    if c["banner"] and len(c["banner"]) > 60:
        errors.append(f"card {c['n']}: banner {len(c['banner'])} chars > 60")
    if c["accent"] == "red":
        errors.append(f"card {c['n']}: red is reserved for the stickman's shirt")
    if c["card_value"] == "cream" and c["stickman"] is None and c["n"] == 1:
        errors.append("card 1 must not be a cream card (header legibility)")
for a, b in zip(cards, cards[1:]):
    if a["accent"] == b["accent"]:
        errors.append(f"cards {a['n']}->{b['n']}: adjacent cards share accent '{a['accent']}'")
if cards[0]["start"] != 0.0:
    errors.append("card 1 does not start at t=0.0")
if LEAD > 0.30:
    errors.append(f"first word at {LEAD}s; must be <= 0.30s (CLAUDE.md §5.5)")
covered = sorted(c for card in cards for c in card["clauses"])
if covered != [c[0] for c in CLAUSES]:
    errors.append("clause coverage is not exactly 1..34 — gaps or repeats")

# §6 hard rule: the segment's tone must be readable from the stickman alone.
if not any(c["stickman"] for c in cards):
    errors.append("CLAUDE.md §6: no stickman anywhere in the segment")
for beat in sorted({c["beat"] for c in cards}):
    if not any(c["stickman"] and c["beat"] == beat for c in cards):
        errors.append(f"CLAUDE.md §6: beat '{beat}' carries no stickman")
# §10.8: the fate beats must carry him.
for cid in ("how_grave", "close_radiation", "close_finale"):
    if not next(c for c in cards if c["id"] == cid)["stickman"]:
        errors.append(f"CLAUDE.md §10.8: fate card '{cid}' has no stickman")
# §6: at least 5-6 distinct expressions across the segment.
if len({c["stickman"]["expression"] for c in cards if c["stickman"]}) < 5:
    errors.append("CLAUDE.md §6: fewer than 5 distinct stickman expressions")

# ---------------------------------------------------------------------------
# 8. Emit
# ---------------------------------------------------------------------------

def main():
    print(f"cards        {len(cards)}")
    print(f"clauses      {len(covered)}/34 covered, no gaps, no repeats")
    print(f"words        {total_words}")
    print(f"speech       {sum(c['duration'] for c in cards):.2f}s")
    print(f"total        {total_s:.2f}s   (target 60-100s)")
    print(f"wpm          {WPM:.0f} scripted / {total_words / total_s * 60:.1f} effective "
          f"(target 190-213)")
    print(f"card dur     min {min(c['duration'] for c in cards):.2f}s  "
          f"max {max(c['duration'] for c in cards):.2f}s  (target 2-5s)")
    print(f"accents      {sorted({c['accent'] for c in cards})}  "
          f"(4 locked values, adjacent-different verified)")
    print(f"cream cards  {sum(1 for c in cards if c['card_value'] == 'cream')}/{len(cards)}")
    print(f"stickman     {sum(1 for c in cards if c['stickman'])}/{len(cards)} cards, "
          f"{len({c['stickman']['expression'] for c in cards if c['stickman']})} "
          f"expressions, "
          f"{len({c['stickman']['pose'] for c in cards if c['stickman']})} poses")
    print(f"first word   t={LEAD:.2f}s  (must be <= 0.30s)")
    print()
    print("beats:")
    for beat in sorted({c["beat"] for c in cards}):
        bc = [c for c in cards if c["beat"] == beat]
        ns = sum(1 for c in bc if c["stickman"])
        print(f"  {beat:<16} {bc[0]['start']:>6.2f}-{bc[-1]['end']:>6.2f} "
              f"({bc[-1]['end'] - bc[0]['start']:>5.2f}s, {len(bc):>2} cards, "
              f"stickman {ns}/{len(bc)})")
    print()
    if errors:
        print("VALIDATION FAILED")
        for e in errors:
            print("  ! " + e)
        raise SystemExit(1)
    print("all hard constraints pass")
    print()

    out = {
        "segment": "PSR B1257+12",
        "segment_index": 3,
        "round": 1,
        "wav_path": "round_1_audio.wav",
        "alignment_path": "round_1_alignment.json",
        "duration_s": round(total_s, 2),
        "word_count": total_words,
        "narrator_wpm": WPM,
        "effective_wpm": round(total_words / total_s * 60, 1),
        "first_word_t": LEAD,
        "fps": GEO["fps"],
        "geometry": GEO,
        "palette": {k: list(v) for k, v in PAL.items()},
        "accent_roles": {k: list(v) for k, v in ACCENT_RGB.items()},
        "type_scale": TYPE,
        "fact_flags": [
            "ALL SIX FLAGS APPLIED. Narration in work/scripts.py, work/scripts.md and "
            "round_1_script.md is now fact-correct and the WAV must be regenerated.",
            "E1 APPLIED - psr_name and name_star: constellation stamp is VIRGO, not "
            "VELA. PSR B1257+12 is in Virgo; Vela hosts PSR B0833-45, which has no "
            "planets. Clause 12 dropped the constellation entirely.",
            "E2 APPLIED - psr_rate: spin period is 6.2185 ms (160.8 rev/s), not 1/6 s. "
            "Clause 9 now reads 'One turn takes six thousandths of a second' and the "
            "sketch's backwards '161ms/rev' now reads as 6.2 ms per rev; 161 is the "
            "frequency in Hz, not a period.",
            "E3 APPLIED - planet_masses: true masses are Draugr 0.020, Phobetor 3.9, "
            "Poltergeist 4.3 Earth masses. One is Moon-ish and two are ~4 Earths, not "
            "two Moon-ish and one heavy. Caption and disc radii (16/40/42) both fixed.",
            "E4 APPLIED - planet_periods: true periods are 25.262, 66.5419 and 98.2114 "
            "days, not 66/204/365. Banner, ring labels and clause 16 all fixed.",
            "E5 APPLIED - the how_1992 card is renamed how_1990. Pulsar discovered 9 Feb "
            "1990; first two planets announced January 1992, third later in 1992. The "
            "unsourced 'nobody believed him' beat is dropped, not reworded; clause 20 "
            "keeps the two-year wait, which is the 1990->1992 gap.",
            "E6 APPLIED - name_base_eight / name_punchline cards replaced by "
            "name_coordinates / name_just_digits. The base-eight joke was a fabrication "
            "attributed to Wolszczan and Frail and is gone. The replacement states the "
            "verifiable fact: PSR 1257+12 is a sexagesimal sky coordinate, 12h57m right "
            "ascension and plus 12 degrees declination.",
        ],
        "cards": cards,
    }
    with open(os.path.join(HERE, "round_1_card_schedule.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)

    with open(os.path.join(HERE, "cards.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["n", "id", "beat", "clauses", "start_s", "end_s", "dur_s", "words",
                    "caption", "banner", "accent", "value", "stick_h", "expression",
                    "pose", "motion", "sketch"])
        for c in cards:
            s = c["stickman"]
            w.writerow([c["n"], c["id"], c["beat"], "+".join(map(str, c["clauses"])),
                        c["start"], c["end"], c["duration"], c["words"],
                        c["caption"], c["banner"] or "", c["accent"], c["card_value"],
                        s["height"] if s else 0, s["expression"] if s else "",
                        s["pose"] if s else "", c["motion"], c["sketch"]])

    print("wrote round_1_card_schedule.json and cards.csv")
    print()
    for c in cards:
        s = c["stickman"]
        tag = f"{s['height']}px {s['expression']}/{s['pose']}" if s else "no stickman"
        print(f"{c['n']:>2} {c['id']:<20} {c['beat']:<16} "
              f"{c['start']:>6.2f}-{c['end']:>6.2f} ({c['duration']:>4.2f}s "
              f"{c['words']:>2}w) {c['accent']:<7}{tag}")


if __name__ == "__main__":
    main()

# work3/measure/STAGE_PLANS.md -- the 9-chapter stage grouping for the
# persistent-stage rebuild.
#
# WHY THIS FILE EXISTS
#   The readability defect was structural: every scene used `card(i, j, ...)`,
#   which paints ONE full frame and is live only for beat i..j-1, so a new
#   full-frame image appeared every ~2.4s and nothing survived between beats.
#   pinegap2_scene.py is the completed pilot (7 stages, motion on ~10 small
#   elements, text on 41% of beats). The other eight chapters need the same
#   conversion, and the beat->stage boundaries are a DIRECTORIAL judgment call
#   that should not be re-invented (or lost) per builder.
#
#   These boundaries were chosen from each chapter's beat arc: a stage is a run
#   of consecutive beats that share a SETTING, so the viewer can hold one
#   recognisable scene in their head while the art builds up inside it.
#
# HOW TO USE IT
#   Each builder is given its chapter's block below verbatim and told to use
#   exactly those boundaries. Within a stage the builder decides which old card
#   art accrues and which replaces -- that is the mechanical part.
#
# THE TWO RULES (from the pilot, both learned the hard way)
#   1. Accrue the WORLD, replace the LABELS. Scenery accumulates; anything
#      carrying text, and any two elements sharing the same region of the
#      frame, must REPLACE or they pile up.
#   2. Motion is RARE and it is on SMALL THINGS. ~8-12 moving elements per
#      chapter, each 0.45-0.6s, on small subjects only. The reference is 83%
#      still; large slow drifts read as image churn, not animation.

## pinegap (DONE -- the pilot)
A b01-03  B b04-09  C b10-16  D b17-21  E b22-27  F b28-30  G b31-34

## mezhgorye (30 beats)
A b01-05  mountain + frozen hills, location reveal
B b06-09  built in the 1930s, prisoners digging
C b10-12  hand drills, workers died, buried in rock
D b13-16  the tunnel network, 100km, chambers, power/water/housing
E b17-21  the stone fortress above, the rail line in
F b22-26  forgotten, closed on paper, rumours, mushroom cloud
G b27-30  the fortress still standing in snow, finale

## cheyenne (38 beats)
A b01-04  the mountain that is not a mountain; CMC reveal
B b05-09  granite, fifteen tunnels, fifteen buildings
C b10-16  steel springs, and the 700-ton door (the point of it)
D b17-21  cold interior, 200 people, its own power
E b22-25  self-sufficiency: no power line, springs, water tanks
F b26-29  the space defence centre, warning clocks
G b30-33  the painted concrete forest on the roof
H b34-38  nobody confirms; still staffed; the ninety percent figure

## room39 (37 beats)
A b01-06  under the Kremlin; Object 739; Stalin's own refuge
B b07-13  hardened steel; the doors made to close forever
C b14-16  Stalin never went in; lead-lined corridors
D b17-21  the control room and the one console
E b22-26  never filmed; an ordinary fence on an ordinary street
F b27-29  steel doors; rumour of a code
G b30-37  the system outlives its builder; the red light; finale

## svalbard (35 beats)
A b01-05  Arctic mountain; the tunnel down into the rock
B b06-10  the vault cut into permafrost; foil packets
C b11-17  a million samples; minus eighteen; the seeds sleep
D b18-21  the original plan was to shut the door
E b22-26  the 2016 flood; 800 tonnes; cut off for a year
F b27-30  the same permafrost thaws; watched year round; new tunnel
G b31-35  still a bunker against catastrophe; finale

## fortknox (44 beats)
A b01-07  the most secure building; Kentucky hills; a low brick building
B b08-13  looks like a school; it is not; work 1939-1944
C b14-16  Gothic roof; vaulted stone arches
D b17-25  the 56-ton door; steel/concrete/steel; walls thicker than doors
E b26-30  gold on nine floors; 12,000 tonnes; stacked to the ceiling
F b31-36  other nations' gold; national flags; only a few hundred tonnes left
G b37-41  the visitor counter; school trips; they walk above the gold
H b42-44  never below; inner doors bolted; finale

## tomb (45 beats)
A b01-05  eight thousand clay soldiers; the Terracotta Army title
B b06-10  six hundred horses; long rows; all guarding one man
C b11-16  Qin Shi Huang; first emperor; one script, one ruler
D b17-20  burned the books; the scholars; forced labour
E b21-25  the mound copied a pyramid; outside Xi'an; every soldier a
         different height, no two faces the same
F b26-31  vanished two thousand years; 1974 farmers; a clay shoulder;
         the hole covered over
G b32-37  2012 new pit; bronze cranes repaired with modern glue; the 1983
         acid attack, markings unreadable
H b38-42  mercury in the soil samples; enough to fill a pool; a slow poison
I b43-45  the main chamber never opened; still sealed; finale

## vatican (38 beats)
A b01-06  beneath Vatican City; the Archives; opened once in 1939, then closed
B b07-13  deep under the hill; shelves for kilometres; no electric light;
         no photography
C b14-18  fused pages; opening them tears them; most boxes stay shut
D b19-25  catalogued once then shelved; one index card is the whole record;
         filmed instead of opened
E b26-29  the shelving plan is filed upstairs; nobody has carried it down
F b30-34  a reader between tall shelves; access is a favour, not a right
G b35-38  a hand holding a small key; the lowest shelves; absolute dark

## area51 (34 beats)
A b01-04  a place with no name; Fifty-One; the most secret base
B b05-09  dry lake bed, Nevada; the Groom Lake sign; the arrest warning
C b10-14  the fence runs for miles; a second fence; cameras; the base is
         smaller than its fence
D b15-19  no aircraft may fly; red dashed line; pilots noticed first
E b20-25  Roswell; Hangar 18; that hangar is not officially there
F b26-30  Nellis runs the site; the budget is not public; Bob Lazar
G b31-34  2020 FBI files; the fence is still standing; finale
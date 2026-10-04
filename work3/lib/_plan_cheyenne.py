"""cheyenne plan -- 38 beats, ONE short sentence each.

THE RULE THIS FILE EXISTS TO ENFORCE. Every sentence in NARRATION is a single
self-contained declarative of at most 8 words, so the engine's phrase splitter
never has to cut a sentence mid-clause and no caption can read like a broken
fragment ("It is run jointly by the"). Short flat declaratives are also the
authentic Paint-Explainer read-aloud cadence -- hushed, dry, faintly ominous.

Two hard invariants, because the engine consumes this file silently:
  * len(NARRATION sentences) == len(BEATS) == 38, assigned 1:1 in order.
  * No sentence may contain an internal full stop. A decimal or an abbreviation
    would split into two captions and desync every beat after it. Numbers are
    spelled out for exactly this reason ("seven hundred tons", "ninety percent").

Verify after any edit:
  python -c "import io,re; s={}; exec(compile(io.open('lib/_plan_cheyenne.py',encoding='utf-8').read(),'p','exec'),s); sent=[p for p in re.split(r'(?<=[.!?])\\s+',s['NARRATION'].strip()) if p]; w=[len(re.findall(r\"[A-Za-z0-9']+\",x)) for x in sent]; print(len(sent),len(s['BEATS']),sum(w),max(w))"
"""

TITLE = "The Cheyenne Mountain Complex"

NARRATION = """Look at this mountain. It is not a mountain at all. It is a very large hiding place. This is the Cheyenne Mountain Complex. Work began there in the early sixties. The Cold War set the whole schedule. Granite sat under the entire site. Crews drilled out fifteen long tunnels. Fifteen separate buildings went in there. Each building rests on steel springs. The springs swallow the shock themselves. Then the mountain above does the rest. The entrance has one very large door. It weighs roughly seven hundred tons. It was built to seal completely. That door is the whole point of it. Inside the mountain, the air stays cold. The cold keeps the machines stable. Roughly two hundred people work down there. The complex runs on its own power. Diesel generators sit far below ground. No power line ever reaches the mountain. Water rises from springs in the rock. The tanks hold thousands of gallons daily. Nothing from outside reaches this place. This was the space defence centre. Satellites passed directly over the roof. Sensors in here watched for launches. The warning clocks started in this room. Outside, the mountain wears a painted forest. The trees are painted concrete slabs. They hide the ventilation towers behind them. From the air, nothing stands out at all. Now for the part nobody confirms. People say it still stays staffed. People say the government still goes down. They quote one number about survival. Ninety percent, though nobody has confirmed it."""

# One dict per intended beat, in order. Exactly 38, matching NARRATION's 38
# sentences. The cutter assigns narration spans to beats 1:1, in order.
BEATS = [
    {"beat": "HOOK", "visual": "one grey granite mountain filling the whole frame, hand-drawn flat painterly fills, washed-out sky; no buildings, no trees"},
    {"beat": "PIVOT", "visual": "same mountain, held still; a single faint scratch line appears across the rock face"},
    {"beat": "REVEAL", "visual": "rock face cut open in a wedge; character close-up, deadpan; speech bubble 'not a mountain'"},
    {"beat": "TITLE", "visual": "title 'CHEYENNE MOUNTAIN COMPLEX' stamped across the rock; small label 'COLORADO SPRINGS' with a state outline"},
    {"beat": "ESTABLISH", "visual": "period construction site on the hillside; stamp 'EARLY 1960s'; flat grey palette, cold light"},
    {"beat": "FACT", "visual": "simple hand-drawn globe with two superpowers facing off; a thin red line under the mountain"},
    {"beat": "IMAGE", "visual": "close cross-section of mottled pink granite; label 'SOLID GRANITE'; a drill silhouette boring into it"},
    {"beat": "FACT", "visual": "cutaway mountain with fifteen tunnel lines bored through it; big number '15'; character tiny beside them"},
    {"beat": "FACT", "visual": "fifteen blocky buildings stacked inside the cutaway; count ticking up"},
    {"beat": "FACT", "visual": "close on a building floor resting on a coiled steel spring"},
    {"beat": "FACT", "visual": "the spring squashing flat under a wide red shock arrow; label 'SWALLOWS THE SHOCK'"},
    {"beat": "PIVOT", "visual": "character shrugging under a heavy overhanging rock ceiling; speech bubble 'then what stops the rest?'"},
    {"beat": "ESCALATE", "visual": "steep mountain entrance, one small dark doorway; character tiny at the base, dwarfed"},
    {"beat": "FACT", "visual": "massive steel blast door in cross-section; big number '700 TONS'"},
    {"beat": "FACT", "visual": "the door swinging shut; seal lines closing around the frame; label 'SEALS COMPLETELY'"},
    {"beat": "REVEAL", "visual": "close on the sealed door, small in a huge dark frame; character awed, looking up"},
    {"beat": "ESTABLISH", "visual": "cutaway of the interior: a narrow chamber, a thermometer, breath in the air; label 'COLD'"},
    {"beat": "FACT", "visual": "bank of grey machines in the cold chamber, indicator lights steady"},
    {"beat": "FACT", "visual": "wide interior corridor with rows of coat hooks; small figures in coats; label 'ABOUT 200 STAFF'"},
    {"beat": "COMPARISON", "visual": "split frame: surface city skyline at left, diesel generators underground at right; a severed cable between them"},
    {"beat": "FACT", "visual": "diesel generator set deep underground, hand-drawn, with fuel drums stacked beside it"},
    {"beat": "PIVOT", "visual": "power line on the surface pylon row stopping dead in mid-air; character pointing at the break; speech bubble 'no line in'"},
    {"beat": "FACT", "visual": "water dripping from a granite crack into a pool underground"},
    {"beat": "FACT", "visual": "rows of water tanks under low ceiling light; label 'THOUSANDS OF GALLONS'"},
    {"beat": "PIVOT", "visual": "sealed interior, character alone, small; speech bubble 'nothing gets in'"},
    {"beat": "ESTABLISH", "visual": "Cold War era command room, long desks, warm lamp glow; title card 'SPACE DEFENCE CENTRE'"},
    {"beat": "FACT", "visual": "satellites arcing overhead above the mountain, beams crossing it"},
    {"beat": "FACT", "visual": "radar screen with a sweeping green line and blips; characters watching it"},
    {"beat": "ESCALATE", "visual": "a red arc climbing on the radar screen; room lights shift; the clock hand jumps"},
    {"beat": "REVEAL", "visual": "surface of the mountain from a low aircraft angle: a slope painted with flat concrete-grey tree shapes"},
    {"beat": "FACT", "visual": "close on a painted concrete tree shape, brush texture and drip marks; character awed, touching it"},
    {"beat": "IMAGE", "visual": "ventilation towers behind the fake trees, half-hidden, flat grey on grey"},
    {"beat": "FACT", "visual": "aerial view of the whole mountain, uniform and blank; character tiny on the crest"},
    {"beat": "PIVOT", "visual": "character hands-up, deadpan; speech bubble 'nobody confirms this part'"},
    {"beat": "FACT", "visual": "modern-day staff walking the corridor, coats, cold light; the room still in use"},
    {"beat": "FACT", "visual": "a line of plain cars on a highway; small black limousine at the end, no flags"},
    {"beat": "ESCALATE", "visual": "a hand-drawn number on a chalkboard: '90%'; a large question mark drawn beside it; a chalk line half-erased"},
    {"beat": "FINALE", "visual": "the sealed blast door closed, unlit frame, one cold light; nothing happens; held still to black"},
]

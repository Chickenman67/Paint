"""pinegap plan -- 32 beats, ONE short sentence each.

THE RULE THIS FILE EXISTS TO ENFORCE. Every beat's line is a single
self-contained sentence of at most ~8 words. That is what makes the
phrase-level caption reveal land on a DIGESTIBLE unit -- the phrase splitter
never has to cut mid-clause, so no caption ever reads like "It is run jointly
by the". Short declarative sentences ARE the Paint-Explainer read-aloud style
anyway; long ones are what force ugly fragment captions.

32 sentences x ~7 words ~ 226 words. At 165 wpm that is ~82s, matching the
reference's Pine Gap chapter duration tier. Keep NARRATION and BEATS at 32
sentences/beats -- _mkscript cuts them 1:1.
"""

TITLE = "Pine Gap - Australia's Most Secret Eavesdropping Station"

NARRATION = """Look at this place. There is nothing here. That is the point. It sits in central Australia. The desert runs out for miles. Then you see the white spheres. A whole cluster of them. They sit behind layers of wire. They look like ordinary buildings. They are not buildings. This is Pine Gap. It runs under a secret agreement. America and Australia share it. For decades the public was told nothing. They called it a space research facility. We now know what the white balls are. They are radomes. A radome is a protective cover. Inside each one sits a satellite dish. The cover hides the dish's exact angle. Nobody outside can tell who is watched. This is a top level listening post. It belongs to the Five Eyes group. Five Eyes shares the signal between nations. Spy satellites pass overhead every day. Their signals land at Pine Gap. The signals include phone calls. They include radio traffic. They include missile launch data. Getting close is nearly impossible. Airspace is locked to eighteen thousand feet. Armed guards walk the perimeter. Crossing the fence means seven years in prison. No one goes inside."""

# One dict per intended beat, in order. Exactly 34, matching NARRATION's 34
# sentences. The cutter assigns narration spans 1:1.
BEATS = [
 {"beat": "HOOK", "visual": "wide empty red desert, nothing on screen; label 'nothing here'"},
 {"beat": "PIVOT", "visual": "same empty desert, held"},
 {"beat": "REVEAL", "visual": "character close-up, deadpan; speech bubble 'nothing. on purpose'"},
 {"beat": "ESTABLISH", "visual": "map of Australia, a dot in the center"},
 {"beat": "IMAGE", "visual": "the desert horizon, empty, long"},
 {"beat": "IMAGE", "visual": "white sphere domes appear on the horizon, filling frame"},
 {"beat": "FACT", "visual": "dome cluster, wide, fence in foreground"},
 {"beat": "FACT", "visual": "wire fence layer, close"},
 {"beat": "REVEAL", "visual": "dome; label 'ordinary buildings'"},
 {"beat": "REVEAL", "visual": "dome; label 'not buildings'"},
 {"beat": "TITLE", "visual": "title 'PINE GAP'; two flags, US and Australia"},
 {"beat": "FACT", "visual": "two flags beside the domes"},
 {"beat": "FACT", "visual": "government building with a closed shutter over the door"},
 {"beat": "FACT", "visual": "closed shutter, close"},
 {"beat": "PIVOT", "visual": "character shrugging; speech bubble 'wait, what are they?'"},
 {"beat": "REVEAL", "visual": "close on one white sphere; label peels to 'RADOME'"},
 {"beat": "REVEAL", "visual": "the word 'RADOME' stamped over the sphere"},
 {"beat": "FACT", "visual": "radome cutaway label"},
 {"beat": "FACT", "visual": "cutaway: white cover lifts to reveal a dish inside"},
 {"beat": "FACT", "visual": "dish inside the lifted cover"},
 {"beat": "REVEAL", "visual": "arrow showing the angle hidden by the cover"},
 {"beat": "REVEAL", "visual": "character peeking from behind the cover; speech bubble 'looking at who?'"},
 {"beat": "ESCALATE", "visual": "globe with signal lines; number '1' badge"},
 {"beat": "ESCALATE", "visual": "five eye icons in a row, labeled 'FIVE EYES'"},
 {"beat": "ESCALATE", "visual": "globe with signal lines; nation links"},
 {"beat": "ESCALATE", "visual": "satellite overhead dropping beams"},
 {"beat": "ESCALATE", "visual": "signals landing at Pine Gap on a dish"},
 {"beat": "FACT", "visual": "icons: phone, radio"},
 {"beat": "ESCALATE", "visual": "icon: missile, red"},
 {"beat": "PIVOT", "visual": "character creeping toward the fence and stopping; speech bubble 'no further'"},
 {"beat": "FACT", "visual": "tall cylinder over the base; big number '18,000 ft'"},
 {"beat": "FACT", "visual": "drone with a red X over it, bounced back"},
 {"beat": "FACT", "visual": "perimeter fence with guard silhouettes and spotlights"},
 {"beat": "FINALE", "visual": "domes at night, dark; character awed; speech bubble 'we may never know'"},
]
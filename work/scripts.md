# Segment scripts (original narration, NOT derived from the reference)
# Target 190-213 wpm to match the reference pacing per CLAUDE.md §2.

# Segment 1: HD 188753 Ab (triple-star world)
# Target ~75-90s
HD_188753_SCRIPT = """Imagine a sky with three suns.

Not in a line, like a cosmic cliché. In a slow waltz. One yellow, one orange, one red, drifting across each other every few days, casting shadows that don't make sense.

That's HD 188753 Ab. A gas giant, roughly the mass of Jupiter, locked into a tight orbit around all three of them at once.

Discovered in 2005 by a team that included a scientist named Dr. Konacki, who basically said, and I'm quoting the spirit not the letter: this thing shouldn't be calm.

Three stars pull on a planet in three different directions at the same time. The orbit isn't a circle. It's a slow, wobbling, slightly drunk figure-eight. Sometimes the planet swings close to one star, then back out, then close to another.

We have no idea what its atmosphere does under that. We have no idea what its weather looks like.

We don't even know if it has weather.

It's the kind of place where a calendar would be a lie. Where "sunrise" is a meaningless word, because the light is always coming from somewhere, and the shadows are always lying.

And the planet just sits there. Three suns. Wobbling. Doing its impossible thing.

Nothing about it is calm."""

# Segment 2: HD 80606 b (the whiplash planet, +500°C swings)
# Target ~75-90s
HD_80606_SCRIPT = """Now imagine a planet that gets a fever every forty days.

HD 80606 b. A gas giant about four times the mass of Jupiter, on an orbit so stretched out it looks like someone drew it with a ruler and then bent the ruler.

Most of the time, it sits far from its star. Cold. Quiet. Average.

And then it swings in close. Very close. So close that the side facing the star gets hit with about eight hundred times more starlight than the side facing away.

In a few hours, the temperature on the dayside spikes by five hundred degrees Celsius.

Five hundred.

Then it swings back out, and the temperature crashes just as fast.

The atmosphere can't do anything reasonable with that. Models suggest winds on the order of several kilometers per second, supersonic shock waves, day-side temperatures hot enough to glow.

Every forty days, the same thing. The planet gets cooked, then frozen, then cooked again.

It is, as far as we can tell, the most violent routine in the galaxy.

A fever, on a loop. With no medicine, and no off switch."""


# Segment 3: PSR B1257+12 (pulsar planets)
# Word count: 317 (95.1s @ 200 wpm)
# Fact-corrected round 2: E1 Virgo not Vela, E2 6.2ms period, E3 0.020/3.9/4.3
# Earth masses, E4 periods 25/67/98 days, E5 1990 discovery / 1992 announcement,
# E6 base-eight joke removed (unsourced fabrication).
# Beat + card breakdown in work/segments/psrb1257/round_1_script.md
PSRB1257_SCRIPT = """Here is a star that has already died.
It is still spinning, and it is still talking.
And it is not spinning alone.
A neutron star.
City-sized.
Denser than anything should be allowed.
Its fuel ran out, it exploded, and the rest collapsed in here.
That collapse is what makes it spin. Fast.
One turn takes six thousandths of a second.
Beams of radio light rake out of its magnetic poles.
On and off and on. A lighthouse made of a dead star.
PSR B1257 plus twelve.
It has three planets.
One is barely heavier than the Moon. Two weigh four times the Earth.
That is not a solar system. That is rubble in a minefield.
Their laps take twenty-five days, sixty-seven, and ninety-eight.
So how do you find a planet around a corpse? You listen to the ticks.
Every rotation has a signature. Any wobble means something tugs.
Aleksander Wolszczan found that pulsar in 1990. It had a wobble in it.
He waited two years for it to come back. It came back.
A neutron star should not have a planet. It exploded. It is a grave.
But the wobble was steady, and rhythmic, and never stopped.
Something small was pulling on the beam, forever, on a schedule.
The first confirmed planets ever found around a dead star.
They named the planets after the things that haunt you.
Draugr. Phobetor. Poltergeist.
And they named the star PSR B1257 plus twelve.
The name is not a name. It is a spot in the sky, written in digits.
Twelve fifty-seven. Plus twelve. That is the entire name.
Here is the part that should bother you.
These did not form around a star that was burning.
They formed here, or they survived being made here.
The radiation on them now would take an atmosphere apart in an afternoon.
Three rocks and one collapsed core. Turning, forever, in the dark."""


def estimate_duration_s(text, wpm=200):
    """Estimate the audio duration in seconds given text and target wpm."""
    n_words = len(text.split())
    return (n_words / wpm) * 60.0

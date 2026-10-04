"""tres2b scene -- the first real v3 segment, end to end.

This is the integration that proves the whole restarted approach:
  audio3 (165wpm WAV) -> beats.json (exact beat boundaries)
  -> phrase_timing (contiguous 2-6 word phrases with start/end)
  -> engine3 (progressive timed-reveal compositor, 60fps)
  + character3 (stickman-with-a-face)
  + v2subjects/v2draw (flat vector primitives)

THE DESIGN RULE, straight from the user's brief and the reference measurement:
  "if its a big block of words or the word hasn't been said yet don't just put
   them all in on visual that spoils it ... sync the words/phrases with the
   narration so that each digestable phrase appears when the narrator speaks it."

So NOTHING full-sentence appears at once. Every caption is ONE phrase (2-6
words), revealed at that phrase's own start time. Visual elements arrive one at
a time, also at phrase onsets. The subject (planet) is on the frame from frame 0
and grows/reveals detail as the narration describes it -- it is never a spoiler.

Cadence discipline (measure/_cadence_compare.py): the reference is 66/8/26
still/motion/cut at 6fps -- still-heavy, changes by sharp cuts. So most beats
here are STILL with one cut per phrase. Continuous motion is reserved for two
accent moments: the star swelling toward the planet (beat 12) and the atmosphere
streaming off as a tail (beat 13). Do not add more sliding/orbiting.

Everything is deterministic: all seeds are constants, no wall clock. Rendering
this twice is byte-identical (see lib/_determinism_probe.py).

Run:  python lib/tres2b_scene.py            (writes segments/tres2b/frames + mp4)
      python lib/tres2b_scene.py --preview  (also dump a contact sheet)
"""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import engine3 as E3
import phrase_timing as PT
import character3 as C3

# v2 primitives live in work/lib; engine3 already puts it on sys.path.
import v2subjects as S
import v2draw as D

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.abspath(os.path.join(HERE, os.pardir, 'segments', 'tres2b'))
BEATS = os.path.join(SEG, 'beats.json')
TITLE = 'TRES-2b'

W, H = E3.W, E3.H

# --- palette (flat, page-white, ink; one accent per beat so adjacent reveals
#     don't read as one card with a glitch -- CLAUDE.md palette rule) ---------
INK = (24, 24, 28)
PAGE = (252, 252, 251)
RED = (198, 48, 40)        # heat / alarm
DULL = (168, 62, 44)       # the dull-red glow
GREY_LT = (208, 208, 210)
GREY_DK = (92, 92, 98)
DAY = (222, 176, 96)       # lit face
NIGHT = (38, 38, 44)       # dark face


def _caption(text, cx, cy, at, until=None, size=None, fill=None, max_w=None):
    """A phrase caption element: appears at `at`, LEAVES at `until`.

    THE `until` IS THE WHOLE POINT. The first pass of this file appended every
    phrase as a permanent element, so a beat with four phrases stacked four
    captions at the same y and they rendered as an unreadable black smear --
    which is exactly the "big block of words on the visual" failure the user
    called out. A caption must be on screen only while its phrase is being
    spoken. If `until` is omitted it defaults to the next phrase's start, so
    captions hand off cleanly instead of piling up.

    Uses v2draw.draw_label so the caption inherits the LOCKED type scale (and
    the black keyline that goes with every non-black label) instead of a
    hand-rolled text blit.
    """
    color = T.INK if fill is None else fill
    sz = size if size is not None else T.LABEL_PX
    max_w = max_w or 980
    # An INK caption must carry NO keyline. draw_label strokes every non-INK
    # label, and a 34px face with a 4px black stroke on both sides closes the
    # counters of every letter -- the first pass rendered "That is darker than
    # coal" as an illegible black smear for exactly this reason. Only COLOURED
    # captions get a keyline, and it is kept thin (2px) so it reads as a
    # marker-pen edge rather than a fill.
    outline = None if color == T.INK else T.INK
    stroke_w = 0 if color == T.INK else 2

    def draw(tile, fw, fh):
        f = T.load_font(sz, bold=True)
        probe = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        bb = probe.textbbox((0, 0), text, font=f, stroke_width=stroke_w)
        tw = bb[2] - bb[0]
        if tw > max_w:
            sz2 = max(14, int(sz * max_w / float(tw)))
            f = T.load_font(sz2, bold=True)
            bb = probe.textbbox((0, 0), text, font=f, stroke_width=stroke_w)
            tw = bb[2] - bb[0]
        # Pad by the STROKE. Measuring the fill advance and then compositing a
        # stroked draw into that box clips the outline -- memory:
        # hero-word-must-account-for-stroke.
        pad = stroke_w + 6
        w = int(tw) + pad * 2
        h = int(bb[3] - bb[1]) + pad * 2
        sub = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        D.draw_label(sub, text, color=color, size=sz, center=(w / 2, h / 2),
                     outline=outline, outline_w=stroke_w)
        tile.alpha_composite(sub, (int(cx - w / 2), int(cy - h / 2)))
    return E3.E('cap_%d_%s' % (int(at * 1000), text[:14]), 'text', draw,
                at=at, until=until)


def _label(text, cx, cy, at, until=None, size=None, fill=None):
    """A small diagram label (day/night, numbers)."""
    return _caption(text, cx, cy, at, until=until,
                    size=size or T.LABEL_SM_PX, fill=fill)


from PIL import Image, ImageDraw  # noqa: E402
import v2type as T  # noqa: E402


def _planet_center():
    # FRAME-FILL (round-2 critic finding #4, memory frame-fill-subject-scale): the
    # dominant subject must OWN the frame, not float in it. r=205 at y=320 left the
    # disc spanning only 57% of frame height with a dead band top and bottom -- a
    # timid prop. r=225 at y=320 spans y 95..545: 62% of the height, and the top
    # edge (95) still clears the title baseline (67). Wider geometry is the
    # caller's other job -- see the cropped secondary bodies below.
    return (W // 2, 320, 225)


def _closeup_char(draw, hx, hy, hr, expression, seed, shoulder=1.0):
    """A CROPPED-IN character close-up: one shoulder mass + the head.

    ROUND 5 -- extracted from the finale so it can be reused. Round 4 had exactly
    one close-up (the finale) and the round-4 critic found that all five of its
    losses were frames where our side was a diagram on an empty page while the
    bar's side was an expressive character close-up. So the capability the
    finale already proved has to be available to the MIDDLE of the segment too,
    not just the last 5 seconds.

    `shoulder` scales the shoulder mass (0 disables it).

    THE SHOULDER (round 5 follthrough). The finale's original shoulder was a
    wedge running from off-frame-left down to the bottom edge -- fine when the
    head is jammed into the LEFT edge, but as a shared helper for a head on the
    RIGHT it became a huge diagonal slab that covered a third of the frame AND
    the caption (the round-3 finale comment already warned that "a wedge
    spanning the frame reads as a black triangle rather than a person"). So the
    shoulder is rebuilt as a proper CLOSED BUST: a smooth arc that rises to a
    collar just under the jaw and falls away to the frame bottom on BOTH sides
    of the head, cropped by the bottom edge. It reads as the top of a torso
    directly below the head, which is what a cropped close-up shows, and it
    never sprawls sideways far enough to reach the caption.

    All our own drawing; C3.draw_head is character3's face routine, which is
    what makes the expression readable at size.
    """
    import v2paint as PA
    d = draw
    if shoulder > 0:
        # A closed shoulder/torso mass: a bowed top edge (the collar line) from
        # one side of the frame, up under the jaw, and back down the other side,
        # closed off along the bottom edge of the frame.
        jy = hy + hr * 0.92                     # roughly the jaw line
        w = hr * 1.55 * shoulder                # half-width of the torso mass
        cx0 = hx
        top = []
        n = 33
        for i in range(n + 1):
            u = i / float(n)
            x = cx0 - w + 2.0 * w * u
            # a smooth collar: high (near the jaw) at the centre under the chin,
            # falling away toward both ends
            t = (u - 0.5) * 2.0                # -1..1
            y = jy + hr * (0.30 * (t ** 2) + 0.10 * abs(t))
            top.append((x, y))
        bust = top + [(cx0 + w, 830), (cx0 - w, 830)]
        PA.fill_poly(d, bust, INK, seed=seed + 48, value=0.0, tint=0.0,
                     band=0.0, edge=0.0, grow=2)
        PA.hand_stroke(d, top, INK, max(5, int(hr * 0.05)), closed=False,
                       seed=seed + 49, wavelength=160.0, vary=0.30)
    C3.draw_head(d, hx, hy, hr, expression=expression, seed=seed,
                 lw=max(5, int(round(hr * 0.13))))


def build():
    with io.open(BEATS, encoding='utf-8') as f:
        meta = json.load(f)
    phrases = PT.all_phrases_timed(BEATS)

    # index phrases by beat for easy lookup: beat_id -> [(start, text), ...]
    by_beat = {}
    for ph in phrases:
        by_beat.setdefault(ph['beat_id'], []).append((ph['start'], ph['text']))

    def ph(bid, i):
        return by_beat[bid][i]

    # Beat end times come from beats.json, which records each beat's real
    # span. Do NOT derive them from the phrase list -- by_beat holds
    # (start, text) pairs, so there is no end time in it to read.
    bend = {b['id']: b.get('end', b.get('start', 0.0) + 1.0)
            for b in meta['beats']}

    def until_of(bid, i):
        """When the phrase at (bid, i) stops being on screen: the next phrase's
        start in the same beat, else the next beat's first phrase start, else
        the beat's own end. This is what keeps ONE caption on screen at a time
        and hands off to the next phrase cleanly."""
        lst = by_beat[bid]
        if i + 1 < len(lst):
            return lst[i + 1][0]
        # last phrase in the beat -> run until the next beat starts
        nxt = [p['start'] for p in phrases
               if p['start'] > bend[bid] - 1e-6]
        return min(nxt) if nxt else bend[bid]

    def cap(bid, i, cx, cy, **kw):
        """Add one phrase caption, revealed on its phrase and hidden on the
        next. THE central helper: every caption in the file goes through here
        so none of them can pile up."""
        start, text = ph(bid, i)
        return _caption(text, cx, cy, start, until=until_of(bid, i), **kw)

    px, py, pr = _planet_center()
    els = []

    # ---- persistent page background (at 0, never moves) --------------------
    def bg(tile, fw, fh):
        # PAINTERLY (round-2 critic finding #3): this was a single exact #fcfcfb
        # fill across all 921600 pixels -- a dead field with no tooth. The paper
        # tooth is applied HERE rather than in engine3 because engine3 owns the
        # blank page and must not be modified; the bg element is composited
        # first, so everything (art AND text) lands on top of the texture.
        import v2paint as PA
        ImageDraw.Draw(tile).rectangle([0, 0, fw, fh], fill=PAGE + (255,))
        PA.paper_overlay(tile, seed=99)
    els.append(E3.E('bg', 'bg', bg, at=0.0))

    # ---- BEAT 1: hook -- "Look at this planet. You will never see it." ------
    # The planet is here from the start (frame 0) but almost entirely BLACK --
    # only a thin lit rim. That IS the hook: you are looking at something you
    # cannot see. Do not fill it in; the narrator is about to say why.
    def planet_dark(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        # near-black disc
        S.planet(d, px, py, pr, fill=(28, 28, 33), seed=1, width=7)
        # A thin crescent of light on the upper-left edge only.
        # ROUND 3: this was `d.polygon([centre] + arc_points)` -- a pie wedge
        # with two exact straight radii, which on a dead-black disc read as a
        # flat yellow triangle pasted on the planet. It now goes through
        # v2subjects.crescent_light, which bows the inner boundary the same way
        # split_planet bows its terminator, so the segment's two "lit side"
        # devices look like one hand drew them.
        S.crescent_light(d, px, py, pr, 200, 255, (210, 168, 92), seed=1)
    els.append(E3.E('planet_dark', 'subject', planet_dark, at=0.0))

    els.append(cap('hook_never_see_it', 0, px, 560, size=40))
    els.append(cap('hook_never_see_it', 1, px, 560, size=40))
    els.append(cap('hook_never_see_it', 2, px, 620, size=34, fill=RED))

    # character reacts, cropped INTO the frame at the right (not placed on it)
    def char_skeptic(tile, fw, fh):
        C3.draw_character(tile, 1090, 720, 430, pose='standing',
                          expression='skeptic', seed=3)
    els.append(E3.E('char1', 'character', char_skeptic, at=ph('hook_never_see_it', 1)[0],
                    until=bend['hook_never_see_it']))

    # ---- BEAT 2: albedo -- "It bounces back less than one percent" ----------
    b2 = 'albedo_one_percent'
    def big_one_percent(tile, fw, fh):
        sub = Image.new('RGBA', (320, 200), (0, 0, 0, 0))
        D.draw_number(sub, '1%', center=(160, 100), color=T.RED, size=150)
        # shifted left: the planet grew to r=225, so its left edge is now x=415
        # and the old x=90..410 paste crowded it
        tile.alpha_composite(sub, (60, 180))
    els.append(E3.E('one_pct', 'text', big_one_percent, at=ph(b2, 0)[0], until=bend[b2]))
    els.append(cap(b2, 0, px, 600, size=30, max_w=760))
    els.append(cap(b2, 2, px, 600, size=30, max_w=760))

    # ---- BEAT 3: darker than coal / asphalt --------------------------------
    b3 = 'darker_than_coal'
    def swatches(tile, fw, fh):
        S.swatch(tile, 120, 470, 150, 110, (58, 58, 62), seed=5, label='coal')
        S.swatch(tile, 300, 470, 150, 110, (78, 78, 84), seed=6, label='asphalt')
    els.append(E3.E('swatches', 'shape', swatches, at=ph(b3, 0)[0], until=bend[b3]))
    els.append(cap(b3, 0, px, 600, size=30))
    els.append(cap(b3, 1, px, 600, size=30))

    # ROUND 5 -- CHARACTER PRESENCE, beat 3. This 7.5-second beat was two
    # swatches and a planet on an otherwise empty right half. The bar keeps its
    # character on screen nearly all the time; a diagram-only stretch is exactly
    # the shape that lost all five of round 4's pairs. A small deadpan pose
    # cropped by the RIGHT edge, revealed on its own phrase ("The instruments
    # checked it twice") so it arrives with the narration rather than at the
    # beat's top. cx=1120 keeps his whole gesture inside the frame -- the
    # pointing reach is cx+0.465*height = 1120+0.465*470 = 1339, PAST the
    # edge, so this pose is 'standing' (no outward reach) instead.
    def char3_deadpan(tile, fw, fh):
        C3.draw_character(tile, 1150, 720, 440, pose='standing',
                          expression='deadpan', seed=41)
    els.append(E3.E('char3', 'character', char3_deadpan, at=ph(b3, 2)[0],
                    until=bend[b3]))

    # ---- BEAT 4: tidally locked -- character close-up ----------------------
    # The most-emotionally-loaded beat. Per CLAUDE.md S10.8 the character must
    # carry this beat. Close-up, cropped into frame.
    b4 = 'tidally_locked_reveal'
    def char_closeup(tile, fw, fh):
        # Was 'peeking' at x=210, height 640: the pose throws both arms out
        # sideways, so at that scale his left hand fell off the frame edge and
        # read as a rendering error rather than a deliberate crop. 'pointing'
        # keeps the mass inboard and aims him AT the planet, which is what this
        # beat is about. Cropping is fine; cropping a hand mid-gesture is not
        # (memory: character-must-be-cropped-into-not-placed-on).
        #
        # ROUND 3 -- THE POINTING HAND NO LONGER STABS THE PLANET. He was drawn
        # at cx=300, height 600, which put the right hand-blob at x=579, y=267 --
        # 164px INSIDE the r=225 disc (left edge x=415). A hand buried in the
        # planet reads as a rendering error, not a gesture. The reach of
        # POSES['pointing'] is cx + 0.465*height horizontally (see the arm
        # geometry in character3._limb: L1=0.216h, L2=0.204h, right arm at
        # 78deg then 90deg, hand blob a further 0.035h), so cx=140/h=520 puts
        # the fingertip at x=382 and the blob's outer edge at x=400 -- a 15px
        # gap to the disc. He points AT the planet from outside it, and his other
        # hand stays clear of the LEFT frame edge too (at cx=140/h=520 the
        # trailing hand clipped the edge, which reads as a rendering error).
        # Verified by measuring the rendered alpha bbox, not by eye.
        C3.draw_character(tile, 155, 720, 500, pose='pointing',
                          expression='deadpan', seed=7)
    els.append(E3.E('char4', 'character', char_closeup, at=ph(b4, 0)[0], until=bend[b4]))
    els.append(cap(b4, 1, W // 2, 610, size=36))
    els.append(cap(b4, 2, W // 2, 610, size=36, fill=RED))
    els.append(cap(b4, 3, W // 2, 610, size=30))

    # ---- BEAT 5: two faces -- the split planet (the reveal) ----------------
    # The dark planet is REPLACED here by a clearly split day/night planet: this
    # is the visual "here's what I meant" moment. We fade the old planet out and
    # the split one in, timed to the phrases.
    b5 = 'two_faces_forever'
    def planet_split(tile, fw, fh):
        d = ImageDraw.Draw(tile)
        S.split_planet(d, px, py, pr, light_frac=0.5, light_dir=(-1, 0),
                       seed=9, width=7, day='day', night='night')
    els.append(E3.E('planet_split', 'subject', planet_split, at=ph(b5, 0)[0]))
    # hide the dark planet when the split one arrives (until= replaces it)
    for e in els:
        if e.id == 'planet_dark':
            e.until = ph(b5, 0)[0]

    # Labels sit OUTSIDE the disc. At r=205 they were at px+/-70, which is
    # inside the planet, so both were painted over by the sphere.
    #
    # ROUND 3 -- THESE TWO WERE SWAPPED. split_planet is called with
    # light_dir=(-1,0), so the LIT half is on the LEFT of the disc (see the
    # _rim(+1) arc: 90deg..270deg, i.e. x from cx down to cx-r), but "day" was
    # parked at px+pr+78 on the RIGHT and "night, always" at px-pr-92 on the
    # LEFT. Every rendered frame therefore labelled the dark face "day" and the
    # lit face "night, always" -- a factual error in the one beat whose whole
    # point is which side is which. Swapped to match the geometry.
    els.append(_label('day', px - pr - 78, py - 30, ph(b5, 0)[0],
                      until=bend[b5], size=24, fill=RED))
    els.append(_label('night, always', px + pr + 92, py + 40, ph(b5, 1)[0],
                      until=bend[b5], size=24, fill=(150, 150, 156)))
    els.append(cap(b5, 0, W // 2, 600, size=30))
    els.append(cap(b5, 1, W // 2, 600, size=30))

    # ROUND 5 -- a pose for the two-faces beat ("One half faces the star
    # forever. The other half never sees it at all."). This beat was a bare
    # split disc on an empty page with two small labels, which is the exact
    # diagram-on-nothing composition that lost five blind pairs in round 4, and
    # the tide-lock payoff is one of the segment's most loaded beats.
    # 'pointing' puts a real elbow in the right arm and aims it at the lit half,
    # which is what the line is about; 'confused' is the reaction that goes with
    # a world whose two halves never trade places.
    # cx=200, feet y=700, h=400 -> bbox roughly x 70..330, head top y~285.
    # Clear of the disc (left edge x=407), of the 'day' label (starts x~300 at
    # y=295), and of the caption (centred on 640, spans x~455..825). Measured,
    # not eyeballed -- see lib/_r5_char_measure.py.
    def char5_point(tile, fw, fh):
        C3.draw_character(tile, 200, 700, 400, pose='pointing',
                          expression='confused', seed=60)
    els.append(E3.E('char5', 'character', char5_point, at=ph(b5, 0)[0],
                    until=bend[b5]))

    # ---- BEAT 6: never warms / never cools -- gauges ------------------------
    b6 = 'never_warms_never_cools'
    def thermo(tile, fw, fh):
        # ROUND 5 -- the hot thermometer moved 1110 -> 900 and the character is
        # now a close-up cropped by the RIGHT edge. At x=1110 the glass ran
        # straight through where the close-up's head now sits. At 900 it sits in
        # the clear gap between the planet's right edge (865) and the
        # character's shoulder (starts ~942), so BOTH thermometers stay fully
        # readable -- which is the whole point of the beat (frozen night side vs
        # furnace day side). Verified on the rendered frame.
        S.thermometer(ImageDraw.Draw(tile), 170, 660, 190, 0.05, seed=11, hot=False)
        S.thermometer(ImageDraw.Draw(tile), 900, 660, 190, 0.95, seed=12, hot=True)
    els.append(E3.E('thermos', 'shape', thermo, at=ph(b6, 0)[0], until=bend[b6]))
    els.append(cap(b6, 0, W // 2, 620, size=32))
    els.append(cap(b6, 1, W // 2, 620, size=32, fill=RED))

    # ROUND 5 -- a cropped-in close-up for beat 6 ("The day side never cools").
    # One of the two beats the round-4 critic saw as an empty diagram page. The
    # expression is 'worried': the whole point of the beat is that NEITHER side
    # is ever comfortable, and a shrug at small scale could not carry that. Head
    # centre (1105, 340) r=175 -> both eyes fully in frame, head cropped by the
    # right edge. Narrow shoulder (0.60) so it clears the hot thermometer.
    def char6_worried(tile, fw, fh):
        _closeup_char(tile, 1105, 340, 175, 'worried', 61, shoulder=0.60)
    els.append(E3.E('char6', 'character', char6_worried, at=ph(b6, 1)[0],
                    until=bend[b6]))

    # ---- BEAT 7: day side furnace -------------------------------------------
    b7 = 'day_side_furnace'
    def furnace(tile, fw, fh):
        S.lava_planet(ImageDraw.Draw(tile), px, py, pr, seed=13)
    els.append(E3.E('furnace', 'subject', furnace, at=ph(b7, 0)[0],
                    until=bend[b7]))
    els.append(cap(b7, 0, W // 2, 600, size=34, fill=RED))

    # ROUND 5 -- a cropped-in close-up for beat 7 ("That day side is a
    # furnace"). The other beat the round-4 critic saw as an empty diagram page:
    # before this, the beat was a single lava disc and a caption. This is the
    # most shocked line in the segment and it now has a shocked face on it.
    # Head centre (185, 330) r=175 -> blob x -2..372, cropped by the LEFT edge,
    # clear of the lava planet (left edge x=415) and of the caption at 640.
    def char7_shock(tile, fw, fh):
        _closeup_char(tile, 185, 330, 175, 'shock', 62, shoulder=0.68)
    els.append(E3.E('char7', 'character', char7_shock, at=ph(b7, 0)[0],
                    until=bend[b7]))

    # ---- BEAT 8: dull red glow ----------------------------------------------
    b8 = 'dull_red_glow'
    def glow_num(tile, fw, fh):
        # Size the scratch tile from the MEASURED glyph, not a guess. At 110px
        # "2000 K" is 345px of advance plus an 11px keyline on each side, so the
        # old hardcoded 360px tile clipped ~4px off the right of the K.
        size = 110
        probe = ImageDraw.Draw(Image.new('RGB', (1, 1)))
        bb = probe.textbbox((0, 0), '2000 K',
                            font=T.load_font(size, bold=True),
                            stroke_width=max(3, int(size * 0.10)))
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        pad = 8
        sub = Image.new('RGBA', (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
        D.draw_number(sub, '2000 K', center=(sub.size[0] / 2, sub.size[1] / 2),
                      color=DULL, size=size)
        # LAYOUT COLLISION (round-2 critic finding #5). This used to paste at
        # (px-180, 560), i.e. centred under the planet at y 560..710 -- exactly
        # where the beat's caption sits (W//2, 640). "2000 K" and "Like coals
        # left in a hearth." rendered on top of each other and BOTH became
        # unreadable. The number is now a callout parked in the clear right-hand
        # shoulder (the disc ends at x=865, the caption is ~430px wide centred on
        # 640), so the hero number and the caption never share pixels. x=872 put
        # the glyph run's right edge at x=1255 -- inside the 1280 frame but with
        # only 25px of margin, which read as clipped. 838 leaves 60px.
        tile.alpha_composite(sub, (838, 470))
    els.append(E3.E('glow_num', 'text', glow_num, at=ph(b8, 2)[0], until=bend[b8]))
    els.append(cap(b8, 0, W // 2, 640, size=30))
    els.append(cap(b8, 3, W // 2, 640, size=28, fill=GREY_DK))

    # ROUND 5 -- a small pose for the dull-red-glow beat. Another long beat that
    # was planet + one number; the beat's whole subject is a faint ember glow,
    # and 'awed' is the reaction that goes with looking at something dim and
    # still being unable to see it. Small, cropped by the LEFT edge, low enough
    # to clear the planet (bottom y=545). Revealed on "It does glow, faintly."
    def char8_awed(tile, fw, fh):
        C3.draw_character(tile, 150, 720, 420, pose='peeking',
                          expression='awed', seed=63)
    els.append(E3.E('char8', 'character', char8_awed, at=ph(b8, 0)[0],
                    until=bend[b8]))

    # ---- BEAT 9: paradox -- character confused, shielded --------------------
    b9 = 'hot_but_too_dark'
    def char_confused(tile, fw, fh):
        # ROUND 3: was cx=1120, which put the shrug's right hand-blob at x=1284 --
        # past the 1280 frame edge, so the arm was visibly guillotined by the
        # border (measured: the rendered alpha bbox ran 916..1280, i.e. exactly
        # to the edge). cx=1080 puts the hand at 1244 and the blob's outer edge
        # at ~1260, so the whole gesture is inside the frame.
        C3.draw_character(tile, 1080, 720, 470, pose='shrug',
                          expression='confused', seed=17)
    els.append(E3.E('char9', 'character', char_confused, at=ph(b9, 0)[0], until=bend[b9]))
    els.append(cap(b9, 0, W // 2 - 120, 620, size=32, max_w=720))
    els.append(cap(b9, 1, W // 2 - 120, 620, size=32, fill=RED, max_w=720))

    # ---- BEAT 10-13: the star rises, swells, and eats the atmosphere --------
    # MOTION ACCENT #1 (beat 12) and #2 (beat 13). These two are the only
    # continuous motion in the segment; everything else is still-with-cuts.
    b12 = 'swelling_and_closer'
    b13 = 'atmosphere_as_tail'
    b14 = 'unmade_by_its_own_sun'

    def star_small(tile, fw, fh):
        # FRAME-FILL: r=60 was a tiny dot lost in the corner. r=92 reads as the
        # second subject it is, and it still clears the title (its spikes reach
        # y=150-92*1.55~7 ... so pull it down to y=170 to keep the rays off the
        # title strip; the swell in beat 12 carries it toward the planet anyway).
        S.star(ImageDraw.Draw(tile), 1075, 175, 92, seed=19)
    # star fades in at the pivot, then SWELLS toward the planet (motion accent)
    star_el = E3.E('star', 'subject', star_small, at=ph('watch_the_star', 0)[0],
                   motion=[(ph('watch_the_star', 0)[0], 0.0, 0.0, 1.0, 0.0),
                           (ph(b12, 0)[0], 0.0, 0.0, 1.0, 0.0),
                           (ph(b12, 1)[0], -180.0, 120.0, 1.6, 0.0)])
    els.append(star_el)

    els.append(cap('watch_the_star', 0, W // 2, 620, size=32))
    els.append(cap(b12, 0, W // 2, 620, size=32))
    els.append(cap(b12, 1, W // 2, 620, size=32))
    els.append(cap(b12, 2, W // 2, 620, size=32, fill=RED))

    # ROUND 5 -- a small pose across the 10-second stretch from "Now watch the
    # star" through "the fuel that keeps it alive", which round 4 left with a
    # star and captions and nothing else. He stands in the clear lower-right and
    # looks UP at the star with one arm raised toward it.
    #
    # cx=1150 put the waving hand-blob at x=1307 -- 27px PAST the right frame
    # edge, so the gesture was guillotined by the border, which reads as a
    # rendering fault rather than as a wave (memory:
    # character-must-be-cropped-into-not-placed-on; the finale comment makes the
    # same point about a hand cropped mid-gesture). The wave reach is
    # cx + sin(72)*0.216h + sin(38)*0.204h + hand = cx + 0.376h, so cx=1060 puts
    # the hand at 1222 with the blob's outer edge at ~1237 -- inside the frame.
    # His trailing hand lands at ~965, clear of the planet's right edge (865).
    def char10_look(tile, fw, fh):
        C3.draw_character(tile, 1060, 720, 430, pose='wave',
                          expression='skeptic', seed=64)
    els.append(E3.E('char10', 'character', char10_look,
                    at=ph('watch_the_star', 0)[0], until=ph(b12, 0)[0]))

    # ---- ROUND 5: WHERE THE PLUME LIVES ----------------------------------
    # The star's SETTLED disc position, derived from the star element's own
    # motion rather than hardcoded. The plume is anchored here (not at the
    # planet) because by beat 13 the star has swollen over the planet's right
    # limb and IS the body the gas is being torn off; anchoring the plume at the
    # planet (round 3/4) put a 300px gold lens straight across the star's disc.
    # See the ROUND 5 block in v2subjects.atmosphere_tail and the measured
    # before/after in lib/_r5_plume_measure.py.
    #
    # engine3 transforms an element about its own ink centroid, so the settled
    # centre is origin + tilesize/2 + final_offset. We read it off the element
    # itself (which also builds its tile) so this stays correct if the swell
    # keyframes are ever retuned.
    def _settled_star():
        tile, origin = star_el.tile_and_origin()
        _t, dx, dy, sc, _rot = star_el.motion[-1]
        cx = origin[0] + tile.size[0] / 2.0 + dx
        cy = origin[1] + tile.size[1] / 2.0 + dy
        return cx, cy, 92.0 * sc          # authored radius is 92 (star_small)
    star_cx, star_cy, star_r = _settled_star()

    # atmosphere tail streams off (motion accent #2)
    def tail(tile, fw, fh):
        # ROUND 5. Two changes from round 4, both about the plume's anchor:
        #   * it now starts AT THE STAR'S LIMB (anchor_frac=1.0) rather than
        #     0.68r inside whatever body it was attached to, and
        #   * clear_radius=0.98 hard-zeros any plume alpha inside the star's
        #     disc, so the star stays readable no matter how the falloff is
        #     tuned. Measured: plume coverage of the star's inner disc went from
        #     97.2% at alpha 1.0 to 0.00% (see _r5_plume_measure.py).
        # It streams RIGHT, away from the planet, so it crosses open page and
        # exits the frame edge rather than piling onto the disc.
        S.atmosphere_tail(ImageDraw.Draw(tile), star_cx, star_cy, star_r,
                          360, seed=21, width=6, spread=1.0, direction=(1, 0),
                          anchor_frac=1.0, clear_radius=0.98)
    els.append(E3.E('tail', 'subject', tail, at=ph(b13, 0)[0],
                    motion=[(ph(b13, 0)[0], -40.0, 0.0, 0.3, 0.0),
                            (ph(b13, 1)[0], 0.0, 0.0, 1.0, 0.0)]))
    els.append(cap(b13, 0, W // 2, 620, size=30))
    els.append(cap(b13, 1, W // 2, 660, size=28, fill=DULL))

    # ROUND 5 -- a pose for the swell + tail climax (beats 12 and 13: "So it is
    # swelling... it is pulling the air off the planet... trailing away as a long
    # glowing tail"). This was the segment's biggest hole: before this the last
    # character before the finale left at 59.87, so the entire ten-second
    # climax -- the swell AND the tail reveal, which is the segment's own payoff
    # shot -- played out over the art alone. The reference keeps a reaction on
    # its emotional beats; we had already established that pattern and then left
    # ten seconds of the most loaded lines in the segment bare.
    # 'handsup' (both arms up and out, real elbows) plus 'shock' is the reaction
    # that goes with watching a star swallow a planet's air. This replaced an
    # earlier 'recoil' here, whose 74/68 deg arm angles threw the left hand to
    # exactly x=0 -- a blob sliced by the border reads as a framing error rather
    # than a deliberate crop (see the char7/char14 crops, which take a real
    # slice). 'handsup' at 100 deg is more vertical and lands inside the frame.
    # cx=195, feet y=700, h=420 -> bbox roughly x 60..350, clear of the planet's
    # left edge (407), the star (starts ~690), and both captions (centred on
    # 640, left edge ~455). Verified by rendered frame and _r5_char_measure.py.
    def char11_recoil(tile, fw, fh):
        C3.draw_character(tile, 195, 700, 420, pose='handsup',
                          expression='shock', seed=65)
    els.append(E3.E('char11', 'character', char11_recoil,
                    at=ph(b12, 0)[0], until=ph('unmade_by_its_own_sun', 0)[0]))

    # ---- FINALE: planet fading, character awed ------------------------------
    # ROUND 3 -- THIS IS NOW A REAL CLOSE-UP, NOT A SMALL FULL-BODY FIGURE.
    # Round 2 shipped a full-body `recoil` at 500px tall standing beside a
    # 450px planet, so the character was set dressing: ~19% of frame height,
    # face about 5% of frame area. Round 2's own README even recorded that the
    # close-up capability "was NOT forced into every beat" and left the call to
    # the orchestrator; the round-2 critic named it as the second-biggest loss,
    # so it is applied here. The bar crops INTO the face on its emotional beats
    # and the character IS the subject; a small figure next to a big planet is
    # not that.
    #
    # Construction (all our own drawing; C3.draw_head is character3's face
    # routine, which is exactly what makes the expression readable at size):
    #   head radius 235 -> blob 502x442 px, i.e. 61% of frame HEIGHT
    #   head centre (255, 340) -> the blob's left edge lands at x=-13, so the
    #     head is CROPPED BY THE LEFT FRAME EDGE, not placed on the page, while
    #     both eyes stay fully in frame (an earlier pass at centre x=150 cut the
    #     left eye in half, which reads as a framing error rather than a crop)
    #   ONE shoulder mass enters from the bottom-left, cropped by both the left
    #     and bottom edges. It was originally a wedge spanning the full frame
    #     width from y=556, which filled the bottom third of the picture with
    #     flat black and read as a black triangle rather than a person. A single
    #     shoulder is what a cropped close-up actually shows, and it leaves the
    #     right two-thirds of the frame free for the planet, the star, the tail
    #     and the caption.
    # The caption moves to the clear lower-right so it never crosses the face,
    # the tail, or the shoulder.
    def char_awed(tile, fw, fh):
        _closeup_char(tile, 255, 340, 235, 'shock', 23)
    els.append(E3.E('char14', 'character', char_awed, at=ph(b14, 0)[0], until=bend[b14]))
    # The caption used to sit at (W//2, 620) -- dead centre, i.e. straight
    # through the face at this scale. Parked in the lower-right: clear of the
    # head (right edge x=523), clear of the shoulder (right edge x=374), below
    # the planet (bottom y=545) and below the tail (bottom y~414).
    els.append(cap(b14, 0, 860, 640, size=32, fill=RED))

    scene = E3.Scene(els, title=TITLE, title_seed=23, duration=meta['duration_s'])
    return scene


def render_preview(scene, path, n=8):
    from PIL import Image
    dur = scene.duration
    times = [dur * i / max(1, n - 1) for i in range(n)]
    tiles = [E3.render_frame(scene, t) for t in times]
    tw, th = 320, 180
    sheet = Image.new('RGB', (tw * 4, th * 2), (20, 20, 24))
    for i, t in enumerate(tiles):
        sheet.paste(t.resize((tw, th), Image.LANCZOS), ((i % 4) * tw, (i // 4) * th))
    sheet.save(path)
    print('preview -> %s' % path)


def render_video(scene, out):
    import subprocess
    d = os.path.dirname(out)
    os.makedirs(d, exist_ok=True)
    n = scene.frame_count()
    cmd = ['ffmpeg', '-y', '-v', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
           '-framerate', '60', '-i', '-',
           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', '60', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        fr = E3.render_frame(scene, i / 60.0)
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    print('video -> %s (%d frames, %.1fs)' % (out, n, scene.duration))


if __name__ == '__main__':
    sc = build()
    print('scene: %d elements, %.2fs, %d frames'
          % (len(sc.elements), sc.duration, sc.frame_count()))
    if '--preview' in sys.argv:
        render_preview(sc, os.path.join(SEG, '_preview_sheet.png'))
    if '--video' in sys.argv:
        render_video(sc, os.path.join(SEG, '_silent.mp4'))
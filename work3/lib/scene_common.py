"""Shared scene machinery, extracted from the proven tres2b scene.

WHY THIS FILE EXISTS. tres2b_scene.py was the first real scene and it carries
the whole template inline: the caption helper with its `until` handoff, the
cropped close-up character, the phrase-timed `cap()`, the build() plumbing and
the ffmpeg raw-video driver. Copying that ~200 lines into nine chapter scenes
would mean nine places to fix the "captions pile up" and "character reads as set
dressing" bugs, and CLAUDE.md is explicit that the type scale and character rules
must not drift between segments. So the invariants live here once and each
chapter file declares only its own cards.

THE INVARIANTS THIS LOCKS IN

1. CAPTIONS HAND OFF, THEY NEVER PILE UP. Every caption goes through `cap()`,
   which sets `until` to the next phrase's start. The first tres2b pass appended
   each phrase as a permanent element and four captions rendered at the same y,
   as an unreadable black smear -- exactly the "big block of words" defect the
   brief calls out. See `_caption`.

2. AN INK CAPTION CARRIES NO KEYLINE. v2draw.draw_label strokes every non-INK
   label, and a 34px face with a 4px black stroke closes the counters of every
   letter. Only COLOURED captions get a keyline, kept thin (2px).

3. STROKE-WIDTH PADDING. A stroked draw needs its box padded by the stroke; a
   fill advance measured alone clips the outline (memory:
   hero-word-must-account-for-stroke).

4. FRAME-FILL. `closeup()` and `subject_r()` are sized so the dominant subject
   owns the frame and is cropped BY a frame edge, not parked inside it (memory:
   frame-fill-subject-scale, character-must-be-cropped-into-not-placed-on).

5. DETERMINISM. No wall clock, no unseeded randomness. render_frame(scene, t) is
   a pure function of (scene, t); verified by _scene_determinism.py.

Per-chapter palettes differ; everything structural does not.
"""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFilter

import engine3 as E3
import phrase_timing as PT
import character3 as C3

# v2 primitives live in work/lib; engine3 already puts it on sys.path.
import v2paint as PA
import v2subjects as S
import v2draw as D
import v2type as T

W, H = E3.W, E3.H

# --- the locked type scale (CLAUDE.md STYLE_CANON §2) ------------------------
# Every chapter uses these and only these. Per-segment re-sizing was the type
# drift problem in the v2 build.
INK = (24, 24, 28)
PAGE = (252, 252, 251)


# ---------------------------------------------------------------------------
# caption
# ---------------------------------------------------------------------------

PAPER_KEY = (240, 236, 224)


def _draw_keylined(sub, text, color, sz, w, h, outline, stroke_w):
    """Draw a caption with a contrasting keyline UNDER the glyph fill.

    Only INK (dark) captions get the extra paper buffer: they ship with no
    outline of their own (invariant 2), so a subject keyline crossing behind
    one used to strike the words out. A light paper buffer fixes that.

    COLOURED captions already carry a dark keyline from invariant 2, and they
    are usually light text on a dark register -- adding a paper halo on top of
    that reads as a neon glow, which is worse than the collision. So the paper
    pass is skipped whenever the caption already has an outline.
    """
    f = T.load_font(sz, bold=True)
    if outline is None or not stroke_w:
        # INK caption: paper keyline first, then the dark glyphs on top
        D.draw_label(sub, text, color=PAPER_KEY, size=sz,
                     center=(w / 2.0, h / 2.0), outline=PAPER_KEY, outline_w=3)
        D.draw_label(sub, text, color=color, size=sz,
                     center=(w / 2.0, h / 2.0), outline=None, outline_w=0)
    else:
        # coloured caption: its own dark keyline is the contrast, nothing extra
        D.draw_label(sub, text, color=color, size=sz,
                     center=(w / 2.0, h / 2.0), outline=outline,
                     outline_w=stroke_w)


def caption(text, cx, cy, at, until=None, size=None, fill=None, max_w=None,
            halo=None):
    """One phrase caption: appears at `at`, LEAVES at `until`.

    `until` is the whole point (invariant 1). If omitted the caller should pass
    it -- cap() always does.

    `halo` is a numeric knockout strength (0 = off). It defaults to 1.0 for
    INK (dark) captions, which have no outline to protect them; pass 0 to
    disable, or a number to tune.
    """
    color = T.INK if fill is None else fill
    if halo is None and color == T.INK:
        halo = 1.0                                  # paper knockout
    halo_col = (238, 234, 222)
    sz = size if size is not None else T.LABEL_PX
    max_w = max_w or 980
    outline = None if color == T.INK else T.INK          # invariant 2
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
        pad = stroke_w + 8                                  # invariant 3 (+keyline)
        w = int(tw) + pad * 2
        h = int(bb[3] - bb[1]) + pad * 2
        sub = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        _draw_keylined(sub, text, color, sz, w, h, outline, stroke_w)
        # CLAMP into the frame. Every scene places captions by eye at a y like
        # 690 or 700, but a 49px-tall caption centred there ends at 724 or 744
        # -- the bottom third of the letters is sliced off by the frame edge,
        # which reads as a broken render, not as a design choice. Clamping here
        # rather than asking each scene to remember means a caption can never be
        # authored off-frame, and a caption authored that low slides up instead
        # of disappearing.
        pad_x, pad_y = 12, 8
        x = int(cx - w / 2)
        y = int(cy - h / 2)
        if x < pad_x:
            x = pad_x
        elif x + w > 1280 - pad_x:
            x = 1280 - pad_x - w
        if y < pad_y:
            y = pad_y
        elif y + h > 720 - pad_y:
            y = 720 - pad_y - h
        tile.alpha_composite(sub, (x, y))
    return E3.E('cap_%d_%s' % (int(at * 1000), text[:14]), 'text', draw,
                at=at, until=until)


def label(text, cx, cy, at, until=None, size=None, fill=None, max_w=None):
    """A small diagram label -- same rules, smaller default."""
    return caption(text, cx, cy, at, until=until,
                   size=size or T.LABEL_SM_PX, fill=fill, max_w=max_w)


# ---------------------------------------------------------------------------
# character
# ---------------------------------------------------------------------------

def closeup(draw, hx, hy, hr, expression, seed, shoulder=1.0):
    """A CROPPED-IN character close-up: one closed shoulder mass + the head.

    The round-4 critic found all five losses were frames where our side was a
    diagram on an empty page while the bar's side was an expressive close-up,
    so this capability has to be reachable from the MIDDLE of a chapter, not
    just the finale.

    The shoulder is a CLOSED BUST -- a bowed collar arc rising under the jaw
    and falling away to the frame bottom on BOTH sides -- not a wedge spanning
    the frame, which read as a black triangle rather than a person.
    """
    if shoulder > 0:
        jy = hy + hr * 0.92
        w = hr * 1.55 * shoulder
        top = []
        n = 33
        for i in range(n + 1):
            u = i / float(n)
            x = hx - w + 2.0 * w * u
            t = (u - 0.5) * 2.0
            y = jy + hr * (0.30 * (t ** 2) + 0.10 * abs(t))
            top.append((x, y))
        bust = top + [(hx + w, 830), (hx - w, 830)]
        PA.fill_poly(PA.img_of(draw), bust, INK, seed=seed + 48, value=0.0,
                     tint=0.0, band=0.0, edge=0.0, grow=2)
        PA.hand_stroke(draw, top, INK, max(5, int(hr * 0.05)), closed=False,
                       seed=seed + 49, wavelength=160.0, vary=0.30)
    C3.draw_head(PA.img_of(draw), hx, hy, hr, expression=expression,
                 seed=seed, lw=max(5, int(round(hr * 0.13))))


def fullbody(draw, x, feet_y, height, pose='standing', expression='neutral',
             seed=0):
    """A full-body character standing on `feet_y`, centred at x.

    character3's primitives take an Image (they open their own ImageDraw),
    while hand_stroke takes a Draw -- so this recovers the image rather than
    forwarding the draw the caller has.
    """
    C3.draw_character(PA.img_of(draw), x, feet_y, height, pose=pose,
                      expression=expression, seed=seed)


# ---------------------------------------------------------------------------
# painterly background
# ---------------------------------------------------------------------------

def paper_bg(seed=99):
    """Page-white + paper tooth. Composited first so art AND text sit on it."""
    def draw(tile, fw, fh):
        ImageDraw.Draw(tile).rectangle([0, 0, fw, fh], fill=PAGE + (255,))
        PA.paper_overlay(tile, seed=seed)
    return draw


def sky_bg(top, bottom, seed=7, hz_frac=0.62):
    """A two-tone painted ground/sky fill with paper tooth -- for exteriors.

    `top` is the sky, `bottom` the ground; the horizon sits at 62% height so
    subjects stand on it rather than floating.

    WHY THE SKY IS PAINTED FULL-HEIGHT FIRST. The first version filled sky as
    [0,0,fw,hz] and ground as [0,hz,fh] as two abutting rects. fill_rect's
    default `edge=EDGE` wobbles the boundary independently on each of them, so
    the two wobbled edges don't coincide and a pale seam snakes across the
    horizon -- it read as a rendering error, not paint. Painting the sky over
    the WHOLE frame first and then laying the ground on top (starting slightly
    above the nominal horizon) means any wobble is covered by the second fill
    and the horizon becomes the single wobbled edge it should be.
    """
    hz = int(H * hz_frac)

    def draw(tile, fw, fh):
        PA.fill_rect(tile, [0, 0, fw, fh], top, seed=seed, value=0.05)
        PA.fill_rect(tile, [0, hz - 6, fw, fh], bottom, seed=seed + 1, value=0.07)
        PA.paper_overlay(tile, seed=seed + 2)
    return draw


def night_bg(top, bottom, seed=7, hz_frac=0.62):
    """Night exterior -- same construction as sky_bg, for the finale beats."""
    return sky_bg(top, bottom, seed=seed, hz_frac=hz_frac)


# ---------------------------------------------------------------------------
# title backdrop
# ---------------------------------------------------------------------------

# The engine stamps scene.title LAST on every frame, and v2draw._wobble_glyph
# hardcodes fill=T.INK -- the title is always near-black and the engine cannot be
# changed for one chapter. On the paper register that is correct and crisp. On a
# NIGHT card it is invisible: the assembled film was shipping eight chapters
# whose titles could not be read, which no gate had caught because every gate
# reports on structure and this is a VALUE problem.
#
# This is vatican's `_lintel`, promoted to shared because it is the fix, not a
# chapter-specific flourish. Measured on the four eye-confirmed cases, a title on
# this backdrop reads at WCAG ~2.9 against the same title at ~1.15 on the raw
# night card -- the difference between "the most legible title in the film" and
# "I cannot read this".
#
# Call it FIRST in a card body, before any fill that would cover it, and keep it
# shallow (it stops at y=122) so the card's own in-art label has room at y=180.
TITLE_BACKDROP_SPAN = (10, 73)   # the part inside the title band, for the gate


def title_backdrop(tile, seed, col=(104, 92, 78), x0=0, x1=1280, dim=1.0):
    """A lit stone course at the head of a dark card, for the title to read on.

    ONE course across the band, uniform in value. Two overlapping courses were
    tried first (a full-value head course and a 0.55x course below it) because
    it reads more like cut stone, but the two values differ by ~45 levels -- far
    past the intrusion gate's DEV=25 -- so every band row failed the "uniform
    end to end" test that TITLE_BACKDROP relies on and the backdrop was reported
    as art striking through the title. The gate cannot tell a deliberate seam
    from a stroke, and it must not be loosened to try: the honest fix is a
    backdrop whose rows really are uniform. The masonry joints below supply the
    cut-stone read instead.

    `dim` scales the whole thing down for a finale, where the darkness is the
    subject and only a trace of the course may catch light.
    """
    def _c(k):
        return (int(col[0] * k * dim), int(col[1] * k * dim),
                int(col[2] * k * dim))

    d = ImageDraw.Draw(tile)
    # ONE uniform course covering the whole title band (y=0..86), with no value
    # change inside it. edge/value are low so the fill stays flat enough that
    # each row is uniform end to end.
    PA.fill_rect(tile, [x0, 0, x1, 86], _c(1.0), seed=seed, value=0.02, edge=1.0)
    # Masonry joints run BELOW the band only (band ends ~y=73). Run them up into
    # the band and they become dark verticals through the glyphs.
    x = x0 + 96
    k = 0
    while x < x1 - 40:
        PA.hand_stroke(d, [(x, 104), (x + 2, 122)], _c(0.52), 3, closed=False,
                       seed=seed + 10 + k, wavelength=70.0)
        x += 118
        k += 1


# ---------------------------------------------------------------------------
# build() plumbing
# ---------------------------------------------------------------------------

class BeatClock(object):
    """Phrase- and beat-timed lookups over a segment's beats.json.

    This is the object that makes the brief's core requirement mechanical: a
    caption appears at ITS phrase's word onset, not at the segment start and not
    at a predicted time. Word timings come from the synthesized WAV, so there is
    nothing to drift.
    """

    def __init__(self, beats_path):
        with io.open(beats_path, encoding='utf-8') as f:
            self.meta = json.load(f)
        phrases = PT.all_phrases_timed(beats_path)
        self.by_beat = {}
        for ph in phrases:
            self.by_beat.setdefault(ph['beat_id'], []).append(
                (ph['start'], ph['text']))
        self.bend = {b['id']: b.get('end', b.get('start', 0.0) + 1.0)
                     for b in self.meta['beats']}
        self.phrases = phrases
        self.duration = self.meta['duration_s']

    def n(self, bid):
        return len(self.by_beat[bid])

    def ph(self, bid, i):
        """(start, text) of phrase i in beat bid."""
        return self.by_beat[bid][i]

    def at(self, bid, i=0):
        return self.by_beat[bid][i][0]

    def until_of(self, bid, i):
        """When phrase (bid, i) leaves: the next phrase in the beat, else the
        next beat's first phrase start, else the beat's own end."""
        lst = self.by_beat[bid]
        if i + 1 < len(lst):
            return lst[i + 1][0]
        nxt = [p['start'] for p in self.phrases
               if p['start'] > self.bend[bid] - 1e-6]
        return min(nxt) if nxt else self.bend[bid]

    def bend_of(self, bid):
        return self.bend[bid]


def finish(els, title, clock, title_seed=0):
    """Wrap elements into a Scene with the real duration."""
    return E3.Scene(els, title=title, title_seed=title_seed,
                    duration=clock.duration)


# ---------------------------------------------------------------------------
# render drivers
# ---------------------------------------------------------------------------

def render_preview(scene, path, n=8):
    tw, th = 320, 180
    sheet = Image.new('RGB', (tw * 4, th * 2), (20, 20, 24))
    for i in range(n):
        t = scene.duration * i / max(1, n - 1)
        sheet.paste(E3.render_frame(scene, t).resize((tw, th), Image.LANCZOS),
                    ((i % 4) * tw, (i // 4) * th))
    sheet.save(path)
    print('preview -> %s' % path)


def render_video(scene, out, fps=60):
    import subprocess
    os.makedirs(os.path.dirname(out), exist_ok=True)
    n = scene.frame_count()
    cmd = ['ffmpeg', '-y', '-v', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
           '-framerate', str(fps), '-i', '-',
           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-r', str(fps), out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import time
    t0 = time.time()
    for i in range(n):
        p.stdin.write(E3.render_frame(scene, i / float(fps)).tobytes())
        # Progress heartbeat every ~5s so a background run is observable from the
        # output file. Without it a 6-hour render is an opaque PID.
        if (i + 1) % 300 == 0:
            el = time.time() - t0
            rate = (i + 1) / el
            eta = (n - i - 1) / rate if rate else 0
            print('    %d/%d frames  %.1f fps  elapsed %.1f min  ETA %.1f min'
                  % (i + 1, n, rate, el / 60.0, eta / 60.0), flush=True)
    p.stdin.close()
    p.wait()
    print('video -> %s (%d frames, %.1fs, %.1f fps overall)'
          % (out, n, scene.duration, n / max(1e-6, time.time() - t0)),
          flush=True)


def mux(seg_dir, fps=60):
    """Mux _silent.mp4 + audio.wav -> segment.mp4.

    RE-ENCODE BOTH STREAMS' AUDIO. CLAUDE.md §9.2: `-c copy` on audio is wrong
    -- every input's audio starts at PTS 0 and is not rebased onto a running
    timeline, so the assembled audio timestamps come out wrong while nb_frames
    still reads correct. Copy video only.
    """
    import subprocess
    silent = os.path.join(seg_dir, '_silent.mp4')
    wav = os.path.join(seg_dir, 'audio.wav')
    out = os.path.join(seg_dir, 'segment.mp4')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', silent, '-i', wav,
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-ar', '44100', '-ac', '2', '-shortest', out],
                   check=True)
    # Verify both streams separately: format=duration reports only the longest.
    def dur(stream):
        r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', stream,
                            '-show_entries', 'stream=duration',
                            '-of', 'default=nw=1:nk=1', out],
                           capture_output=True, text=True)
        try:
            return float(r.stdout.strip())
        except ValueError:
            return -1.0
    v, a = dur('v'), dur('a')
    print('muxed -> %s  video %.3fs  audio %.3fs  %s'
          % (out, v, a, 'OK' if abs(v - a) < 0.35 else 'DESYNC'))
    return out
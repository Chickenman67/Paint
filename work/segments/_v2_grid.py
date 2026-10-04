# _v2_grid.py -- one contact sheet of the WHOLE v2 film.
#
# Reviewing beats one PNG at a time does not work: the defects that matter most
# in this project are CROSS-BEAT (the same subject at the same size in every
# beat reads as a slideshow of one sticker; type scale drifting; a card that is
# mostly empty). Those are invisible in a single frame and obvious in a grid.
#
#   python _v2_grid.py --video <mp4> --out grid.png --cols 6 --rows 5
#
# Samples on a normalized fraction of the runtime, so it works on any length.

import argparse
import os
import subprocess

from PIL import Image, ImageDraw

TW, TH = 320, 180          # thumb size
LAB = 18


def dur_of(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=nw=1:nk=1', path],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cols', type=int, default=6)
    ap.add_argument('--rows', type=int, default=5)
    a = ap.parse_args()

    d = dur_of(a.video)
    n = a.cols * a.rows
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = os.path.join(os.path.dirname(os.path.abspath(a.out)), '_gridtmp')
    os.makedirs(tmp, exist_ok=True)

    sheet = Image.new('RGB', (a.cols * (TW + 6) + 6, a.rows * (TH + LAB + 6) + 6),
                      (18, 18, 22))
    dr = ImageDraw.Draw(sheet)
    for i in range(n):
        frac = (i + 0.5) / n
        t = frac * d
        p = os.path.join(tmp, 'g%02d.png' % i)
        if not os.path.exists(p):
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', a.video,
                            '-ss', '%.2f' % t, '-frames:v', '1', p], check=True)
        im = Image.open(p).convert('RGB').resize((TW, TH), Image.LANCZOS)
        cx, cy = 6 + (i % a.cols) * (TW + 6), 6 + (i // a.cols) * (TH + LAB + 6)
        sheet.paste(im, (cx, cy))
        dr.text((cx + 3, cy + TH + 3), '%5.1fs' % t, fill=(210, 210, 210))
    sheet.save(a.out)
    print('%s  %dx%d  from %s (%.1fs)' % (a.out, sheet.width, sheet.height,
                                         os.path.basename(a.video), d))


if __name__ == '__main__':
    main()

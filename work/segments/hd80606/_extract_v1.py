import subprocess, os
times = [2, 8, 14, 20, 28, 36, 44, 52, 60]
out_dir = 'C:/Users/david/.claude/jobs/9aa8631b/tmp'
os.makedirs(out_dir, exist_ok=True)
for t in times:
    tc = min(t, 40)
    outp = out_dir + '/r2_seg2_v1_t' + str(t) + '.png'
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{tc:.2f}', '-i', 'round_2.mp4', '-frames:v', '1', outp]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print('FAIL', t, r.stderr.strip()[:200])
    else:
        print('ok', t, '->', outp)

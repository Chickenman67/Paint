import subprocess, os
out_dir = 'C:/Users/david/.claude/jobs/9aa8631b/tmp'
# Late timestamps — clamp to 39.5s (last meaningful frame)
for t in [44, 52, 60]:
    tc = 39.5
    outp = out_dir + '/r2_seg2_v1_t' + str(t) + '.png'
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{tc:.2f}', '-i', 'round_2.mp4', '-frames:v', '1', outp]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(t, '->', r.returncode, r.stderr.strip()[:200] if r.returncode else 'ok', outp)

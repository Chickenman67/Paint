#!/usr/bin/env bash
# One chapter per process. The all-in-one run was killed by the harness at
# ~1800/4193 frames of pinegap (memory pressure); a fresh process per chapter
# releases everything between them. Logs per chapter, and the whole thing is
# resumable -- re-running skips chapters whose segment.mp4 already exists.
cd "$(dirname "$0")" || exit 1
for ch in area51 tomb room39 mezhgorye cheyenne svalbard fortknox vatican; do
  echo "=== $ch  $(date -u +%H:%M:%S) ==="
  python _build_segments.py "$ch" > "_build_${ch}.log" 2>&1
  echo "   exit=$? -- $(tail -1 "_build_${ch}.log")"
done
echo "=== ALL DONE $(date -u +%H:%M:%S) ==="

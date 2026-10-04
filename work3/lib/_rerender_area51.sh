#!/usr/bin/env bash
# area51's log was truncated when I killed that stray process during the
# whack-a-mole cleanup, so its segment.mp4 is stale (pre-title-fix). Re-render
# it alone, AFTER the sequential driver (PID passed in $1) finishes, so we never
# run two render processes at once. Uses 'tasklist' PID polling, which works on
# Windows -- pgrep does not.
cd "$(dirname "$0")" || exit 1
DRIVER_PID="$1"
while tasklist //FI "PID eq ${DRIVER_PID}" 2>/dev/null | grep -q "${DRIVER_PID}"; do
  sleep 6
done
echo "driver ${DRIVER_PID} finished -- starting area51 re-render"
python _build_segments.py area51 > _build_area51_rerender.log 2>&1
echo "area51 exit=$? -- $(tail -1 _build_area51_rerender.log)"

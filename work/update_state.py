# work/update_state.py — Helper to append log entries to progress/state.json
# Used by the orchestrator to track live activity.

import json
import os
import time

STATE_PATH = 'progress/state.json'


def append_log(msg, state=None):
    if state is None:
        try:
            with open(STATE_PATH) as f:
                state = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            state = {}
    if 'log' not in state:
        state['log'] = []
    state['log'].append({'t': time.strftime('%H:%M:%S'), 'msg': msg})
    # Keep last 100 entries
    state['log'] = state['log'][-100:]
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)
    return state


def set_segment(seg_id, **kwargs):
    """Update a segment's state in progress/state.json."""
    try:
        with open(STATE_PATH) as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}
    if 'segments' not in state:
        state['segments'] = {}
    if seg_id not in state['segments']:
        state['segments'][seg_id] = {}
    state['segments'][seg_id].update(kwargs)
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)
    return state


if __name__ == '__main__':
    import sys
    msg = ' '.join(sys.argv[1:])
    append_log(msg)
    print(f"Logged: {msg}")

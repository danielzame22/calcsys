# storage.py — persistencia JSON
import json, os
from datetime import date, timedelta

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')


def _load():
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)


def today():
    return date.today().isoformat()


def yesterday():
    return (date.today() - timedelta(days=1)).isoformat()


# ── STREAK ──────────────────────────────────────────────
def get_streak():
    d = _load()
    streak = d.get('streak', 0)
    last = d.get('last_completed', '')
    # reset if more than 1 day gap
    if last and last != today() and last != yesterday():
        streak = 0
        d['streak'] = 0
        _save(d)
    return streak, last


def record_completion():
    """Returns new streak count. Only counts if not already recorded today."""
    d = _load()
    streak = d.get('streak', 0)
    last = d.get('last_completed', '')
    if last == today():
        return streak  # already counted
    if last == yesterday():
        streak += 1
    else:
        streak = 1
    d['streak'] = streak
    d['last_completed'] = today()
    _save(d)
    return streak


# ── SUDOKU PROGRESS ──────────────────────────────────────
def get_sudoku_progress():
    d = _load()
    return d.get('sudoku_' + today(), None)


def save_sudoku_progress(board, completed=False):
    d = _load()
    d['sudoku_' + today()] = {'board': board, 'completed': completed}
    _save(d)


# ── SOLVER HISTORY ───────────────────────────────────────
def get_history():
    return _load().get('history', [])


def add_history(q, a):
    d = _load()
    h = d.get('history', [])
    h.insert(0, {'q': q, 'a': a})
    d['history'] = h[:20]
    _save(d)

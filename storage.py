import json
import os
import tempfile
from typing import List, Dict, Any

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "actions.json")


def load_actions(path: str | None = None) -> List[Dict[str, Any]]:
    """Load list of action dicts from JSON file. Returns empty list if file missing or invalid."""
    p = path or DEFAULT_PATH
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def save_actions(actions: List[Dict[str, Any]], path: str | None = None) -> None:
    """Atomically save actions (list of dicts) to JSON file."""
    p = path or DEFAULT_PATH
    d = os.path.dirname(p)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    # atomic write
    fd, tmp = tempfile.mkstemp(dir=d or ".", prefix=".tmp_actions_", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(actions, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass
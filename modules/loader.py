# modules/loader.py
import json
from pathlib import Path

def load_config(path="config.json"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{path} not found")
    return json.loads(p.read_text(encoding="utf-8"))

def load_processed(path="processed.json"):
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except:
        return {}

def save_processed(data, path="processed.json"):
    p = Path(path)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)


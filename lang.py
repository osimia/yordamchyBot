import json
from pathlib import Path

LANG_CACHE = {}

def get_text(lang: str, key: str) -> str:
    if lang not in LANG_CACHE:
        path = Path("locales") / f"{lang}.json"
        with open(path, encoding="utf-8") as f:
            LANG_CACHE[lang] = json.load(f)
    return LANG_CACHE[lang].get(key, f"[{key}]")

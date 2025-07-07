# src/utils/user_storage.py

import json
from pathlib import Path

STORAGE_FILE = Path("user_data.json")

def load_user_ids() -> set[int]:
    if STORAGE_FILE.exists():
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data)
        except Exception:
            return set()
    return set()

def save_user_ids(user_ids: set[int]):
    try:
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(list(user_ids), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения user_id: {e}")

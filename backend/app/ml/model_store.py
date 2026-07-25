"""Pickle-based persistence for trained ML artifacts (models, encoders,
metrics) under app/ml/model_store/."""
from __future__ import annotations

import pickle
from pathlib import Path

STORE_DIR = Path(__file__).parent / "model_store"
STORE_DIR.mkdir(parents=True, exist_ok=True)


def save(name: str, obj) -> Path:
    path = STORE_DIR / f"{name}.pkl"
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    return path


def load(name: str):
    path = STORE_DIR / f"{name}.pkl"
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def exists(name: str) -> bool:
    return (STORE_DIR / f"{name}.pkl").exists()

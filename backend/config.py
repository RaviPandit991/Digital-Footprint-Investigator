"""Local configuration and API key storage."""
import json
import os
from pathlib import Path

CONFIG_DIR = Path(__file__).parent / "data"
CONFIG_DIR.mkdir(exist_ok=True)
KEYS_FILE = CONFIG_DIR / "api_keys.json"

DEFAULT_KEYS = {
    "hibp":       "",  # HaveIBeenPwned
    "shodan":     "",
    "virustotal": "",
    "hunter":     "",  # hunter.io
    "abuseipdb":  "",
    "google_cse": "",  # Google Custom Search
    "google_cx":  "",  # Google Custom Search Engine ID
    "tineye":     "",
}


def load_keys() -> dict:
    if not KEYS_FILE.exists():
        save_keys(DEFAULT_KEYS)
        return DEFAULT_KEYS.copy()
    try:
        with open(KEYS_FILE) as f:
            data = json.load(f)
        # Fill any missing defaults
        for k, v in DEFAULT_KEYS.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return DEFAULT_KEYS.copy()


def save_keys(keys: dict) -> None:
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)


def get_key(name: str) -> str:
    return load_keys().get(name, "")


def update_key(name: str, value: str) -> None:
    keys = load_keys()
    keys[name] = value
    save_keys(keys)

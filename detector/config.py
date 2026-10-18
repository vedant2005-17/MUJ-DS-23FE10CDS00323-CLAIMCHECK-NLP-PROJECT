"""Loads config.yaml once and exposes it as a plain dict."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_config(path="config.yaml"):
    with open(ROOT / path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_text(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")

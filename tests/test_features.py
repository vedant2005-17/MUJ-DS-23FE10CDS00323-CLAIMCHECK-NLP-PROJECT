import json

from detector.analyzer import verdict_for
from detector.config import load_config
from detector.features import extract_features, heuristic_score
from detector.llm_client import parse_json

cfg = load_config()

FAKE = ("SHOCKING!!! Sources say the government is hiding the TRUTH. "
        "You won't believe what happens next, share before it gets banned!")
REAL = ("The city council approved the 2026 budget on Tuesday by a vote of 7 to 2. "
        "Council member Rao said the plan funds road repairs and two new libraries.")


def test_fake_text_scores_higher_than_real():
    fake = heuristic_score(extract_features(FAKE, cfg), cfg)
    real = heuristic_score(extract_features(REAL, cfg), cfg)
    assert fake > real


def test_features_detect_phrases():
    f = extract_features(FAKE, cfg)
    assert "you won't believe" in f["clickbait_found"]
    assert f["exclamations"] == 4


def test_parse_json_handles_code_fences():
    raw = "```json\n" + json.dumps({"fake_score": 140, "red_flags": ["a"]}) + "\n```"
    out = parse_json(raw)
    assert out["fake_score"] == 100  # clamped


def test_verdict_bands():
    bands = cfg["scoring"]["bands"]
    assert verdict_for(10, bands) == "Likely reliable"
    assert verdict_for(90, bands) == "Likely fake"

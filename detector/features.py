"""Classic NLP features computed without any model.

These give a quick, explainable 'style suspicion' score that is blended
with the LLM's judgement in analyzer.py.
"""
import re
from collections import Counter

STOPWORDS = set("""a an the and or but if of to in on at by for with from as is are was were be been
it its this that these those he she they we you i his her their our your not no so than then
there which who whom what when where will would can could should has have had do does did
about into over after before more most also said says""".split())

WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\-]*")
SENT_RE = re.compile(r"[.!?]+(?:\s|$)")


def tokenize(text):
    return WORD_RE.findall(text)


def count_phrases(text_lower, phrases):
    """Return the phrases from `phrases` that appear in the text."""
    return [p for p in phrases if p in text_lower]


def extract_features(text, cfg):
    lex = cfg["lexicons"]
    tokens = tokenize(text)
    lower_tokens = [t.lower() for t in tokens]
    text_lower = text.lower()

    sentences = [s for s in SENT_RE.split(text) if s.strip()]
    n_words = len(tokens)
    n_sent = max(len(sentences), 1)

    # Words written fully in capitals (ignore 1-2 letter words like "US", "TV")
    caps = [t for t in tokens if t.isupper() and len(t) > 2]

    keywords = Counter(t for t in lower_tokens if t not in STOPWORDS and len(t) > 3)

    sensational = sorted({w for w in lower_tokens if w in set(lex["sensational_words"])})
    clickbait = count_phrases(text_lower, lex["clickbait_phrases"])
    vague = count_phrases(text_lower, lex["vague_sourcing"])

    return {
        "word_count": n_words,
        "sentence_count": n_sent,
        "avg_sentence_len": round(n_words / n_sent, 1),
        "lexical_diversity": round(len(set(lower_tokens)) / n_words, 2) if n_words else 0,
        "exclamations": text.count("!"),
        "all_caps_ratio": round(len(caps) / n_words, 3) if n_words else 0,
        "second_person_ratio": round(
            sum(t in ("you", "your", "you're") for t in lower_tokens) / n_words, 3
        ) if n_words else 0,
        "sensational_found": sensational,
        "clickbait_found": clickbait,
        "vague_found": vague,
        "top_keywords": [w for w, _ in keywords.most_common(6)],
    }


def heuristic_score(features, cfg):
    """Weighted sum of style signals, each capped, clipped to 0-100."""
    w = cfg["heuristics"]["weights"]
    cap = cfg["heuristics"]["caps"]

    parts = {
        "sensational_words": len(features["sensational_found"]) * w["sensational_words"],
        "clickbait_phrases": len(features["clickbait_found"]) * w["clickbait_phrases"],
        "vague_sourcing": len(features["vague_found"]) * w["vague_sourcing"],
        "exclamations": features["exclamations"] * w["exclamations"],
        "all_caps_ratio": features["all_caps_ratio"] * w["all_caps_ratio"],
        "second_person_ratio": features["second_person_ratio"] * w["second_person_ratio"],
    }
    total = sum(min(v, cap[k]) for k, v in parts.items())
    return round(min(total, 100))

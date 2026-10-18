"""Pipeline: features -> LLM -> blended score -> verdict."""
from .features import extract_features, heuristic_score


def verdict_for(score, bands):
    for upper, label in bands:
        if score <= upper:
            return label
    return bands[-1][1]


class Analyzer:
    def __init__(self, cfg, llm):
        self.cfg = cfg
        self.llm = llm

    def analyze(self, text):
        features = extract_features(text, self.cfg)
        h_score = heuristic_score(features, self.cfg)
        llm_out = self.llm.ask(text, features)

        weight = self.cfg["scoring"]["llm_weight"]
        final = round(weight * llm_out["fake_score"] + (1 - weight) * h_score)

        return {
            "score": final,
            "verdict": verdict_for(final, self.cfg["scoring"]["bands"]),
            "llm_score": llm_out["fake_score"],
            "heuristic_score": h_score,
            "verifiable": llm_out["verifiable"],
            "summary": llm_out["summary"],
            "reasoning": llm_out["reasoning"],
            "red_flags": llm_out["red_flags"],
            "claims_to_verify": llm_out["claims_to_verify"],
            "features": features,
        }

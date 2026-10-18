# Claimcheck: Fake News / Misinformation Detector

A small Flask web app that estimates how likely a piece of text is to be misinformation.
It combines two things:

1. **Classic NLP features** (`detector/features.py`): tokenization, sentence splitting, stop-word
   filtering, keyword frequency, and lexicon matching for sensational words, clickbait phrases and
   vague sourcing. These produce a transparent 0-100 "style suspicion" score.
2. **An LLM call** (`detector/llm_client.py`): the Google Gemini API (free tier; Anthropic is also
   supported) reads the text, lists red flags and claims worth verifying, and returns a 0-100 score
   as JSON. The prompt lives in `prompts/`.

The web page marks the loaded wording and vague sourcing directly in your text, so the score is easy
to explain. The final score is a weighted blend (`scoring.llm_weight` in `config.yaml`, default 0.75
LLM / 0.25 statistics).

## Project layout

```
app.py                  Flask routes
config.yaml             provider, model, limits, scoring weights, lexicons
prompts/                system_prompt.txt, user_prompt.txt
detector/features.py    NLP feature extraction + heuristic score
detector/llm_client.py  API call, JSON parsing, error handling
detector/analyzer.py    pipeline: features -> LLM -> blended verdict
templates/, static/     web UI
tests/                  pytest unit tests (no API key needed)
```

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then put your GEMINI_API_KEY in .env
                                 # free key: https://aistudio.google.com/apikey
python app.py                    # open http://127.0.0.1:5000
pytest                           # run the tests
```

## Design notes

- The LLM is asked for strict JSON; `parse_json` strips code fences and clamps the score so a
  badly formatted reply cannot crash the app.
- Temperature is 0.2 so repeated checks of the same text give similar scores.
- The model cannot browse the web. The prompt tells it to say when a claim needs an outside
  source, and the UI lists such claims under "Claims worth verifying".
- All tunable values (provider, model, weights, word lists, score bands) are in `config.yaml`.

## Limitations

This is a classroom project, not a fact-checking service. It judges writing style and internal
plausibility, and it can be wrong on breaking news or niche topics.

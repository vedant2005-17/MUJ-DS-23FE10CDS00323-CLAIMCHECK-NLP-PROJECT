import logging

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from detector.analyzer import Analyzer
from detector.config import load_config
from detector.llm_client import LLMClient, LLMError

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

cfg = load_config()
app = Flask(__name__)
_analyzer = None


def get_analyzer():
    """Create the analyzer lazily so the page still loads without an API key."""
    global _analyzer
    if _analyzer is None:
        _analyzer = Analyzer(cfg, LLMClient(cfg))
    return _analyzer


@app.get("/")
def index():
    return render_template("index.html", max_chars=cfg["app"]["max_input_chars"])


@app.post("/api/analyze")
def analyze():
    text = (request.get_json(silent=True) or {}).get("text", "").strip()

    if len(text.split()) < cfg["app"]["min_input_words"]:
        return jsonify(error=f"Please paste at least {cfg['app']['min_input_words']} words."), 400
    if len(text) > cfg["app"]["max_input_chars"]:
        return jsonify(error=f"Text is too long (limit {cfg['app']['max_input_chars']} characters)."), 400

    try:
        return jsonify(get_analyzer().analyze(text))
    except LLMError as exc:
        return jsonify(error=str(exc)), 502


if __name__ == "__main__":
    app.run(port=cfg["app"]["port"], debug=True)

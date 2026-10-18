"""Thin wrapper around the LLM API.

Everything provider-specific lives in this file. The provider and model
are chosen in config.yaml ("gemini" is free, "anthropic" is paid).
"""
import json
import logging
import os
import re

from .config import read_text

log = logging.getLogger(__name__)

KEY_NAMES = {"gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self, cfg):
        self.cfg = cfg["llm"]
        self.provider = self.cfg["provider"]
        if self.provider not in KEY_NAMES:
            raise LLMError(f"Unknown provider '{self.provider}' in config.yaml.")

        key_name = KEY_NAMES[self.provider]
        key = os.getenv(key_name)
        if not key:
            raise LLMError(f"{key_name} is not set. Copy .env.example to .env and add your key.")

        self.system_prompt = read_text(self.cfg["system_prompt_file"])
        self.user_template = read_text(self.cfg["user_prompt_file"])

        if self.provider == "gemini":
            from google import genai
            from google.genai import types
            self._types = types
            self.client = genai.Client(
                api_key=key,
                http_options=types.HttpOptions(timeout=self.cfg["timeout_seconds"] * 1000),
            )
        else:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=key,
                timeout=self.cfg["timeout_seconds"],
                max_retries=self.cfg["max_retries"],
            )

    def _build_user_message(self, article, features):
        return self.user_template.format(
            article=article,
            word_count=features["word_count"],
            avg_sentence_len=features["avg_sentence_len"],
            exclamations=features["exclamations"],
            all_caps_ratio=features["all_caps_ratio"],
            sensational_found=", ".join(features["sensational_found"]) or "none",
            clickbait_found=", ".join(features["clickbait_found"]) or "none",
            vague_found=", ".join(features["vague_found"]) or "none",
        )

    def _call_gemini(self, user_msg):
        t = self._types
        resp = self.client.models.generate_content(
            model=self.cfg["model"],
            contents=user_msg,
            config=t.GenerateContentConfig(
                system_instruction=self.system_prompt,
                temperature=self.cfg["temperature"],
                max_output_tokens=self.cfg["max_tokens"],
                response_mime_type="application/json",
            ),
        )
        return resp.text or ""

    def _call_anthropic(self, user_msg):
        resp = self.client.messages.create(
            model=self.cfg["model"],
            max_tokens=self.cfg["max_tokens"],
            temperature=self.cfg["temperature"],
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )
        return "".join(b.text for b in resp.content if b.type == "text")

    def ask(self, article, features):
        user_msg = self._build_user_message(article, features)
        call = self._call_gemini if self.provider == "gemini" else self._call_anthropic
        try:
            raw = call(user_msg)
        except Exception as exc:  # network, quota, bad key, wrong model name
            log.error("%s API error: %s", self.provider, exc)
            raise LLMError("The language model could not be reached. Check your API key, "
                           "model name and internet, then try again.") from exc
        return parse_json(raw)


def parse_json(raw):
    """Models sometimes wrap JSON in code fences; strip them and parse."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise LLMError("The model returned an unreadable answer.")
    try:
        data = json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError("The model returned an unreadable answer.") from exc

    data["fake_score"] = max(0, min(100, int(data.get("fake_score", 50))))
    for key in ("red_flags", "claims_to_verify"):
        data[key] = [str(x) for x in data.get(key, [])][:5]
    data.setdefault("summary", "")
    data.setdefault("reasoning", "")
    data["verifiable"] = bool(data.get("verifiable", True))
    return data

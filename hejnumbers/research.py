"""Thema wählen, recherchieren und unabhängig prüfen – mit Claude und Websuche."""
import json
import os
import re
import requests

API = "https://api.anthropic.com/v1/messages"


def ask_claude(model, system, prompt, max_searches=8, max_tokens=4000):
    r = requests.post(
        API,
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
            "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": max_searches}],
        },
        timeout=600,
    )
    r.raise_for_status()
    text = "\n".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text")
    return parse_json(text)


def parse_json(text):
    text = text.replace("```json", "").replace("```", "")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("Keine JSON-Antwort von Claude:\n" + text[:500])
    return json.loads(m.group(0))


RESEARCH_SYSTEM = """You research content for @hejnumbers, an Instagram/TikTok/LinkedIn account that posts one "Top 4" statistic per day in English.
Rules:
- Use web search. Every one of the 4 values must be confirmed by at least 2 independent, reputable sources (official bodies, encyclopedias, scientific institutions, major statistical offices). Prefer recent data.
- Choose rankings where reputable sources agree on the order. Avoid topics where the ranking is disputed or depends heavily on definitions.
- Avoid politics, religion, violence, health advice and anything that could hurt or offend.
- The fun fact must also be confirmed by 2 sources.
- Units: ALWAYS metric (m, km, km², kg, t, °C, km/h). Never feet, miles, inches, pounds or °F.
- Every value must make clear what it is. Either the value carries its unit ("828 m", "6,650 km", "1.42 B people")
  or, for years, counts or rankings without a unit, the subtitle says what the number means ("Year founded", "Number of moons").
- The subtitle is always filled: a short line under the title that names the measure and unit, e.g. "Height in metres",
  "Area in km²", "Year founded", "Population in billions".
- Approximate values: write "~1096" (no "c.", no "about").
- Labels max 22 characters, values max 10 characters.
- Answer ONLY with JSON, no other text."""

RESEARCH_PROMPT = """Category for today: {category}
Topics already used (do NOT repeat or closely repeat): {history}

Return JSON:
{{
  "topic": "short internal topic name",
  "title": "Post title, max 40 characters, e.g. 'Longest rivers'",
  "subtitle": "What the numbers mean, with unit, max 32 characters, e.g. 'Year founded' or 'Height in metres'",
  "hook": "Short hook for slide 1, e.g. 'Can you guess #1?'",
  "items": [
    {{"label": "...", "value": "...", "number": 0.0, "sources": ["url1", "url2"]}},
    ... exactly 4 items, rank 1 first ...
  ],
  "fact": "One surprising fact, max 110 characters",
  "fact_sources": ["url1", "url2"],
  "source": "Short source name for the footer, e.g. 'NASA' or 'UN'",
  "captions": {{
    "instagram": "Caption with a hook line, a question for comments, source line and 6 hashtags incl. #top4 #hejnumbers",
    "tiktok": "Short caption with a question and 4 hashtags incl. #hejnumbers",
    "linkedin": "Factual caption, 2-3 short sentences, a question, source line, 3 hashtags"
  }}
}}
"number" is the plain numeric value used for bar lengths."""

VERIFY_SYSTEM = """You are a strict, independent fact-checker. Use web search yourself; do not trust the sources given.
A post may only pass if all 4 values, the ranking order and the fun fact are correct and supported by at least 2 reputable sources each.
Small rounding differences are fine. Answer ONLY with JSON."""

VERIFY_PROMPT = """Check this post:
{post}

Return JSON:
{{"verdict": "ok" or "reject", "problems": ["..."]}}"""


def research(model, category, history):
    return ask_claude(model, RESEARCH_SYSTEM,
                      RESEARCH_PROMPT.format(category=category, history=", ".join(history[-120:]) or "none"),
                      max_searches=10)


def verify(model, post):
    slim = {k: post[k] for k in ("title", "items", "fact", "fact_sources")}
    return ask_claude(model, VERIFY_SYSTEM, VERIFY_PROMPT.format(post=json.dumps(slim, ensure_ascii=False, indent=1)),
                      max_searches=10, max_tokens=2000)


def valid_shape(post):
    try:
        assert len(post["items"]) == 4
        for it in post["items"]:
            float(it["number"])
            assert it["label"] and it["value"]
            assert len(it.get("sources", [])) >= 2
        assert len(post.get("fact_sources", [])) >= 2
        assert post["title"] and post["fact"] and post["source"] and post.get("subtitle")
        for k in ("instagram", "tiktok", "linkedin"):
            assert post["captions"][k]
        return True
    except (KeyError, AssertionError, TypeError, ValueError):
        return False

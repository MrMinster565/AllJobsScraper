"""Score jobs against the user's free-text criteria.

Two scorers with the same interface:
  - KeywordMatcher: free, local, no setup. Hebrew-aware (strips one-letter prefixes like ה/ב/ל).
  - ClaudeMatcher:  used automatically when ANTHROPIC_API_KEY is set. Understands "roughly a match".
"""
from __future__ import annotations

import json
import re
from typing import Iterable

from .config import anthropic_key
from .models import Job, Match

_NIQQUD = re.compile(r"[֑-ׇ]")
_TOKEN = re.compile(r"[א-תa-zA-Z0-9+#]+")
_HE_PREFIXES = "והבלמכש"
_STOPWORDS = {
    "אני", "מחפש", "מחפשת", "עבודה", "משרה", "משרות", "תפקיד", "של", "עם", "או", "את", "על", "אל",
    "זה", "גם", "לא", "כל", "יש", "רוצה", "בתחום", "באזור", "ניסיון", "שנות", "שנים", "ב", "ל",
    "the", "a", "an", "and", "or", "in", "for", "of", "with", "job", "jobs", "looking",
}


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(_NIQQUD.sub("", text.lower()))


def _variants(token: str) -> set[str]:
    """The token plus Hebrew forms with up to two leading prefix letters removed."""
    out = {token}
    t = token
    for _ in range(2):
        if len(t) >= 3 and t[0] in _HE_PREFIXES:
            t = t[1:]
            out.add(t)
    return out


def _terms(text: str) -> list[str]:
    seen: list[str] = []
    for tok in _tokens(text):
        if tok in _STOPWORDS or len(tok) < 2:
            continue
        base = min(_variants(tok), key=len) if re.match(r"[א-ת]", tok) else tok
        if base not in seen:
            seen.append(base)
    return seen


class KeywordMatcher:
    STRONG_WEIGHT = 3

    def score(self, jobs: Iterable[Job], criteria: str) -> list[Match]:
        terms = _terms(criteria)
        results = []
        for job in jobs:
            if not terms:
                results.append(Match(job, 0, "לא הוזנו קריטריונים"))
                continue
            # Words in the title or location field count more than words buried in the description.
            title_words = {v for tok in _tokens(f"{job.title} {job.location}") for v in _variants(tok)}
            body_words = {v for tok in _tokens(job.text()) for v in _variants(tok)}
            total = got = 0
            hits: list[str] = []
            for term in terms:
                total += self.STRONG_WEIGHT
                if term in title_words:
                    got += self.STRONG_WEIGHT
                    hits.append(term)
                elif term in body_words:
                    got += 1
                    hits.append(term)
            score = round(100 * got / total)
            results.append(Match(job, score, "נמצאו: " + ", ".join(hits) if hits else "אין התאמה"))
        return sorted(results, key=lambda m: m.score, reverse=True)


_SYSTEM = (
    "You rank job ads for a job seeker. The seeker writes criteria in Hebrew (or English). "
    "For each job give an integer score 0-100 for how well it fits (a rough fit is still useful: "
    "50+ means worth a look), and a one-line reason in Hebrew. Judge location, role type and "
    "stated requirements. Output only the JSON object requested."
)
_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "score": {"type": "integer"},
                    "reason": {"type": "string"},
                },
                "required": ["id", "score", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


class ClaudeMatcher:
    MODEL = "claude-haiku-4-5"

    def __init__(self, api_key: str | None = None, batch_size: int = 10, max_chars: int = 3000):
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key)
        self.batch_size = batch_size
        self.max_chars = max_chars
        self.input_tokens = 0
        self.output_tokens = 0

    def score(self, jobs: Iterable[Job], criteria: str) -> list[Match]:
        jobs = list(jobs)
        matches: list[Match] = []
        for i in range(0, len(jobs), self.batch_size):
            matches.extend(self._score_batch(jobs[i : i + self.batch_size], criteria))
        return sorted(matches, key=lambda m: m.score, reverse=True)

    def _score_batch(self, batch: list[Job], criteria: str) -> list[Match]:
        ads = "\n\n".join(f"<job id=\"{j.id}\">\n{j.text()[: self.max_chars]}\n</job>" for j in batch)
        resp = self.client.messages.create(
            model=self.MODEL,
            max_tokens=2000,
            system=_SYSTEM,
            messages=[{"role": "user", "content": f"<criteria>\n{criteria}\n</criteria>\n\n{ads}"}],
            output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
        )
        self.input_tokens += resp.usage.input_tokens
        self.output_tokens += resp.usage.output_tokens
        text = next((b.text for b in resp.content if b.type == "text"), "{}")
        by_id = {r["id"]: r for r in json.loads(text).get("results", [])}
        out = []
        for job in batch:
            r = by_id.get(job.id)
            if r is None:  # model skipped a job: fall back to the local scorer for it
                out.extend(KeywordMatcher().score([job], criteria))
            else:
                out.append(Match(job, max(0, min(100, r["score"])), r["reason"]))
        return out

    def cost_usd(self) -> float:
        """Haiku 4.5 list price: $1 / MTok input, $5 / MTok output."""
        return self.input_tokens / 1e6 * 1.0 + self.output_tokens / 1e6 * 5.0


def get_matcher():
    key = anthropic_key()
    return ClaudeMatcher(key) if key else KeywordMatcher()

from alljobs.matcher import KeywordMatcher
from alljobs.models import Job


def job(i, title, desc="", location=""):
    return Job(id=str(i), title=title, description=desc, location=location)


def test_ranks_relevant_first_and_handles_hebrew_prefixes():
    jobs = [
        job(1, "נהג חלוקה", "משאית, אזור הצפון", "חיפה"),
        job(2, "מפתח/ת Python", "פיתוח בצד שרת, ניסיון בענן", "תל אביב"),
        job(3, "מזכירה רפואית", "קליניקה", "ירושלים"),
    ]
    ranked = KeywordMatcher().score(jobs, "מחפש עבודה בתחום הפיתוח, Python, בתל אביב")
    assert ranked[0].job.id == "2"
    assert ranked[0].score > ranked[-1].score


def test_empty_criteria_scores_zero():
    ranked = KeywordMatcher().score([job(1, "x")], "")
    assert ranked[0].score == 0


def test_location_prefix_matches_bare_city():
    ranked = KeywordMatcher().score([job(1, "מזכירה", "", "תל אביב")], "בתל אביב")
    assert ranked[0].score >= 50


def test_claude_matcher_parses_response_and_falls_back_when_job_skipped():
    import json
    from types import SimpleNamespace

    from alljobs.matcher import ClaudeMatcher

    reply = {"results": [{"id": "1", "score": 120, "reason": "מתאים"}]}  # score gets clamped
    fake = SimpleNamespace(
        usage=SimpleNamespace(input_tokens=1000, output_tokens=50),
        content=[SimpleNamespace(type="text", text=json.dumps(reply))],
    )
    m = ClaudeMatcher.__new__(ClaudeMatcher)
    m.batch_size, m.max_chars, m.input_tokens, m.output_tokens = 10, 3000, 0, 0
    m.client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: fake))

    ranked = m.score([job(1, "מפתח Python"), job(2, "נהג")], "Python")
    assert ranked[0].job.id == "1" and ranked[0].score == 100
    assert {r.job.id for r in ranked} == {"1", "2"}  # job 2 was skipped by the model -> local fallback
    assert abs(m.cost_usd() - (0.001 + 0.00025)) < 1e-9

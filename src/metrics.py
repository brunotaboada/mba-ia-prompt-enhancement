import json
import re
from typing import Dict, Optional


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def tone_score(text: str) -> float:
    positive_markers = [
        "clear",
        "measurable",
        "when",
        "then",
        "given",
        "claro",
        "mensuravel",
        "quando",
        "entao",
        "dado",
    ]
    penalties = ["maybe", "probably", "etc", "todo", "fix soon", "talvez", "provavelmente"]
    score = 0.75
    score += 0.05 * sum(marker in text.lower() for marker in positive_markers)
    score -= 0.1 * sum(marker in text.lower() for marker in penalties)
    return _clamp(score)


def acceptance_criteria_score(text: str) -> float:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    ac_lines = [line for line in lines if line.startswith("-") or line.startswith("*")]
    if not ac_lines:
        return 0.0

    gwt_lines = [
        line
        for line in ac_lines
        if any(token in line.lower() for token in ["given", "when", "then", "dado", "quando", "entao"])
    ]
    coverage = len(gwt_lines) / max(1, len(ac_lines))
    volume = min(len(ac_lines) / 4.0, 1.0)
    return _clamp((coverage * 0.7) + (volume * 0.3))


def user_story_format_score(text: str) -> float:
    pattern_en = re.compile(
        r"as\s+a[n]?\s+.+?,\s*i\s+want\s+.+?,\s*so\s+that\s+.+",
        re.IGNORECASE | re.DOTALL,
    )
    pattern_pt = re.compile(
        r"como\s+.+?,\s*eu\s+quero\s+.+?,\s*para\s+.+",
        re.IGNORECASE | re.DOTALL,
    )
    return 1.0 if (pattern_en.search(text) or pattern_pt.search(text)) else 0.0


def completeness_score(text: str) -> float:
    lowered = text.lower()
    checks = [
        ("as a" in lowered) or ("como" in lowered),
        ("i want" in lowered) or ("eu quero" in lowered),
        ("so that" in lowered) or ("para" in lowered),
        ("acceptance criteria" in lowered) or ("criterios de aceite" in lowered),
    ]
    return _clamp(sum(1 for check in checks if check) / len(checks))


def evaluate_output(text: str) -> Dict[str, float]:
    return {
        "tone_score": round(tone_score(text), 4),
        "acceptance_criteria_score": round(acceptance_criteria_score(text), 4),
        "user_story_format_score": round(user_story_format_score(text), 4),
        "completeness_score": round(completeness_score(text), 4),
    }


def _parse_score_payload(raw_text: str) -> Optional[Dict[str, float]]:
    # Supports models that may wrap JSON with commentary.
    json_match = re.search(r"\{[\s\S]*\}", raw_text)
    candidate = json_match.group(0) if json_match else raw_text

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        return None

    expected = [
        "tone_score",
        "acceptance_criteria_score",
        "user_story_format_score",
        "completeness_score",
    ]

    if not all(key in payload for key in expected):
        return None

    try:
        normalized = {key: round(_clamp(float(payload[key])), 4) for key in expected}
    except (TypeError, ValueError):
        return None

    return normalized


def evaluate_output_with_judge(judge_llm, bug_report: str, generated_output: str) -> Optional[Dict[str, float]]:
    prompt = (
        "You are evaluating quality of a generated user story from a bug report. "
        "Return ONLY valid JSON with numeric values between 0 and 1 for these keys: "
        "tone_score, acceptance_criteria_score, user_story_format_score, completeness_score.\n\n"
        "Scoring rubric:\n"
        "- tone_score: clarity, precision, professional tone\n"
        "- acceptance_criteria_score: testability, explicit Given/When/Then style\n"
        "- user_story_format_score: adherence to 'As a..., I want..., so that...'\n"
        "- completeness_score: has title, user story, acceptance criteria, edge cases\n\n"
        f"Bug report:\n{bug_report}\n\n"
        f"Generated output:\n{generated_output}"
    )

    result = judge_llm.invoke([("human", prompt)])
    raw_text = getattr(result, "content", str(result))
    return _parse_score_payload(raw_text)

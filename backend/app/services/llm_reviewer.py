from __future__ import annotations

import json
from typing import Protocol

from pydantic import BaseModel, Field, ValidationError

from app.graphql.types import Issue, Severity, Suggestion
from app.services.analyzer import AnalysisResult


class LlmIssue(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    severity: Severity
    line: int | None = Field(default=None, ge=1)
    explanation: str = Field(min_length=10, max_length=600)
    suggestion: str = Field(min_length=10, max_length=600)


class LlmSuggestion(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    explanation: str = Field(min_length=10, max_length=700)
    improved_code: str | None = None


class LlmReview(BaseModel):
    summary: str = Field(min_length=20, max_length=900)
    score_adjustment: int = Field(default=0, ge=-20, le=10)
    bugs: list[LlmIssue] = Field(default_factory=list, max_length=5)
    security_issues: list[LlmIssue] = Field(default_factory=list, max_length=5)
    performance_issues: list[LlmIssue] = Field(default_factory=list, max_length=5)
    suggestions: list[LlmSuggestion] = Field(default_factory=list, max_length=6)


class GeminiReviewError(RuntimeError):
    def __init__(self, message: str, *, reason: str = "unavailable") -> None:
        super().__init__(message)
        self.reason = reason


class CodeReviewer(Protocol):
    def review(self, *, language: str, code: str, context: str | None, base: AnalysisResult) -> LlmReview:
        ...


class GeminiCodeReviewer:
    def __init__(self, *, api_key: str, model: str, fallback_model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.fallback_model = fallback_model

    def review(self, *, language: str, code: str, context: str | None, base: AnalysisResult) -> LlmReview:
        from google import genai
        from google.genai import types

        prompt = build_review_prompt(language=language, code=code, context=context, base=base)
        client = genai.Client(api_key=self.api_key)

        try:
            response = generate_with_fallback(
                client=client,
                types=types,
                models=[self.model, self.fallback_model],
                prompt=prompt,
            )
        finally:
            client.close()

        if isinstance(response.parsed, LlmReview):
            return response.parsed

        return parse_llm_review(response.text or "")


def generate_with_fallback(*, client, types, models: list[str | None], prompt: str):
    last_error: Exception | None = None
    for model in [model for model in models if model]:
        try:
            return client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=1600,
                    response_mime_type="application/json",
                    response_schema=LlmReview,
                ),
            )
        except Exception as exc:
            last_error = exc
            if not is_retryable_gemini_error(exc):
                raise

    if last_error is not None:
        raise GeminiReviewError(
            str(last_error),
            reason="quota_exceeded" if is_quota_error(last_error) else "unavailable",
        ) from last_error

    raise ValueError("No Gemini model configured.")


def is_retryable_gemini_error(exc: Exception) -> bool:
    text = str(exc).upper()
    return "503" in text or "UNAVAILABLE" in text or "RESOURCE_EXHAUSTED" in text


def is_quota_error(exc: Exception) -> bool:
    text = str(exc).upper()
    return "429" in text or "RESOURCE_EXHAUSTED" in text or "QUOTA" in text


def build_review_prompt(
    *, language: str, code: str, context: str | None, base: AnalysisResult
) -> str:
    return f"""
You are a senior code reviewer for an AI code review platform.

Review the submitted {language} code and return ONLY valid JSON matching this shape:
{{
  "summary": "short practical review summary",
  "score_adjustment": -20,
  "bugs": [
    {{"title": "...", "severity": "LOW|MEDIUM|HIGH|CRITICAL", "line": 1, "explanation": "...", "suggestion": "..."}}
  ],
  "security_issues": [],
  "performance_issues": [],
  "suggestions": [
    {{"title": "...", "explanation": "...", "improved_code": null}}
  ]
}}

Rules:
- Do not repeat deterministic findings unless you add new, specific reasoning.
- Do not invent exact line numbers. Use null when unsure.
- Keep findings actionable and concise.
- Never include markdown fences.
- Preserve the deterministic security baseline; do not lower severity for known security risks.
- Use score_adjustment from -20 to 10 only.

Submitted context:
{context or "No additional context provided."}

Deterministic baseline:
summary: {base.summary}
score: {base.overall_score}
bug_count: {len(base.bugs)}
security_count: {len(base.security_issues)}
performance_count: {len(base.performance_issues)}

Code:
{code}
""".strip()


def parse_llm_review(raw_text: str) -> LlmReview:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.removeprefix("json").strip()

    try:
        payload = json.loads(text)
        return LlmReview.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("Gemini returned an invalid review payload.") from exc


def merge_llm_review(base: AnalysisResult, llm_review: LlmReview | None) -> AnalysisResult:
    if llm_review is None:
        return base

    bugs = [*base.bugs, *[to_issue(issue) for issue in llm_review.bugs]]
    security_issues = [
        *base.security_issues,
        *[to_issue(issue) for issue in llm_review.security_issues],
    ]
    performance_issues = [
        *base.performance_issues,
        *[to_issue(issue) for issue in llm_review.performance_issues],
    ]
    suggestions = [
        *base.suggestions,
        *[
            Suggestion(
                title=suggestion.title,
                explanation=suggestion.explanation,
                improved_code=suggestion.improved_code,
            )
            for suggestion in llm_review.suggestions
        ],
    ]

    score = max(0, min(100, base.overall_score + llm_review.score_adjustment))
    summary = f"{base.summary} Gemini review: {llm_review.summary}"

    return AnalysisResult(
        overall_score=score,
        summary=summary,
        bugs=dedupe_issues(bugs),
        security_issues=dedupe_issues(security_issues),
        performance_issues=dedupe_issues(performance_issues),
        suggestions=dedupe_suggestions(suggestions),
    )


def to_issue(issue: LlmIssue) -> Issue:
    return Issue(
        title=issue.title,
        severity=issue.severity,
        line=issue.line,
        explanation=issue.explanation,
        suggestion=issue.suggestion,
    )


def dedupe_issues(issues: list[Issue]) -> list[Issue]:
    seen: set[tuple[str, int | None]] = set()
    result: list[Issue] = []
    for issue in issues:
        key = (issue.title.lower(), issue.line)
        if key in seen:
            continue
        seen.add(key)
        result.append(issue)
    return result


def dedupe_suggestions(suggestions: list[Suggestion]) -> list[Suggestion]:
    seen: set[str] = set()
    result: list[Suggestion] = []
    for suggestion in suggestions:
        key = suggestion.title.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(suggestion)
    return result

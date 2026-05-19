from __future__ import annotations

import json
from typing import Protocol
from urllib.parse import parse_qs, urlsplit, urlunsplit

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


class LlmReviewError(RuntimeError):
    def __init__(self, message: str, *, reason: str = "unavailable") -> None:
        super().__init__(message)
        self.reason = reason


class CodeReviewer(Protocol):
    def review(self, *, language: str, code: str, context: str | None, base: AnalysisResult) -> LlmReview:
        ...


class AzureFoundryCodeReviewer:
    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        model: str,
        api_version: str | None = None,
        reasoning_effort: str = "medium",
        max_completion_tokens: int = 5000,
    ) -> None:
        self.base_url = normalize_foundry_base_url(endpoint)
        self.api_key = api_key
        self.model = model
        self.api_version = api_version or "preview"
        self.reasoning_effort = reasoning_effort
        self.max_completion_tokens = max_completion_tokens

    def review(self, *, language: str, code: str, context: str | None, base: AnalysisResult) -> LlmReview:
        from openai import AzureOpenAI

        prompt = build_review_prompt(language=language, code=code, context=context, base=base)
        client = AzureOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            api_version=self.api_version,
        )

        try:
            response = client.responses.create(
                model=self.model,
                instructions=(
                    "You are a senior code reviewer. Return only JSON matching "
                    "the requested schema."
                ),
                input=prompt,
                max_output_tokens=self.max_completion_tokens,
                reasoning={"effort": self.reasoning_effort},
                text={"format": {"type": "json_object"}},
            )
        except Exception as exc:
            raise LlmReviewError(
                str(exc),
                reason="quota_exceeded" if is_quota_error(exc) else "unavailable",
            ) from exc
        finally:
            client.close()

        text = response.output_text
        return parse_llm_review(text or "")


def normalize_foundry_base_url(target_uri: str) -> str:
    """Accept a Foundry base URL or a full responses/chat completions target URI."""
    parsed = urlsplit(target_uri.strip())
    path = parsed.path.rstrip("/")
    segments = [segment for segment in path.split("/") if segment]

    if len(segments) >= 3 and segments[-2:] == ["chat", "completions"]:
        segments = segments[:-2]

    if segments and segments[-1] == "responses":
        segments = segments[:-1]

    if "openai" in segments:
        openai_index = segments.index("openai")
        if len(segments) <= openai_index + 1 or segments[openai_index + 1] != "v1":
            segments = [*segments[: openai_index + 1], "v1"]
        else:
            segments = segments[: openai_index + 2]

    path = "/" + "/".join(segments) if segments else ""
    normalized = urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))
    return normalized.rstrip("/") + "/"


def extract_api_version(target_uri: str) -> str | None:
    parsed = urlsplit(target_uri.strip())
    versions = parse_qs(parsed.query).get("api-version")
    return versions[0] if versions else None


def is_retryable_llm_error(exc: Exception) -> bool:
    text = str(exc).upper()
    retryable_markers = (
        "408",
        "429",
        "500",
        "502",
        "503",
        "504",
        "RATE",
        "RESOURCE_EXHAUSTED",
        "TIMEOUT",
        "TOO MANY REQUESTS",
        "UNAVAILABLE",
    )
    return any(marker in text for marker in retryable_markers)


def is_quota_error(exc: Exception) -> bool:
    text = str(exc).upper()
    return "429" in text or "RESOURCE_EXHAUSTED" in text or "QUOTA" in text or "RATE LIMIT" in text


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
        raise ValueError("LLM reviewer returned an invalid review payload.") from exc


def merge_llm_review(
    base: AnalysisResult, llm_review: LlmReview | None, *, provider_name: str = "Azure Foundry"
) -> AnalysisResult:
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
    summary = f"{base.summary} {provider_name} review: {llm_review.summary}"

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

from app.graphql.inputs import CodeInput
from app.graphql.types import Severity
from app.services.analyzer import AnalysisResult
from app.services.llm_reviewer import (
    GeminiReviewError,
    LlmIssue,
    LlmReview,
    LlmSuggestion,
    is_quota_error,
    is_retryable_gemini_error,
)
from app.services.review_service import ReviewService


class FakeReviewer:
    def review(self, *, language: str, code: str, context: str | None, base: AnalysisResult) -> LlmReview:
        return LlmReview(
            summary="The function needs clearer input validation and a narrower return path.",
            score_adjustment=-7,
            bugs=[
                LlmIssue(
                    title="Missing empty input branch",
                    severity=Severity.MEDIUM,
                    line=2,
                    explanation="The function does not document or handle empty input clearly.",
                    suggestion="Add an explicit guard clause and test for the empty input path.",
                )
            ],
            suggestions=[
                LlmSuggestion(
                    title="Clarify function contract",
                    explanation="Document expected inputs and return values before adding more logic.",
                    improved_code=None,
                )
            ],
        )


class BrokenReviewer:
    def review(self, *, language: str, code: str, context: str | None, base: AnalysisResult) -> LlmReview:
        raise RuntimeError("network unavailable")


class QuotaReviewer:
    def review(self, *, language: str, code: str, context: str | None, base: AnalysisResult) -> LlmReview:
        raise GeminiReviewError("429 RESOURCE_EXHAUSTED quota exceeded", reason="quota_exceeded")


def test_review_service_merges_gemini_style_review() -> None:
    service = ReviewService(code_reviewer=FakeReviewer())

    review = service.analyze_code(
        CodeInput(language="python", code="def total(items):\n    return sum(items)")
    )

    assert review.overall_score == 93
    assert "Gemini review:" in review.summary
    assert review.bugs[0].title == "Missing empty input branch"
    assert review.suggestions[-1].title == "Clarify function contract"


def test_review_service_falls_back_when_gemini_fails() -> None:
    service = ReviewService(code_reviewer=BrokenReviewer())

    review = service.analyze_code(CodeInput(language="python", code="print('hello')"))

    assert review.overall_score < 100
    assert any(suggestion.title == "Gemini review unavailable" for suggestion in review.suggestions)


def test_review_service_reports_gemini_quota_failure() -> None:
    service = ReviewService(code_reviewer=QuotaReviewer())

    review = service.analyze_code(CodeInput(language="python", code="print('hello')"))

    assert any(suggestion.title == "Gemini quota exceeded" for suggestion in review.suggestions)


def test_gemini_retryable_error_detection() -> None:
    assert is_retryable_gemini_error(RuntimeError("503 UNAVAILABLE"))
    assert is_retryable_gemini_error(RuntimeError("RESOURCE_EXHAUSTED"))
    assert not is_retryable_gemini_error(RuntimeError("401 unauthorized"))
    assert is_quota_error(RuntimeError("429 RESOURCE_EXHAUSTED quota exceeded"))

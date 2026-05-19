from app.graphql.inputs import CodeInput
from app.graphql.types import Severity
from app.services.analyzer import AnalysisResult
from app.services.llm_reviewer import (
    LlmReviewError,
    LlmIssue,
    LlmReview,
    LlmSuggestion,
    is_quota_error,
    is_retryable_llm_error,
    extract_api_version,
    normalize_foundry_base_url,
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
        raise LlmReviewError("429 RESOURCE_EXHAUSTED quota exceeded", reason="quota_exceeded")


def test_review_service_merges_azure_foundry_style_review() -> None:
    service = ReviewService(code_reviewer=FakeReviewer())

    review = service.analyze_code(
        CodeInput(language="python", code="def total(items):\n    return sum(items)")
    )

    assert review.overall_score == 93
    assert "Azure Foundry review:" in review.summary
    assert review.bugs[0].title == "Missing empty input branch"
    assert review.suggestions[-1].title == "Clarify function contract"


def test_review_service_falls_back_when_azure_foundry_fails() -> None:
    service = ReviewService(code_reviewer=BrokenReviewer())

    review = service.analyze_code(CodeInput(language="python", code="print('hello')"))

    assert review.overall_score < 100
    assert any(suggestion.title == "Azure Foundry review unavailable" for suggestion in review.suggestions)


def test_review_service_reports_azure_foundry_quota_failure() -> None:
    service = ReviewService(code_reviewer=QuotaReviewer())

    review = service.analyze_code(CodeInput(language="python", code="print('hello')"))

    assert any(suggestion.title == "Azure Foundry quota exceeded" for suggestion in review.suggestions)


def test_llm_retryable_error_detection() -> None:
    assert is_retryable_llm_error(RuntimeError("503 UNAVAILABLE"))
    assert is_retryable_llm_error(RuntimeError("RESOURCE_EXHAUSTED"))
    assert not is_retryable_llm_error(RuntimeError("401 unauthorized"))
    assert is_quota_error(RuntimeError("429 RESOURCE_EXHAUSTED quota exceeded"))


def test_foundry_target_uri_normalization() -> None:
    assert (
        normalize_foundry_base_url("https://example.openai.azure.com/openai/v1/chat/completions")
        == "https://example.openai.azure.com/openai/v1/"
    )
    assert (
        normalize_foundry_base_url("https://example.services.ai.azure.com/models/chat/completions")
        == "https://example.services.ai.azure.com/models/"
    )
    assert (
        normalize_foundry_base_url(
            "https://example.cognitiveservices.azure.com/openai/responses?api-version=preview"
        )
        == "https://example.cognitiveservices.azure.com/openai/v1/"
    )
    assert (
        extract_api_version(
            "https://example.cognitiveservices.azure.com/openai/responses?api-version=preview"
        )
        == "preview"
    )

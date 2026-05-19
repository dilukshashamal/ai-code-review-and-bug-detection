from collections import Counter
from datetime import UTC, datetime
import logging
from uuid import uuid4

from app.core.config import get_settings
from app.graphql.inputs import CodeInput
from app.graphql.types import CodeReview, DashboardStats, Suggestion
from app.services.analyzer import analyze_source_code, normalize_language
from app.services.llm_reviewer import (
    AzureFoundryCodeReviewer,
    CodeReviewer,
    LlmReviewError,
    merge_llm_review,
)

logger = logging.getLogger(__name__)


class ReviewService:
    def __init__(self, code_reviewer: CodeReviewer | None = None) -> None:
        self._reviews: list[CodeReview] = []
        self._code_reviewer = code_reviewer

    def analyze_code(self, input: CodeInput) -> CodeReview:
        language = input.language.strip()
        code = input.code.strip()
        title = input.title.strip() if input.title else None

        if not language:
            raise ValueError("Programming language is required.")

        if not code:
            raise ValueError("Code is required.")

        analysis = analyze_source_code(language=language, code=input.code, context=input.context)
        llm_reviewer = self._code_reviewer or build_default_reviewer()

        if llm_reviewer is not None:
            try:
                llm_review = llm_reviewer.review(
                    language=language,
                    code=input.code,
                    context=input.context,
                    base=analysis,
                )
                analysis = merge_llm_review(analysis, llm_review)
            except LlmReviewError as exc:
                logger.warning("Azure Foundry review failed: %s", exc)
                if exc.reason == "quota_exceeded":
                    suggestion_title = "Azure Foundry quota exceeded"
                    explanation = (
                        "The deterministic rule-based review completed, but Azure Foundry returned "
                        "a quota or rate-limit error for the configured API key/model."
                    )
                else:
                    suggestion_title = "Azure Foundry review unavailable"
                    explanation = (
                        "The deterministic rule-based review completed, but the Azure Foundry "
                        "review layer could not return a valid response."
                    )
                analysis.suggestions.append(
                    Suggestion(
                        title=suggestion_title,
                        explanation=explanation,
                        improved_code=None,
                    )
                )
            except Exception as exc:
                logger.warning("Azure Foundry review failed: %s", exc)
                analysis.suggestions.append(
                    Suggestion(
                        title="Azure Foundry review unavailable",
                        explanation=(
                            "The deterministic rule-based review completed, but the Azure Foundry "
                            "review layer could not return a valid response."
                        ),
                        improved_code=None,
                    )
                )
        elif get_settings().enable_llm_review:
            analysis.suggestions.append(
                Suggestion(
                    title="Azure Foundry review not configured",
                    explanation=(
                        "Add AZURE_FOUNDRY_ENDPOINT and AZURE_FOUNDRY_KEY to backend/.env "
                        "and restart the backend to enable Azure Foundry reasoning."
                    ),
                    improved_code=None,
                )
            )

        review = CodeReview(
            id=uuid4().hex,
            title=title,
            language=normalize_language(language),
            submitted_code=input.code,
            overall_score=analysis.overall_score,
            summary=analysis.summary,
            bugs=analysis.bugs,
            security_issues=analysis.security_issues,
            performance_issues=analysis.performance_issues,
            suggestions=analysis.suggestions,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._reviews.insert(0, review)
        return review

    def list_reviews(self) -> list[CodeReview]:
        return list(self._reviews)

    def get_review(self, review_id: str) -> CodeReview | None:
        return next((review for review in self._reviews if str(review.id) == review_id), None)

    def get_dashboard_stats(self) -> DashboardStats:
        total_reviews = len(self._reviews)
        total_score = sum(review.overall_score for review in self._reviews)
        language_counts = Counter(review.language for review in self._reviews)

        return DashboardStats(
            total_reviews=total_reviews,
            average_score=(total_score / total_reviews) if total_reviews else 0.0,
            total_bugs=sum(len(review.bugs) for review in self._reviews),
            total_security_issues=sum(len(review.security_issues) for review in self._reviews),
            most_used_language=language_counts.most_common(1)[0][0] if language_counts else None,
        )


def build_default_reviewer() -> CodeReviewer | None:
    settings = get_settings()
    if not settings.enable_llm_review:
        return None

    if settings.llm_review_provider.lower() != "azure_foundry":
        return None

    if not settings.azure_foundry_endpoint or not settings.azure_foundry_key:
        return None

    return AzureFoundryCodeReviewer(
        endpoint=settings.azure_foundry_endpoint,
        api_key=settings.azure_foundry_key,
        model=settings.azure_foundry_model,
        api_version=settings.azure_foundry_api_version,
        reasoning_effort=settings.azure_foundry_reasoning_effort,
        max_completion_tokens=settings.azure_foundry_max_completion_tokens,
    )


review_service = ReviewService()

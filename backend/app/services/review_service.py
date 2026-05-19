from collections import Counter
from datetime import UTC, datetime
import logging
from uuid import uuid4

from app.graphql.inputs import CodeInput
from app.graphql.types import CodeReview, DashboardStats, Suggestion
from app.core.config import get_settings
from app.services.analyzer import analyze_source_code, normalize_language
from app.services.llm_reviewer import (
    CodeReviewer,
    GeminiCodeReviewer,
    GeminiReviewError,
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
            except GeminiReviewError as exc:
                logger.warning("Gemini review failed: %s", exc)
                if exc.reason == "quota_exceeded":
                    title = "Gemini quota exceeded"
                    explanation = (
                        "The deterministic rule-based review completed, but Gemini returned "
                        "a quota or rate-limit error for the configured API key/model."
                    )
                else:
                    title = "Gemini review unavailable"
                    explanation = (
                        "The deterministic rule-based review completed, but the Gemini "
                        "review layer could not return a valid response."
                    )
                analysis.suggestions.append(
                    Suggestion(
                        title=title,
                        explanation=explanation,
                        improved_code=None,
                    )
                )
            except Exception as exc:
                logger.warning("Gemini review failed: %s", exc)
                analysis.suggestions.append(
                    Suggestion(
                        title="Gemini review unavailable",
                        explanation=(
                            "The deterministic rule-based review completed, but the Gemini "
                            "review layer could not return a valid response."
                        ),
                        improved_code=None,
                    )
                )
        elif get_settings().enable_gemini_review:
            analysis.suggestions.append(
                Suggestion(
                    title="Gemini review not configured",
                    explanation=(
                        "Add GEMINI_API_KEY or GOOGLE_API_KEY to backend/.env and restart "
                        "the backend to enable Gemini reasoning."
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
    gemini_api_key = settings.resolved_gemini_api_key
    if not settings.enable_gemini_review or not gemini_api_key:
        return None

    return GeminiCodeReviewer(
        api_key=gemini_api_key,
        model=settings.gemini_model,
        fallback_model=settings.gemini_fallback_model,
    )


review_service = ReviewService()

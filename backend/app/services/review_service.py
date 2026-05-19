from collections import Counter
from datetime import UTC, datetime
from uuid import uuid4

from app.graphql.inputs import CodeInput
from app.graphql.types import CodeReview, DashboardStats
from app.services.analyzer import analyze_source_code, normalize_language


class ReviewService:
    def __init__(self) -> None:
        self._reviews: list[CodeReview] = []

    def analyze_code(self, input: CodeInput) -> CodeReview:
        language = input.language.strip()
        code = input.code.strip()
        title = input.title.strip() if input.title else None

        if not language:
            raise ValueError("Programming language is required.")

        if not code:
            raise ValueError("Code is required.")

        analysis = analyze_source_code(language=language, code=input.code, context=input.context)

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


review_service = ReviewService()

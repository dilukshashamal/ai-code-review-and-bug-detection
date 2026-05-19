from enum import Enum

import strawberry


@strawberry.enum
class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@strawberry.type
class Issue:
    title: str
    severity: Severity
    explanation: str
    suggestion: str
    line: int | None = None


@strawberry.type
class Suggestion:
    title: str
    explanation: str
    improved_code: str | None = None


@strawberry.type
class CodeReview:
    id: strawberry.ID
    title: str | None
    language: str
    submitted_code: str
    corrected_code: str | None
    overall_score: int
    summary: str
    bugs: list[Issue]
    security_issues: list[Issue]
    performance_issues: list[Issue]
    suggestions: list[Suggestion]
    created_at: str


@strawberry.type
class DashboardStats:
    total_reviews: int
    average_score: float
    total_bugs: int
    total_security_issues: int
    most_used_language: str | None = None

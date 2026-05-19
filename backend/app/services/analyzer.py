from dataclasses import dataclass
from enum import Enum
import re

from app.graphql.types import Issue, Severity, Suggestion


class IssueType(Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"


@dataclass(frozen=True)
class AnalyzerFinding:
    issue_type: IssueType
    issue: Issue
    penalty: int


@dataclass(frozen=True)
class AnalysisResult:
    overall_score: int
    summary: str
    corrected_code: str | None
    bugs: list[Issue]
    security_issues: list[Issue]
    performance_issues: list[Issue]
    suggestions: list[Suggestion]


@dataclass(frozen=True)
class Rule:
    pattern: re.Pattern[str]
    issue_type: IssueType
    title: str
    severity: Severity
    explanation: str
    suggestion: str
    penalty: int
    languages: frozenset[str] | None = None

    def applies_to(self, language: str) -> bool:
        return self.languages is None or language.lower() in self.languages


LANGUAGE_ALIASES = {
    "js": "javascript",
    "jsx": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    "py": "python",
    "c++": "cpp",
}


RULES = [
    Rule(
        pattern=re.compile(
            r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"\n]{8,}['\"]"
        ),
        issue_type=IssueType.SECURITY,
        title="Possible hardcoded secret",
        severity=Severity.CRITICAL,
        explanation=(
            "The code appears to assign a secret-like value directly in source code. "
            "Hardcoded credentials can leak through repositories, logs, or bundles."
        ),
        suggestion="Move secrets to environment variables or a managed secret store and rotate exposed values.",
        penalty=28,
    ),
    Rule(
        pattern=re.compile(r"(?i)(execute|query|raw)\s*\([^)]*(f?['\"].*(select|insert|update|delete)|\+)", re.DOTALL),
        issue_type=IssueType.SECURITY,
        title="Possible unsafe SQL construction",
        severity=Severity.HIGH,
        explanation=(
            "The code appears to build a SQL statement dynamically. Dynamic SQL with "
            "string interpolation or concatenation can introduce injection risk."
        ),
        suggestion="Use parameterized queries or a query builder that binds user input separately.",
        penalty=20,
    ),
    Rule(
        pattern=re.compile(r"(?i)\beval\s*\(|new\s+Function\s*\("),
        issue_type=IssueType.SECURITY,
        title="Dynamic code execution",
        severity=Severity.HIGH,
        explanation="Dynamic code execution makes input boundaries difficult to trust and audit.",
        suggestion="Replace dynamic execution with explicit parsing or a constrained command map.",
        penalty=20,
        languages=frozenset({"javascript", "typescript"}),
    ),
    Rule(
        pattern=re.compile(r"(?i)\bexec\s*\(|\bsubprocess\.(Popen|call|run)\s*\([^)]*shell\s*=\s*True", re.DOTALL),
        issue_type=IssueType.SECURITY,
        title="Command execution risk",
        severity=Severity.HIGH,
        explanation="The code appears to execute shell commands, which can become command injection if inputs are unsafe.",
        suggestion="Avoid shell execution or pass arguments as an array after strict validation.",
        penalty=18,
        languages=frozenset({"python"}),
    ),
    Rule(
        pattern=re.compile(r"(?i)(except\s*:|catch\s*\([^)]*\)\s*\{\s*\})", re.DOTALL),
        issue_type=IssueType.BUG,
        title="Swallowed exception",
        severity=Severity.MEDIUM,
        explanation="The code catches an error without handling, logging, or re-raising it.",
        suggestion="Handle the error intentionally and return a safe failure path.",
        penalty=12,
    ),
    Rule(
        pattern=re.compile(r"(?m)^\s*console\.log\s*\("),
        issue_type=IssueType.QUALITY,
        title="Console logging left in code",
        severity=Severity.LOW,
        explanation="Console logging can leak runtime details and adds noise in production code.",
        suggestion="Use a structured logger with levels, or remove debug logging before release.",
        penalty=5,
        languages=frozenset({"javascript", "typescript"}),
    ),
    Rule(
        pattern=re.compile(r"(?m)^\s*print\s*\("),
        issue_type=IssueType.QUALITY,
        title="Print debugging left in code",
        severity=Severity.LOW,
        explanation="Print statements are useful during debugging but are not ideal for production observability.",
        suggestion="Use structured logging with levels and contextual fields.",
        penalty=5,
        languages=frozenset({"python"}),
    ),
    Rule(
        pattern=re.compile(r"(?i)for\s*\([^)]*;\s*[^;]*\.length\s*;[^)]*\)|for\s+\w+\s+in\s+range\(len\("),
        issue_type=IssueType.PERFORMANCE,
        title="Index-based loop may be avoidable",
        severity=Severity.LOW,
        explanation="Index-based loops can be harder to read and sometimes repeat lookups unnecessarily.",
        suggestion="Prefer direct iteration or cache repeated length/lookups when appropriate.",
        penalty=4,
    ),
]


def analyze_source_code(language: str, code: str, context: str | None = None) -> AnalysisResult:
    normalized_language = normalize_language(language)
    findings = collect_findings(normalized_language, code)
    suggestions = build_suggestions(findings, context)
    score = calculate_score(findings, code)

    return AnalysisResult(
        overall_score=score,
        summary=build_summary(score, findings),
        corrected_code=None,
        bugs=[finding.issue for finding in findings if finding.issue_type is IssueType.BUG],
        security_issues=[
            finding.issue for finding in findings if finding.issue_type is IssueType.SECURITY
        ],
        performance_issues=[
            finding.issue for finding in findings if finding.issue_type is IssueType.PERFORMANCE
        ],
        suggestions=suggestions,
    )


def normalize_language(language: str) -> str:
    key = language.strip().lower()
    return LANGUAGE_ALIASES.get(key, key)


def collect_findings(language: str, code: str) -> list[AnalyzerFinding]:
    findings: list[AnalyzerFinding] = []
    used_titles: set[str] = set()

    for rule in RULES:
        if not rule.applies_to(language):
            continue

        match = rule.pattern.search(code)
        if not match or rule.title in used_titles:
            continue

        findings.append(
            AnalyzerFinding(
                issue_type=rule.issue_type,
                issue=Issue(
                    title=rule.title,
                    severity=rule.severity,
                    line=line_number_for_offset(code, match.start()),
                    explanation=rule.explanation,
                    suggestion=rule.suggestion,
                ),
                penalty=rule.penalty,
            )
        )
        used_titles.add(rule.title)

    if len(code.splitlines()) > 80:
        findings.append(
            AnalyzerFinding(
                issue_type=IssueType.QUALITY,
                issue=Issue(
                    title="Large snippet without decomposition",
                    severity=Severity.MEDIUM,
                    line=None,
                    explanation="The submitted code is large enough that smaller functions or modules may be easier to review and test.",
                    suggestion="Split responsibilities into smaller units with focused tests around each unit.",
                ),
                penalty=8,
            )
        )

    return findings


def line_number_for_offset(code: str, offset: int) -> int:
    return code.count("\n", 0, offset) + 1


def calculate_score(findings: list[AnalyzerFinding], code: str) -> int:
    score = 100 - sum(finding.penalty for finding in findings)

    if len(code.strip()) < 20:
        score -= 8

    return max(0, min(100, score))


def build_summary(score: int, findings: list[AnalyzerFinding]) -> str:
    if not findings:
        return "No obvious rule-based issues were detected. This is a first-pass static review, not a full security audit."

    critical_or_high = sum(
        1
        for finding in findings
        if finding.issue.severity in {Severity.CRITICAL, Severity.HIGH}
    )

    return (
        f"Detected {len(findings)} rule-based finding"
        f"{'' if len(findings) == 1 else 's'} with {critical_or_high} high-priority "
        f"item{'' if critical_or_high == 1 else 's'}. Current quality score is {score}."
    )


def build_suggestions(findings: list[AnalyzerFinding], context: str | None) -> list[Suggestion]:
    suggestions: list[Suggestion] = []

    if any(finding.issue_type is IssueType.SECURITY for finding in findings):
        suggestions.append(
            Suggestion(
                title="Prioritize security fixes first",
                explanation="Address critical and high security findings before readability or performance cleanup.",
                improved_code=None,
            )
        )

    if any(finding.issue_type is IssueType.BUG for finding in findings):
        suggestions.append(
            Suggestion(
                title="Add failure-path tests",
                explanation="Add tests that exercise invalid inputs and exception paths so bugs do not silently pass.",
                improved_code=None,
            )
        )

    if context:
        suggestions.append(
            Suggestion(
                title="Use project context during review",
                explanation=f"Review assumptions against the submitted context: {context.strip()}",
                improved_code=None,
            )
        )

    if not suggestions:
        suggestions.append(
            Suggestion(
                title="Continue with human review",
                explanation="Use this automated pass as a filter, then review domain logic, tests, and edge cases manually.",
                improved_code=None,
            )
        )

    return suggestions

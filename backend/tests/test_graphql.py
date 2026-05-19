from fastapi.testclient import TestClient

from app.main import create_app


def test_analyze_code_mutation_returns_structured_review() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/graphql",
        json={
            "query": """
                mutation AnalyzeCode($input: CodeInput!) {
                  analyzeCode(input: $input) {
                    id
                    language
                    submittedCode
                    overallScore
                    summary
                    bugs { title severity line explanation suggestion }
                    securityIssues { title severity line explanation suggestion }
                    performanceIssues { title severity line explanation suggestion }
                    suggestions { title explanation improvedCode }
                    createdAt
                  }
                }
            """,
            "variables": {
                "input": {
                    "title": "Example",
                    "language": "python",
                    "code": "print('hello')",
                    "context": "CLI script",
                }
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body
    review = body["data"]["analyzeCode"]
    assert review["language"] == "python"
    assert review["submittedCode"] == "print('hello')"
    assert review["overallScore"] < 100
    assert any(
        suggestion["title"] == "Use project context during review"
        for suggestion in review["suggestions"]
    )


def test_analyze_code_detects_security_and_bug_findings() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/graphql",
        json={
            "query": """
                mutation AnalyzeCode($input: CodeInput!) {
                  analyzeCode(input: $input) {
                    overallScore
                    summary
                    bugs { title severity line }
                    securityIssues { title severity line suggestion }
                    suggestions { title }
                  }
                }
            """,
            "variables": {
                "input": {
                    "language": "python",
                    "code": "\n".join(
                        [
                            "api_key = 'sk_test_1234567890'",
                            "try:",
                            "    risky_call()",
                            "except:",
                            "    pass",
                        ]
                    ),
                }
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body
    review = body["data"]["analyzeCode"]
    assert review["overallScore"] < 70
    assert review["securityIssues"][0]["title"] == "Possible hardcoded secret"
    assert review["securityIssues"][0]["severity"] == "CRITICAL"
    assert review["bugs"][0]["title"] == "Swallowed exception"
    assert review["suggestions"][0]["title"] == "Prioritize security fixes first"


def test_review_history_and_dashboard_stats_reflect_analyzed_code() -> None:
    client = TestClient(create_app())

    client.post(
        "/graphql",
        json={
            "query": """
                mutation AnalyzeCode($input: CodeInput!) {
                  analyzeCode(input: $input) { id }
                }
            """,
            "variables": {
                "input": {
                    "language": "typescript",
                    "code": "const value: number = 1;",
                }
            },
        },
    )

    response = client.post(
        "/graphql",
        json={
            "query": """
                query ReviewHistory {
                  reviewHistory {
                    id
                    language
                    overallScore
                  }
                  dashboardStats {
                    totalReviews
                    averageScore
                    totalBugs
                    totalSecurityIssues
                    mostUsedLanguage
                  }
                }
            """
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "errors" not in body
    assert len(body["data"]["reviewHistory"]) >= 1
    assert body["data"]["dashboardStats"]["totalReviews"] >= 1
    assert body["data"]["dashboardStats"]["mostUsedLanguage"] in {"python", "typescript"}

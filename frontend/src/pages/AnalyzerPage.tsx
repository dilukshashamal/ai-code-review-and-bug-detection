import { type FormEvent, useMemo, useState } from "react";

import type { CodeReview, Issue, Suggestion } from "../graphql/types";
import { useAnalyzeCode } from "../hooks/useAnalyzeCode";
import { SUPPORTED_LANGUAGES } from "../utils/languages";

export function AnalyzerPage() {
  const [title, setTitle] = useState("");
  const [language, setLanguage] = useState("typescript");
  const [context, setContext] = useState("");
  const [code, setCode] = useState("const total = items.reduce((sum, item) => sum + item.price, 0);");
  const [analyzeCode, { data, loading, error }] = useAnalyzeCode();

  const review = data?.analyzeCode;
  const canSubmit = code.trim().length > 0 && language.trim().length > 0 && !loading;

  const issueCount = useMemo(() => {
    if (!review) {
      return 0;
    }

    return (
      review.bugs.length + review.securityIssues.length + review.performanceIssues.length
    );
  }, [review]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!canSubmit) {
      return;
    }

    await analyzeCode({
      variables: {
        input: {
          title: title.trim() || null,
          language,
          code,
          context: context.trim() || null,
        },
      },
    });
  }

  return (
    <section className="analyzer-grid" aria-labelledby="analyzer-title">
      <form className="editor-panel" onSubmit={handleSubmit}>
        <div className="panel-header">
          <div>
            <p className="eyebrow">Analyzer</p>
            <h2 id="analyzer-title">Submit code for review</h2>
          </div>
          <select
            aria-label="Programming language"
            value={language}
            onChange={(event) => setLanguage(event.target.value)}
          >
            {SUPPORTED_LANGUAGES.map((language) => (
              <option key={language.value} value={language.value}>
                {language.label}
              </option>
            ))}
          </select>
        </div>
        <div className="metadata-row">
          <label>
            <span>Title</span>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Authentication helper"
            />
          </label>
          <label>
            <span>Context</span>
            <input
              value={context}
              onChange={(event) => setContext(event.target.value)}
              placeholder="Backend API, utility function, UI component"
            />
          </label>
        </div>
        <textarea
          aria-label="Source code"
          className="code-input"
          value={code}
          onChange={(event) => setCode(event.target.value)}
          placeholder="Paste source code here."
          spellCheck={false}
        />
        <div className="action-row">
          <p>{code.trim().length.toLocaleString()} characters ready</p>
          <button type="submit" disabled={!canSubmit}>
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </form>

      <aside className="result-panel" aria-label="Review result preview">
        <div className="result-heading">
          <div>
            <p className="eyebrow">Report</p>
            <h2>Review result</h2>
          </div>
          {review ? <strong>{review.overallScore}</strong> : null}
        </div>

        {loading ? <div className="empty-state">Running GraphQL analysis...</div> : null}

        {error ? (
          <div className="error-state" role="alert">
            {error.message}
          </div>
        ) : null}

        {!loading && !error && !review ? (
          <div className="empty-state">Submit code to see structured feedback.</div>
        ) : null}

        {!loading && !error && review ? (
          <ReviewSummary review={review} issueCount={issueCount} />
        ) : null}
      </aside>
    </section>
  );
}

function ReviewSummary({
  review,
  issueCount,
}: {
  review: CodeReview;
  issueCount: number;
}) {
  return (
    <div className="review-summary">
      <dl className="metric-strip">
        <div>
          <dt>Issues</dt>
          <dd>{issueCount}</dd>
        </div>
        <div>
          <dt>Language</dt>
          <dd>{review.language}</dd>
        </div>
      </dl>

      <p className="summary-copy">{review.summary}</p>

      <IssueGroup title="Bugs" issues={review.bugs} />
      <IssueGroup title="Security" issues={review.securityIssues} />
      <IssueGroup title="Performance" issues={review.performanceIssues} />
      <SuggestionGroup suggestions={review.suggestions} />
    </div>
  );
}

function IssueGroup({ title, issues }: { title: string; issues: Issue[] }) {
  return (
    <section className="result-section">
      <h3>{title}</h3>
      {issues.length === 0 ? (
        <p>No findings returned.</p>
      ) : (
        <ul>
          {issues.map((issue) => (
            <li key={`${issue.title}-${issue.line ?? "unknown"}`}>
              <strong>{issue.title}</strong>
              <span>{issue.severity}</span>
              <p>{issue.explanation}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function SuggestionGroup({ suggestions }: { suggestions: Suggestion[] }) {
  return (
    <section className="result-section">
      <h3>Suggestions</h3>
      {suggestions.length === 0 ? (
        <p>No suggestions returned.</p>
      ) : (
        <ul>
          {suggestions.map((suggestion) => (
            <li key={suggestion.title}>
              <strong>{suggestion.title}</strong>
              <p>{suggestion.explanation}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

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

  const currentLanguage = SUPPORTED_LANGUAGES.find((item) => item.value === language);
  const allIssues = review
    ? [...review.bugs, ...review.securityIssues, ...review.performanceIssues]
    : [];

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
    <form className="studio-grid" onSubmit={handleSubmit} aria-labelledby="analyzer-title">
      <section className="studio-panel editor-panel">
        <div className="workspace-tabs" aria-label="Analyzer modes">
          <button className="tab-button active" type="button">
            Prompt
          </button>
          <button className="tab-button" type="button">
            Code
          </button>
          <button className="tab-button" type="button">
            Review
          </button>
        </div>

        <div className="prompt-header">
          <div>
            <p className="eyebrow">Analyzer</p>
            <h2 id="analyzer-title">Code review prompt</h2>
          </div>
          <div className="prompt-meta" aria-label="Current run metadata">
            <span>{currentLanguage?.label ?? language}</span>
            <span>{code.trim().length.toLocaleString()} chars</span>
          </div>
        </div>

        <textarea
          aria-label="Source code"
          className="code-input"
          value={code}
          onChange={(event) => setCode(event.target.value)}
          placeholder="Paste source code here."
          spellCheck={false}
        />

        <div className="composer-bar">
          <div className="composer-tools" aria-label="Editor tools">
            <button type="button" title="Attach file" aria-label="Attach file">
              +
            </button>
            <button type="button" title="Clear editor" aria-label="Clear editor" onClick={() => setCode("")}>
              x
            </button>
          </div>
          <button className="run-button" type="submit" disabled={!canSubmit}>
            {loading ? "Running" : "Run"}
          </button>
        </div>
      </section>

      <aside className="studio-panel settings-panel" id="run-settings" aria-label="Run settings">
        <div className="panel-heading">
          <p className="eyebrow">Run settings</p>
          <h2>Configuration</h2>
        </div>

        <label className="field-stack">
          <span>Model</span>
          <input value="Azure Foundry / GPT-5.4" readOnly />
        </label>

        <label className="field-stack">
          <span>Language</span>
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
        </label>

        <label className="field-stack">
          <span>Title</span>
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Authentication helper"
          />
        </label>

        <label className="field-stack">
          <span>Context</span>
          <textarea
            className="context-input"
            value={context}
            onChange={(event) => setContext(event.target.value)}
            placeholder="Backend API, utility function, UI component"
          />
        </label>

        <div className="settings-summary" aria-label="Analysis summary">
          <div>
            <span>Static rules</span>
            <strong>On</strong>
          </div>
          <div>
            <span>LLM review</span>
            <strong>On</strong>
          </div>
        </div>
      </aside>

      <section className="studio-panel result-panel" id="review-output" aria-label="Review result">
        <div className="result-heading">
          <div>
            <p className="eyebrow">Output</p>
            <h2>Review result</h2>
          </div>
          {review ? <strong>{review.overallScore}</strong> : <span className="score-placeholder">--</span>}
        </div>

        {loading ? <div className="empty-state">Running analysis...</div> : null}

        {error ? (
          <div className="error-state" role="alert">
            {error.message}
          </div>
        ) : null}

        {!loading && !error && !review ? (
          <div className="empty-state">No review generated yet.</div>
        ) : null}

        {!loading && !error && review ? (
          <ReviewSummary
            review={review}
            issueCount={issueCount}
            issues={allIssues}
            onApplyCorrection={setCode}
          />
        ) : null}
      </section>
    </form>
  );
}

function ReviewSummary({
  review,
  issueCount,
  issues,
  onApplyCorrection,
}: {
  review: CodeReview;
  issueCount: number;
  issues: Issue[];
  onApplyCorrection: (code: string) => void;
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

      <CorrectedCode code={review.correctedCode} onApplyCorrection={onApplyCorrection} />
      <IssueGroup issues={issues} />
      <SuggestionGroup suggestions={review.suggestions} />
    </div>
  );
}

function CorrectedCode({
  code,
  onApplyCorrection,
}: {
  code?: string | null;
  onApplyCorrection: (code: string) => void;
}) {
  return (
    <section className="result-section corrected-code-section">
      <div className="section-title-row">
        <h3>Corrected code</h3>
        {code ? (
          <button type="button" onClick={() => onApplyCorrection(code)}>
            Apply correction
          </button>
        ) : null}
      </div>
      {code ? (
        <pre className="corrected-code-block">
          <code>{code}</code>
        </pre>
      ) : (
        <p>No full corrected snippet returned.</p>
      )}
    </section>
  );
}

function IssueGroup({ issues }: { issues: Issue[] }) {
  return (
    <section className="result-section">
      <h3>Findings</h3>
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
              {suggestion.improvedCode ? (
                <pre className="inline-code-block">
                  <code>{suggestion.improvedCode}</code>
                </pre>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

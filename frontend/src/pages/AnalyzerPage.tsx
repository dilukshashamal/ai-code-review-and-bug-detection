import { type FormEvent, useMemo, useState } from "react";

import type { CodeReview, Issue, Severity, Suggestion } from "../graphql/types";
import { useAnalyzeCode } from "../hooks/useAnalyzeCode";
import { SUPPORTED_LANGUAGES } from "../utils/languages";

const SEVERITY_META: Record<Severity, { label: string; className: string }> = {
  LOW: { label: "Low", className: "sev-low" },
  MEDIUM: { label: "Medium", className: "sev-medium" },
  HIGH: { label: "High", className: "sev-high" },
  CRITICAL: { label: "Critical", className: "sev-critical" },
};

export function AnalyzerPage() {
  const [title, setTitle] = useState("");
  const [language, setLanguage] = useState("typescript");
  const [context, setContext] = useState("");
  const [code, setCode] = useState(
    'const total = items.reduce((sum, item) => sum + item.price, 0);',
  );
  const [analyzeCode, { data, loading, error }] = useAnalyzeCode();

  const review = data?.analyzeCode;
  const canSubmit = code.trim().length > 0 && language.trim().length > 0 && !loading;

  const issueCount = useMemo(() => {
    if (!review) return 0;
    return review.bugs.length + review.securityIssues.length + review.performanceIssues.length;
  }, [review]);

  const currentLanguage = SUPPORTED_LANGUAGES.find((l) => l.value === language);
  const allIssues = review
    ? [...review.bugs, ...review.securityIssues, ...review.performanceIssues]
    : [];

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!canSubmit) return;
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
    <form
      className="studio-grid"
      onSubmit={handleSubmit}
      aria-labelledby="analyzer-title"
    >
      {/* ── Editor panel ── */}
      <section className="studio-panel editor-panel">
        <div className="panel-topbar">
          <div className="panel-topbar-left">
            <span className="panel-icon" aria-hidden="true">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M5 4l-3 4 3 4M11 4l3 4-3 4M9 2l-2 12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
            <h2 id="analyzer-title" className="panel-title">Code Input</h2>
          </div>
          <div className="panel-meta">
            <span className="meta-chip">{currentLanguage?.label ?? language}</span>
            <span className="meta-chip">{code.trim().length.toLocaleString()} chars</span>
          </div>
        </div>

        <textarea
          aria-label="Source code"
          className="code-input"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="// Paste your source code here…"
          spellCheck={false}
        />

        <div className="composer-bar">
          <div className="composer-tools">
            <button
              type="button"
              className="tool-btn"
              title="Clear editor"
              aria-label="Clear editor"
              onClick={() => setCode("")}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
              Clear
            </button>
          </div>
          <button className="run-button" type="submit" disabled={!canSubmit}>
            {loading ? (
              <>
                <span className="run-spinner" aria-hidden="true" />
                Analyzing…
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="M3 2l9 5-9 5V2z" fill="currentColor" />
                </svg>
                Run Analysis
              </>
            )}
          </button>
        </div>
      </section>

      {/* ── Settings panel ── */}
      <aside
        className="studio-panel settings-panel"
        id="run-settings"
        aria-label="Run settings"
      >
        <div className="panel-topbar">
          <span className="panel-icon" aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="2.2" stroke="currentColor" strokeWidth="1.6" />
              <path d="M8 1v1.5M8 13.5V15M1 8h1.5M13.5 8H15M2.93 2.93l1.06 1.06M12.01 12.01l1.06 1.06M2.93 13.07l1.06-1.06M12.01 3.99l1.06-1.06" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </span>
          <h2 className="panel-title">Configuration</h2>
        </div>

        <div className="settings-body">
          <label className="field-stack">
            <span className="field-label">Model</span>
            <input className="field-input" value="Azure Foundry / GPT-4o" readOnly />
          </label>

          <label className="field-stack">
            <span className="field-label">Language</span>
            <select
              className="field-input"
              aria-label="Programming language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {SUPPORTED_LANGUAGES.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </label>

          <label className="field-stack">
            <span className="field-label">Title <span className="field-optional">(optional)</span></span>
            <input
              className="field-input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Auth helper"
            />
          </label>

          <label className="field-stack">
            <span className="field-label">Context <span className="field-optional">(optional)</span></span>
            <textarea
              className="field-input context-input"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Backend API, utility function, UI component…"
            />
          </label>

          <div className="settings-toggles" aria-label="Analysis options">
            <div className="toggle-row">
              <span>Static rules</span>
              <span className="toggle-on">On</span>
            </div>
            <div className="toggle-row">
              <span>LLM review</span>
              <span className="toggle-on">On</span>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Result panel ── */}
      <section
        className="studio-panel result-panel"
        id="review-output"
        aria-label="Review result"
      >
        <div className="panel-topbar">
          <div className="panel-topbar-left">
            <span className="panel-icon" aria-hidden="true">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M2 4h12M2 8h8M2 12h5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
            </span>
            <h2 className="panel-title">Review Output</h2>
          </div>
          {review ? (
            <div className="score-badge" aria-label={`Overall score: ${review.overallScore}`}>
              <span className="score-value">{review.overallScore}</span>
              <span className="score-label">/ 100</span>
            </div>
          ) : (
            <div className="score-badge score-badge--empty" aria-hidden="true">
              <span className="score-value">--</span>
            </div>
          )}
        </div>

        <div className="result-body">
          {loading && (
            <div className="empty-state">
              <span className="loading-ring" aria-hidden="true" />
              <span>Running analysis…</span>
            </div>
          )}

          {!loading && error && (
            <div className="error-state" role="alert">
              <strong>Error:</strong> {error.message}
            </div>
          )}

          {!loading && !error && !review && (
            <div className="empty-state">
              <svg width="40" height="40" viewBox="0 0 40 40" fill="none" aria-hidden="true" className="empty-icon">
                <circle cx="20" cy="20" r="18" stroke="currentColor" strokeWidth="1.5" strokeDasharray="4 3" />
                <path d="M14 20h12M20 14v12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
              <p>Paste code and click <strong>Run Analysis</strong> to get started.</p>
            </div>
          )}

          {!loading && !error && review && (
            <ReviewSummary
              review={review}
              issueCount={issueCount}
              issues={allIssues}
              onApplyCorrection={setCode}
            />
          )}
        </div>
      </section>
    </form>
  );
}

/* ── Sub-components ── */

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
        <div className="metric-card">
          <dt>Issues found</dt>
          <dd className={issueCount > 0 ? "metric-warn" : "metric-ok"}>{issueCount}</dd>
        </div>
        <div className="metric-card">
          <dt>Language</dt>
          <dd>{review.language}</dd>
        </div>
        <div className="metric-card">
          <dt>Bugs</dt>
          <dd className={review.bugs.length > 0 ? "metric-warn" : "metric-ok"}>{review.bugs.length}</dd>
        </div>
        <div className="metric-card">
          <dt>Security</dt>
          <dd className={review.securityIssues.length > 0 ? "metric-critical" : "metric-ok"}>{review.securityIssues.length}</dd>
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
    <section className="result-section">
      <div className="section-title-row">
        <h3>Corrected code</h3>
        {code && (
          <button
            type="button"
            className="apply-btn"
            onClick={() => onApplyCorrection(code)}
          >
            ↑ Apply correction
          </button>
        )}
      </div>
      {code ? (
        <pre className="code-block"><code>{code}</code></pre>
      ) : (
        <p className="muted-text">No corrected snippet returned.</p>
      )}
    </section>
  );
}

function IssueGroup({ issues }: { issues: Issue[] }) {
  return (
    <section className="result-section">
      <h3>Findings</h3>
      {issues.length === 0 ? (
        <p className="muted-text">No findings — looks clean.</p>
      ) : (
        <ul className="issue-list">
          {issues.map((issue) => {
            const meta = SEVERITY_META[issue.severity] ?? SEVERITY_META.LOW;
            return (
              <li key={`${issue.title}-${issue.line ?? "x"}`} className="issue-item">
                <div className="issue-header">
                  <strong className="issue-title">{issue.title}</strong>
                  <span className={`sev-badge ${meta.className}`}>{meta.label}</span>
                  {issue.line != null && (
                    <span className="issue-line">line {issue.line}</span>
                  )}
                </div>
                <p className="issue-explanation">{issue.explanation}</p>
                {issue.suggestion && (
                  <p className="issue-suggestion">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" aria-hidden="true" className="issue-suggestion-icon">
                      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.8" />
                      <path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                    {issue.suggestion}
                  </p>
                )}
              </li>
            );
          })}
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
        <p className="muted-text">No suggestions returned.</p>
      ) : (
        <ul className="issue-list">
          {suggestions.map((s) => (
            <li key={s.title} className="issue-item suggestion-item">
              <strong className="issue-title">{s.title}</strong>
              <p className="issue-explanation">{s.explanation}</p>
              {s.improvedCode && (
                <pre className="code-block code-block--sm"><code>{s.improvedCode}</code></pre>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

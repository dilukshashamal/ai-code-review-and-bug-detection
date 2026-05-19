export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type CodeInput = {
  title?: string | null;
  language: string;
  code: string;
  context?: string | null;
};

export type Issue = {
  title: string;
  severity: Severity;
  line?: number | null;
  explanation: string;
  suggestion: string;
};

export type Suggestion = {
  title: string;
  explanation: string;
  improvedCode?: string | null;
};

export type CodeReview = {
  id: string;
  title?: string | null;
  language: string;
  submittedCode: string;
  overallScore: number;
  summary: string;
  bugs: Issue[];
  securityIssues: Issue[];
  performanceIssues: Issue[];
  suggestions: Suggestion[];
  createdAt: string;
};

export type AnalyzeCodeData = {
  analyzeCode: CodeReview;
};

export type AnalyzeCodeVariables = {
  input: CodeInput;
};

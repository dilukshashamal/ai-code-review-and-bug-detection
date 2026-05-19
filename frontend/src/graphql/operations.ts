import { gql } from "@apollo/client";

export const ANALYZE_CODE_MUTATION = gql`
  mutation AnalyzeCode($input: CodeInput!) {
    analyzeCode(input: $input) {
      id
      title
      language
      submittedCode
      overallScore
      summary
      bugs {
        title
        severity
        line
        explanation
        suggestion
      }
      securityIssues {
        title
        severity
        line
        explanation
        suggestion
      }
      performanceIssues {
        title
        severity
        line
        explanation
        suggestion
      }
      suggestions {
        title
        explanation
        improvedCode
      }
      createdAt
    }
  }
`;

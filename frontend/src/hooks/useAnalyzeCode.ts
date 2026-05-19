import { useMutation } from "@apollo/client/react";

import { ANALYZE_CODE_MUTATION } from "../graphql/operations";
import type { AnalyzeCodeData, AnalyzeCodeVariables } from "../graphql/types";

export function useAnalyzeCode() {
  return useMutation<AnalyzeCodeData, AnalyzeCodeVariables>(ANALYZE_CODE_MUTATION);
}

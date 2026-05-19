export type SupportedLanguage = {
  label: string;
  value: string;
};

export const SUPPORTED_LANGUAGES: SupportedLanguage[] = [
  { label: "TypeScript", value: "typescript" },
  { label: "JavaScript", value: "javascript" },
  { label: "Python", value: "python" },
  { label: "Java", value: "java" },
  { label: "Go", value: "go" },
  { label: "C++", value: "cpp" },
];

import type { ReactNode } from "react";

type AppLayoutProps = {
  children: ReactNode;
};

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Code quality workspace</p>
          <h1>AI Code Review Platform</h1>
        </div>
        <div className="status-pill">MVP foundation</div>
      </header>
      <main>{children}</main>
    </div>
  );
}

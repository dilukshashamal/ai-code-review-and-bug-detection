import type { ReactNode } from "react";

type AppLayoutProps = {
  children: ReactNode;
};

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Workspace navigation">
        <div className="brand-mark" aria-hidden="true">
          CR
        </div>
        <nav className="sidebar-nav">
          <a className="nav-item active" href="#analyzer-title" aria-current="page">
            <span aria-hidden="true">A</span>
            <span>Analyzer</span>
          </a>
          <a className="nav-item" href="#review-output">
            <span aria-hidden="true">R</span>
            <span>Reports</span>
          </a>
          <a className="nav-item" href="#run-settings">
            <span aria-hidden="true">S</span>
            <span>Settings</span>
          </a>
        </nav>
      </aside>
      <div className="workspace-shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">Code quality workspace</p>
            <h1>AI Code Review Platform</h1>
          </div>
          <div className="status-pill">Azure Foundry</div>
        </header>
        <main>{children}</main>
      </div>
    </div>
  );
}

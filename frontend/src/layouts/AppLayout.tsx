import type { ReactNode } from "react";

type AppLayoutProps = {
  children: ReactNode;
  onHome: () => void;
};

const NAV_ITEMS = [
  {
    id: "analyzer",
    label: "Analyzer",
    href: "#analyzer-title",
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
        <path d="M3 4h12M3 9h8M3 14h5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        <circle cx="14" cy="13" r="2.5" stroke="currentColor" strokeWidth="1.6" />
        <path d="M15.8 14.8l1.7 1.7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    id: "reports",
    label: "Reports",
    href: "#review-output",
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
        <rect x="2" y="2" width="14" height="14" rx="2" stroke="currentColor" strokeWidth="1.6" />
        <path d="M5 9l2.5 2.5L13 6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    id: "settings",
    label: "Settings",
    href: "#run-settings",
    icon: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
        <circle cx="9" cy="9" r="2.5" stroke="currentColor" strokeWidth="1.6" />
        <path d="M9 1v2M9 15v2M1 9h2M15 9h2M3.22 3.22l1.42 1.42M13.36 13.36l1.42 1.42M3.22 14.78l1.42-1.42M13.36 4.64l1.42-1.42" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    ),
  },
];

export function AppLayout({ children, onHome }: AppLayoutProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Workspace navigation">
        {/* Brand */}
        <button
          className="sidebar-brand"
          onClick={onHome}
          aria-label="SYNAPSE — back to home"
          title="Back to home"
        >
          <img src="/images/logo.png" alt="SYNAPSE logo" className="sidebar-brand-logo" />
          <span className="sidebar-brand-name">SYNAPSE</span>
        </button>

        {/* Nav */}
        <nav className="sidebar-nav" aria-label="Main navigation">
          {NAV_ITEMS.map((item, i) => (
            <a
              key={item.id}
              className={`nav-item${i === 0 ? " active" : ""}`}
              href={item.href}
              aria-current={i === 0 ? "page" : undefined}
            >
              <span className="nav-item-icon">{item.icon}</span>
              <span className="nav-item-label">{item.label}</span>
            </a>
          ))}
        </nav>

        {/* Model badge at bottom */}
        <div className="sidebar-footer">
          <div className="model-badge" title="Powered by Azure AI Foundry">
            <span className="model-badge-dot" aria-hidden="true" />
            <span>Azure Foundry</span>
          </div>
        </div>
      </aside>

      <div className="workspace-shell">
        {/* Top bar */}
        <header className="topbar">
          <div className="topbar-left">
            <p className="eyebrow">Code quality workspace</p>
            <h1 className="topbar-title">Code Analyzer</h1>
          </div>
          <div className="topbar-right">
            <div className="status-pill">
              <span className="status-dot" aria-hidden="true" />
              Live
            </div>
          </div>
        </header>

        <main>{children}</main>
      </div>
    </div>
  );
}

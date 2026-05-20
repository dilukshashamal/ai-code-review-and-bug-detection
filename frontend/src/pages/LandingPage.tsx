import type { ReactNode } from "react";

type LandingPageProps = {
  onEnter: () => void;
};

/* ── SVG icon components ── */
function IconBolt() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M13 2L4.5 13.5H11L10 22L19.5 10.5H13L13 2Z"
        stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconShield() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 2L4 6V12C4 16.4 7.4 20.5 12 22C16.6 20.5 20 16.4 20 12V6L12 2Z"
        stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 12l2 2 4-4"
        stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconBrain() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M9.5 2C7 2 5 4 5 6.5C3.3 7.2 2 8.9 2 11C2 13.2 3.4 15 5.3 15.6C5.1 16 5 16.5 5 17C5 19.2 6.8 21 9 21H15C17.2 21 19 19.2 19 17C19 16.5 18.9 16 18.7 15.6C20.6 15 22 13.2 22 11C22 8.9 20.7 7.2 19 6.5C19 4 17 2 14.5 2C13.4 2 12.4 2.4 11.7 3.1C11 2.4 10.3 2 9.5 2Z"
        stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 6v6M9 9h6"
        stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function IconWand() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M15 4l5 5L8 21l-5-5L15 4Z"
        stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M19 2l1 1M21 6l1-1M17 6l1 1M3 12l1 1M5 8l1 1"
        stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function IconSynapse() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8" />
      <circle cx="4"  cy="6"  r="2" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="20" cy="6"  r="2" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="4"  cy="18" r="2" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="20" cy="18" r="2" stroke="currentColor" strokeWidth="1.6" />
      <path d="M6 7l4 4M18 7l-4 4M6 17l4-4M18 17l-4-4"
        stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

type Feature = {
  icon: ReactNode;
  title: string;
  desc: string;
};

const FEATURES: Feature[] = [
  {
    icon: <IconBolt />,
    title: "Instant Analysis",
    desc: "Paste code and get a full review in seconds — bugs, security holes, and performance issues surfaced immediately.",
  },
  {
    icon: <IconShield />,
    title: "Security Scanning",
    desc: "Detect injection vulnerabilities, insecure patterns, and OWASP-class issues before they reach production.",
  },
  {
    icon: <IconBrain />,
    title: "Deep LLM Review",
    desc: "Powered by Azure AI Foundry. Context-aware suggestions that understand your code's intent, not just its syntax.",
  },
  {
    icon: <IconWand />,
    title: "Auto Correction",
    desc: "Get a corrected version of your code with one click — apply it directly back to the editor.",
  },
];

const STATS = [
  { value: "6+", label: "Languages" },
  { value: "3", label: "Review layers" },
  { value: "<2s", label: "Avg response" },
  { value: "100%", label: "AI-powered" },
];

export function LandingPage({ onEnter }: LandingPageProps) {
  return (
    <div className="landing">
      {/* ── Ambient background orbs ── */}
      <div className="landing-orb landing-orb--1" aria-hidden="true" />
      <div className="landing-orb landing-orb--2" aria-hidden="true" />
      <div className="landing-orb landing-orb--3" aria-hidden="true" />

      {/* ── Nav bar ── */}
      <header className="landing-nav">
        <div className="landing-nav-brand">
          <img src="/images/logo.png" alt="SYNAPSE logo" className="landing-nav-logo" />
          <span className="landing-nav-name">SYNAPSE</span>
        </div>
        <button className="landing-nav-cta" onClick={onEnter}>
          Open Workspace
        </button>
      </header>

      {/* ── Hero ── */}
      <section className="landing-hero" aria-labelledby="hero-heading">

        {/* Big logo — main visual anchor */}
        <div className="landing-hero-logo-wrap" aria-hidden="true">
          <div className="landing-hero-logo-glow" />
          <img
            src="/images/logo.png"
            alt="SYNAPSE"
            className="landing-hero-logo"
          />
        </div>

        <div className="landing-hero-badge">
          <span className="badge-dot" aria-hidden="true" />
          AI-Powered Code Intelligence
        </div>

        <h1 id="hero-heading" className="landing-hero-title">
          Code smarter.<br />
          <span className="landing-hero-gradient">Ship with confidence.</span>
        </h1>

        <p className="landing-hero-sub">
          SYNAPSE reviews your code in real time - catching bugs, security vulnerabilities,
          and performance issues before they reach production. Powered by Azure AI Foundry.
        </p>

        <div className="landing-hero-actions">
          <button className="btn-primary-lg" onClick={onEnter}>
            Start reviewing
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
          <a
            className="btn-ghost-lg"
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
          >
            View on GitHub
          </a>
        </div>

        {/* Stats row */}
        <dl className="landing-stats">
          {STATS.map((s) => (
            <div key={s.label} className="landing-stat">
              <dt className="landing-stat-value">{s.value}</dt>
              <dd className="landing-stat-label">{s.label}</dd>
            </div>
          ))}
        </dl>
      </section>

      {/* ── Feature grid ── */}
      <section className="landing-features" aria-labelledby="features-heading">
        <p className="landing-section-eyebrow">What SYNAPSE does</p>
        <h2 id="features-heading" className="landing-section-title">
          Everything you need to write better code
        </h2>
        <div className="landing-feature-grid">
          {FEATURES.map((f) => (
            <article key={f.title} className="feature-card">
              <div className="feature-card-icon">{f.icon}</div>
              <h3 className="feature-card-title">{f.title}</h3>
              <p className="feature-card-desc">{f.desc}</p>
            </article>
          ))}
        </div>
      </section>

      {/* ── CTA banner ── */}
      <section className="landing-cta-banner" aria-labelledby="cta-heading">
        <div className="landing-cta-inner">
          <h2 id="cta-heading" className="landing-cta-title">
            Ready to review your first file?
          </h2>
          <p className="landing-cta-sub">
            No setup. No account. Paste your code and let SYNAPSE do the rest.
          </p>
          <button className="btn-primary-lg" onClick={onEnter}>
            Open the workspace
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
              <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <div className="landing-footer-brand">
          <span className="landing-footer-icon" aria-hidden="true">
            <IconSynapse />
          </span>
          <span>SYNAPSE</span>
        </div>
        <p className="landing-footer-copy">© 2026 SYNAPSE. AI code review platform.</p>
      </footer>
    </div>
  );
}

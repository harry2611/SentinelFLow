import { NavLink, Outlet } from "react-router-dom";

const navigation = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/tasks", label: "Workflows" },
  { to: "/review", label: "Review Queue" },
  { to: "/integrations", label: "Integrations" },
  { to: "/demo", label: "Demo Lab" },
];

export default function AppShell() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">SF</div>
          <div>
            <p className="brand-eyebrow">Multi-Agent Ops System</p>
            <h1>SentinelFlow</h1>
          </div>
        </div>
        <nav className="nav-list">
          {navigation.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <p>Shared state, memory retrieval, review gates, and operational feedback loops.</p>
        </div>
      </aside>

      <main className="content">
        <header className="topbar">
          <div>
            <p className="topbar-eyebrow">Portfolio-grade operations automation</p>
            <h2>Agentic workflow command center</h2>
          </div>
          <div className="topbar-badge">FastAPI + React + pgvector + Redis</div>
        </header>
        <Outlet />
      </main>
    </div>
  );
}


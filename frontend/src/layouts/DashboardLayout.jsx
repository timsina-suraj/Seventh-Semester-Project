import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

const NAV_BY_ROLE = {
  admin: [
    { to: "/", label: "🏠 Dashboard", end: true },
    { to: "/analytics", label: "📊 Analytics" },
    { to: "/risk-map", label: "🗺️ Nepal Risk Map" },
    { to: "/alerts", label: "🔔 Alerts" },
    { to: "/patients", label: "🧑‍⚕️ Patients" },
    { to: "/doctors", label: "👨‍⚕️ Doctors" },
    { to: "/receptionists", label: "💁 Receptionists" },
    { to: "/appointments", label: "📅 Appointments" },
    { to: "/pharmacy", label: "💊 Pharmacy" },
    { to: "/users", label: "👥 Users" },
  ],
  doctor: [
    { to: "/", label: "🏠 Dashboard", end: true },
    { to: "/patients", label: "🧑‍⚕️ Patients" },
    { to: "/diagnosis", label: "🔬 Diagnosis & Record" },
    { to: "/appointments", label: "📅 Appointments" },
  ],
  receptionist: [
    { to: "/", label: "🏠 Dashboard", end: true },
    { to: "/patients", label: "🧑‍⚕️ Patients" },
    { to: "/patients/register", label: "➕ Register Patient" },
    { to: "/appointments", label: "📅 Appointments" },
    { to: "/appointments/book", label: "📆 Book Appointment" },
    { to: "/pharmacy", label: "💊 Pharmacy" },
  ],
  patient: [
    { to: "/", label: "🏠 Dashboard", end: true },
    { to: "/my-profile", label: "👤 My Profile" },
    { to: "/my-appointments", label: "📅 My Appointments" },
    { to: "/my-reports", label: "📋 My Reports" },
  ],
};

const ROLE_LABELS = {
  admin: "Administrator",
  doctor: "Doctor",
  receptionist: "Receptionist",
  patient: "Patient",
};

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const items = NAV_BY_ROLE[user.role] || [];

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      {/* ── Top Header ─────────────────────────────────── */}
      <header className="top-header">
        <div className="top-header-brand">
          <span className="top-header-logo">🛡️</span>
          <span className="top-header-name">MediShield</span>
          <span className="top-header-tagline">Intelligent Hospital Management System</span>
        </div>
        <div className="top-header-user">
          <span className="top-header-role-badge">{ROLE_LABELS[user.role] || user.role}</span>
          <span className="top-header-username">{user.email}</span>
          <button className="top-header-btn" onClick={() => navigate("/change-password")}>
            🔑 Change Password
          </button>
          <button className="top-header-btn danger" onClick={handleLogout}>
            ⏻ Log out
          </button>
        </div>
      </header>

      {/* ── Body: Sidebar + Main ───────────────────────── */}
      <div className="body-row">
        <aside className="sidebar">
          <nav className="sidebar-nav">
            {items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => (isActive ? "active" : "")}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <div className="main-wrapper">
          <main className="main-content">
            <Outlet />
          </main>

          {/* ── Footer ──────────────────────────────────── */}
          <footer className="app-footer">
            <div className="app-footer-inner">
              <span>© {new Date().getFullYear()} <strong>MediShield</strong> — Intelligent Hospital Management System</span>
              <span className="app-footer-divider">|</span>
              <span>Built for dengue surveillance &amp; patient care in Nepal</span>
              <span className="app-footer-divider">|</span>
              <span>All rights reserved</span>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}

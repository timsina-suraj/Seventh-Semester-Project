import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bar, BarChart, CartesianGrid, Line, LineChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import * as api from "../../api/endpoints";
import { useAuth } from "../../auth/AuthContext.jsx";

const STAT_CONFIG = [
  {
    key: "total_patients",
    label: "Total Patients",
    icon: "🧑‍⚕️",
    color: "#2563eb",
    bg: "#eff6ff",
    border: "#bfdbfe",
    to: "/patients",
  },
  {
    key: "dengue_cases_flagged",
    label: "Dengue Cases Flagged",
    icon: "🦟",
    color: "#dc2626",
    bg: "#fff5f5",
    border: "#fecaca",
    to: "/alerts",
  },
  {
    key: "available_doctors",
    label: "Total Doctors",
    icon: "👨‍⚕️",
    color: "#059669",
    bg: "#f0fdf4",
    border: "#bbf7d0",
    to: "/doctors",
  },
  {
    key: "total_appointments",
    label: "Total Appointments",
    icon: "📅",
    color: "#7c3aed",
    bg: "#faf5ff",
    border: "#ddd6fe",
    to: "/appointments",
  },
  {
    key: "total_lab_results",
    label: "Lab Results",
    icon: "🧪",
    color: "#0891b2",
    bg: "#ecfeff",
    border: "#a5f3fc",
    to: "/patients",
  },
  {
    key: "low_stock_items",
    label: "Low Stock Items",
    icon: "💊",
    color: "#d97706",
    bg: "#fffbeb",
    border: "#fde68a",
    to: "/pharmacy",
  },
  {
    key: "open_alerts",
    label: "Open Alerts",
    icon: "🔔",
    color: "#dc2626",
    bg: "#fff5f5",
    border: "#fecaca",
    to: "/alerts",
  },
];

const QUICK_LINKS = [
  { label: "➕ Register Patient", to: "/patients/register", color: "#2563eb" },
  { label: "📅 Book Appointment", to: "/appointments/book", color: "#7c3aed" },
  { label: "👥 Manage Users", to: "/users", color: "#059669" },
  { label: "📊 Analytics", to: "/analytics", color: "#0891b2" },
  { label: "🗺️ Risk Map", to: "/risk-map", color: "#d97706" },
  { label: "🔔 View Alerts", to: "/alerts", color: "#dc2626" },
];

export default function AdminDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getHospitalStats()
      .then((res) => setStats(res.data))
      .catch(() => setError("Could not load hospital statistics."));
  }, []);

  const now = new Date();
  const greeting =
    now.getHours() < 12 ? "Good morning" : now.getHours() < 17 ? "Good afternoon" : "Good evening";

  return (
    <div>
      {/* ── Greeting ── */}
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div>
          <h1>{greeting}, {user.fullName || user.email} 👋</h1>
        </div>
        <div style={{ fontSize: 13, color: "var(--color-text-muted)" }}>
          {now.toLocaleDateString("en-NP", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
        </div>
      </div>

      {error && <div className="error-text" style={{ marginBottom: 16 }}>{error}</div>}

      {/* ── Stat Tiles ── */}
      {stats && (
        <div className="stat-grid" style={{ marginBottom: 28 }}>
          {STAT_CONFIG.map(({ key, label, icon, color, bg, border, to }) => (
            <div
              key={key}
              className="stat-tile"
              onClick={() => navigate(to)}
              style={{
                background: bg,
                borderColor: border,
                cursor: "pointer",
                transition: "transform 0.15s, box-shadow 0.15s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow = "0 6px 20px rgba(0,0,0,0.10)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "";
                e.currentTarget.style.boxShadow = "";
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div className="label" style={{ color }}>{label}</div>
                <span style={{ fontSize: 22 }}>{icon}</span>
              </div>
              <div className="value" style={{ color, marginTop: 8 }}>{stats[key]}</div>
            </div>
          ))}
        </div>
      )}

      {/* ── Quick Actions ── */}
      <div style={{ marginBottom: 28 }}>
        <div className="section-title">Quick Actions</div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {QUICK_LINKS.map(({ label, to, color }) => (
            <button
              key={to}
              className="btn"
              style={{ background: color, fontSize: 13, padding: "9px 16px" }}
              onClick={() => navigate(to)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Activity Charts ── */}
      <div className="grid-2">
        <div className="card">
          <div className="section-title">Appointments — Last 14 Days</div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={stats?.appointments_trend ?? []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" fontSize={11} />
              <YAxis fontSize={11} allowDecimals={false} />
              <Tooltip />
              <Line type="monotone" dataKey="count" name="Appointments" stroke="#7c3aed" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="section-title">New Registrations — Last 30 Days</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats?.registrations_trend ?? []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" fontSize={11} />
              <YAxis fontSize={11} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" name="Registrations" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card" style={{ gridColumn: "1 / -1" }}>
          <div className="section-title">Hospital Highlights</div>
          {stats ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={highlightStyle("#eff6ff", "#bfdbfe")}>
                <span style={{ color: "#2563eb", fontWeight: 700, fontSize: 20 }}>{stats.total_patients}</span>
                <span style={{ color: "#2563eb", fontSize: 13 }}>patients registered</span>
              </div>
              <div style={highlightStyle("#fff5f5", "#fecaca")}>
                <span style={{ color: "#dc2626", fontWeight: 700, fontSize: 20 }}>{stats.dengue_cases_flagged}</span>
                <span style={{ color: "#dc2626", fontSize: 13 }}>dengue cases flagged by AI</span>
              </div>
              <div style={highlightStyle("#f0fdf4", "#bbf7d0")}>
                <span style={{ color: "#059669", fontWeight: 700, fontSize: 20 }}>{stats.available_doctors}</span>
                <span style={{ color: "#059669", fontSize: 13 }}>doctors on staff</span>
              </div>
              <div style={highlightStyle("#faf5ff", "#ddd6fe")}>
                <span style={{ color: "#7c3aed", fontWeight: 700, fontSize: 20 }}>{stats.total_appointments}</span>
                <span style={{ color: "#7c3aed", fontSize: 13 }}>total appointments booked</span>
              </div>
            </div>
          ) : (
            <div className="empty-state">Loading…</div>
          )}
        </div>
      </div>
    </div>
  );
}

function highlightStyle(bg, border) {
  return {
    background: bg,
    border: `1px solid ${border}`,
    borderRadius: 8,
    padding: "10px 14px",
    display: "flex",
    alignItems: "center",
    gap: 10,
  };
}

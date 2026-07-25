import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../../api/endpoints";
import { useAuth } from "../../auth/AuthContext.jsx";

export default function ReceptionistDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [recentPatients, setRecentPatients] = useState([]);

  useEffect(() => {
    api.getHospitalStats().then((res) => setStats(res.data)).catch(() => {});
    api.listPatients().then((res) => {
      // Show the 5 most recently registered (last in list)
      setRecentPatients([...res.data].reverse().slice(0, 5));
    }).catch(() => {});
  }, []);

  const quickActions = [
    { label: "➕ Register New Patient", to: "/patients/register", color: "#2563eb" },
    { label: "📅 Book Appointment", to: "/appointments/book", color: "#7c3aed" },
    { label: "👥 View All Patients", to: "/patients", color: "#0891b2" },
    { label: "📋 View All Appointments", to: "/appointments", color: "#059669" },
    { label: "💊 Pharmacy Inventory", to: "/pharmacy", color: "#d97706" },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Welcome, {user.email} 👋</h1>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="section-title">Quick Actions</div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 28 }}>
        {quickActions.map((a) => (
          <button
            key={a.to}
            className="btn"
            style={{ background: a.color, fontSize: 14, padding: "10px 18px" }}
            onClick={() => navigate(a.to)}
          >
            {a.label}
          </button>
        ))}
      </div>

      {/* Stats */}
      {stats && (
        <>
          <div className="section-title">Hospital Overview</div>
          <div className="stat-grid" style={{ marginBottom: 28 }}>
            <div className="stat-tile">
              <div className="label">Total Patients</div>
              <div className="value">{stats.total_patients}</div>
            </div>
            <div className="stat-tile">
              <div className="label">Total Appointments</div>
              <div className="value">{stats.total_appointments}</div>
            </div>
            <div className="stat-tile">
              <div className="label">Available Doctors</div>
              <div className="value">{stats.available_doctors}</div>
            </div>
            <div className="stat-tile">
              <div className="label" style={{ color: "#dc2626" }}>Low Stock Items</div>
              <div className="value" style={{ color: "#dc2626" }}>{stats.low_stock_items}</div>
            </div>
          </div>
        </>
      )}

      {/* Recently Registered Patients */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <div className="section-title" style={{ margin: 0 }}>Recently Registered Patients</div>
          <button className="btn secondary" style={{ fontSize: 13 }} onClick={() => navigate("/patients")}>
            View all →
          </button>
        </div>
        {recentPatients.length === 0 ? (
          <div className="empty-state">No patients registered yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Age</th>
                <th>Gender</th>
                <th>District</th>
                <th>Login</th>
              </tr>
            </thead>
            <tbody>
              {recentPatients.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td>{p.age}</td>
                  <td>{p.gender}</td>
                  <td>{p.district}</td>
                  <td>
                    {p.login_email
                      ? `${p.login_email} (${p.must_change_password ? "⚠ temp" : "✅ set"})`
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

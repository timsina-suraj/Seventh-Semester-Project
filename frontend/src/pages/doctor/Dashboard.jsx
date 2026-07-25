import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../../api/endpoints";
import { useAuth } from "../../auth/AuthContext.jsx";

export default function DoctorDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.listPatients().then((res) => setPatients(res.data)).catch(() => {});
    api.listAppointments().then((res) => setAppointments(res.data)).catch(() => {});
    api.getHospitalStats().then((res) => setStats(res.data)).catch(() => {});
  }, []);

  const upcomingAppointments = appointments
    .filter((a) => a.status === "scheduled")
    .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
    .slice(0, 5);

  const patientMap = Object.fromEntries(patients.map((p) => [p.id, p.name]));

  const quickActions = [
    { label: "🔬 Fill Diagnosis & Record", to: "/diagnosis", color: "#7c3aed" },
    { label: "🧑‍⚕️ View Patients", to: "/patients", color: "#2563eb" },
    { label: "📅 My Appointments", to: "/appointments", color: "#059669" },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Welcome, Dr. {user.email} 👨‍⚕️</h1>
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
          <div className="section-title">Today at a Glance</div>
          <div className="stat-grid" style={{ marginBottom: 28 }}>
            <div className="stat-tile">
              <div className="label">Total Patients</div>
              <div className="value">{stats.total_patients}</div>
            </div>
            <div className="stat-tile">
              <div className="label">Dengue Cases Flagged</div>
              <div className="value" style={{ color: "#dc2626" }}>{stats.dengue_cases_flagged}</div>
            </div>
            <div className="stat-tile">
              <div className="label">Total Appointments</div>
              <div className="value">{stats.total_appointments}</div>
            </div>
          </div>
        </>
      )}

      {/* Upcoming appointments */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <div className="section-title" style={{ margin: 0 }}>Upcoming Appointments</div>
          <button className="btn secondary" style={{ fontSize: 13 }} onClick={() => navigate("/appointments")}>
            View all →
          </button>
        </div>
        {upcomingAppointments.length === 0 ? (
          <div className="empty-state">No upcoming scheduled appointments.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>When</th>
                <th>Patient</th>
                <th>Reason</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {upcomingAppointments.map((a) => (
                <tr key={a.id}>
                  <td>{new Date(a.scheduled_at).toLocaleString()}</td>
                  <td>{patientMap[a.patient_id] || `#${a.patient_id}`}</td>
                  <td>{a.reason || "—"}</td>
                  <td>
                    <span className="badge status-open">{a.status}</span>
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

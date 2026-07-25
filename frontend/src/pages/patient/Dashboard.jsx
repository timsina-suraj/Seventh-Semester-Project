import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../../api/endpoints";
import { useAuth } from "../../auth/AuthContext.jsx";

export default function PatientDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [records, setRecords] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getMyPatientRecord()
      .then((res) => setPatient(res.data))
      .catch(() => setError("No patient record linked to your account yet — contact reception."));
    api.listAppointments()
      .then((res) => setAppointments(res.data))
      .catch(() => {});
    api.listMedicalRecords()
      .then((res) => setRecords(res.data))
      .catch(() => {});
  }, []);

  const upcomingAppointments = appointments
    .filter((a) => a.status === "scheduled")
    .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at));

  const latestRecord = records[records.length - 1];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Welcome, {patient?.name || user.email} 🙋</h1>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: "#fca5a5", background: "#fff5f5", marginBottom: 20 }}>
          <p style={{ color: "#dc2626", margin: 0 }}>⚠ {error}</p>
        </div>
      )}

      {/* Quick Actions */}
      <div className="section-title">Quick Actions</div>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 24 }}>
        <button
          className="btn"
          style={{ background: "#dc2626", fontSize: 14, padding: "10px 18px" }}
          onClick={() => navigate("/dengue-check")}
        >
          🩺 Self Dengue Check
        </button>
      </div>

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Profile card */}
        <div className="card">
          <div className="section-title">My Profile</div>
          {patient ? (
            <table>
              <tbody>
                <tr><td style={{ color: "var(--color-text-muted)", width: 120 }}>Name</td><td>{patient.name}</td></tr>
                <tr><td style={{ color: "var(--color-text-muted)" }}>Age</td><td>{patient.age}</td></tr>
                <tr><td style={{ color: "var(--color-text-muted)" }}>Gender</td><td>{patient.gender}</td></tr>
                <tr><td style={{ color: "var(--color-text-muted)" }}>District</td><td>{patient.district}</td></tr>
                <tr><td style={{ color: "var(--color-text-muted)" }}>Phone</td><td>{patient.phone || "—"}</td></tr>
                <tr><td style={{ color: "var(--color-text-muted)" }}>Address</td><td>{patient.address || "—"}</td></tr>
              </tbody>
            </table>
          ) : (
            <div className="empty-state">Profile not loaded.</div>
          )}
        </div>

        {/* Latest Medical Record */}
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <div className="section-title" style={{ margin: 0 }}>Latest Medical Record</div>
            <button className="btn secondary" style={{ fontSize: 13 }} onClick={() => navigate("/my-reports")}>
              All records →
            </button>
          </div>
          {latestRecord ? (
            <div>
              <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginBottom: 8 }}>
                {new Date(latestRecord.date).toLocaleString()}
              </p>
              <p><strong>Symptoms:</strong> {latestRecord.symptoms || "—"}</p>
              <p><strong>Medical History:</strong> {latestRecord.medical_history || "—"}</p>
              <p><strong>Clinical &amp; Medication History:</strong> {latestRecord.clinical_history || "—"}</p>
              <p><strong>Diagnosis:</strong> {latestRecord.diagnosis || "—"}</p>
              <p><strong>Test Results:</strong> {latestRecord.lab_result || "—"}</p>
              <p><strong>Tests Prescribed:</strong> {latestRecord.prescribed_tests || "—"}</p>
              <p><strong>Medicines Prescribed:</strong> {latestRecord.prescription || "—"}</p>
              <p><strong>Doctor Progress Note:</strong> {latestRecord.doctor_note || "—"}</p>
              {latestRecord.ml_dengue_predicted !== null && (
                <p>
                  <strong>AI Screening:</strong>{" "}
                  <span style={{ color: latestRecord.ml_dengue_predicted ? "#dc2626" : "#16a34a", fontWeight: 700 }}>
                    {latestRecord.ml_dengue_predicted ? "🔴 Dengue Positive" : "🟢 Dengue Negative"}
                  </span>{" "}
                  ({(latestRecord.ml_dengue_probability * 100).toFixed(1)}% confidence)
                </p>
              )}
            </div>
          ) : (
            <div className="empty-state">No medical records on file yet.</div>
          )}
        </div>
      </div>

      {/* Upcoming Appointments */}
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <div className="section-title" style={{ margin: 0 }}>My Upcoming Appointments</div>
          <button className="btn secondary" style={{ fontSize: 13 }} onClick={() => navigate("/my-appointments")}>
            All appointments →
          </button>
        </div>
        {upcomingAppointments.length === 0 ? (
          <div className="empty-state">No upcoming appointments scheduled.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>When</th>
                <th>Reason</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {upcomingAppointments.map((a) => (
                <tr key={a.id}>
                  <td>{new Date(a.scheduled_at).toLocaleString()}</td>
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

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
    .filter((a) => a.status === "Pending" || a.status === "Confirmed")
    .sort((a, b) => new Date(a.appointment_date) - new Date(b.appointment_date));

  const latestRecord = records[records.length - 1];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Welcome, {patient?.full_name || user.email} 🙋</h1>
        </div>
      </div>

      {error && (
        <div className="card" style={{ borderColor: "#fca5a5", background: "#fff5f5", marginBottom: 20 }}>
          <p style={{ color: "#dc2626", margin: 0 }}>⚠ {error}</p>
        </div>
      )}

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Profile card */}
        <div className="card">
          <div className="section-title">My Profile</div>
          {patient ? (
            <table>
              <tbody>
                <tr><td style={{ color: "var(--color-text-muted)", width: 120 }}>Patient #</td><td>{patient.patient_number}</td></tr>
                <tr><td style={{ color: "var(--color-text-muted)" }}>Name</td><td>{patient.full_name}</td></tr>
                <tr><td style={{ color: "var(--color-text-muted)" }}>Gender</td><td>{patient.gender}</td></tr>
                <tr><td style={{ color: "var(--color-text-muted)" }}>Blood group</td><td>{patient.blood_group}</td></tr>
                <tr><td style={{ color: "var(--color-text-muted)" }}>District</td><td>{patient.district}</td></tr>
                <tr><td style={{ color: "var(--color-text-muted)" }}>Phone</td><td>{patient.phone || "—"}</td></tr>
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
                {new Date(latestRecord.created_at).toLocaleString()}
              </p>
              <p><strong>Symptoms:</strong> {latestRecord.symptoms || "—"}</p>
              <p><strong>Diagnosis:</strong> {latestRecord.diagnosis || "—"}</p>
              <p><strong>Treatment Plan:</strong> {latestRecord.treatment_plan || "—"}</p>
              <p><strong>Follow-up Date:</strong> {latestRecord.follow_up_date || "—"}</p>
              <p><strong>Doctor Progress Note:</strong> {latestRecord.notes || "—"}</p>
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
                  <td>{new Date(a.appointment_date).toLocaleString()}</td>
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

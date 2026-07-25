import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../api/endpoints";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Appointments() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const canManage = user.role === "admin" || user.role === "receptionist";
  const isDoctor = user.role === "doctor";
  const canAction = canManage || isDoctor;
  const [appointments, setAppointments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);

  const load = () => api.listAppointments().then((res) => setAppointments(res.data));

  useEffect(() => {
    load();
    // Load name lookup maps for admin/receptionist/doctor
    if (canAction) {
      api.listPatients().then((res) => setPatients(res.data));
    }
    if (canManage) {
      api.listDoctors().then((res) => setDoctors(res.data));
    }
  }, []);

  const patientName = (id) => patients.find((p) => p.id === id)?.name || `#${id}`;
  const doctorName = (id) => doctors.find((d) => d.id === id)?.full_name || `#${id}`;

  const handleStatus = async (appt, status) => {
    await api.updateAppointment(appt.id, { status });
    load();
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Appointments</h1>
        </div>
        {canManage && (
          <button className="btn" onClick={() => navigate("/appointments/book")}>
            + Book Appointment
          </button>
        )}
      </div>

      <div className="card">
        <div className="section-title">
          {canManage ? `All appointments (${appointments.length})` : "My appointments"}
        </div>
        <table>
          <thead>
            <tr>
              <th>When</th>
              <th>Patient</th>
              <th>Doctor</th>
              <th>Reason</th>
              <th>Status</th>
              {canAction && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {appointments.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.scheduled_at).toLocaleString()}</td>
                <td>{canAction ? patientName(a.patient_id) : `#${a.patient_id}`}</td>
                <td>{canManage ? doctorName(a.doctor_id) : (isDoctor ? "Me" : `#${a.doctor_id}`)}</td>
                <td>{a.reason || "—"}</td>
                <td>
                  <span
                    className={`badge ${
                      a.status === "scheduled"
                        ? "status-open"
                        : a.status === "completed"
                        ? "status-resolved"
                        : "status-acknowledged"
                    }`}
                  >
                    {a.status}
                  </span>
                </td>
                {canAction && (
                  <td style={{ display: "flex", gap: 6 }}>
                    {a.status === "scheduled" && (
                      <>
                        <button
                          className="btn secondary"
                          onClick={() => handleStatus(a, "completed")}
                        >
                          Complete
                        </button>
                        <button
                          className="btn danger"
                          onClick={() => handleStatus(a, "cancelled")}
                        >
                          Cancel
                        </button>
                      </>
                    )}
                  </td>
                )}
              </tr>
            ))}
            {appointments.length === 0 && (
              <tr>
                <td colSpan={canAction ? 6 : 5} className="empty-state">
                  No appointments found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

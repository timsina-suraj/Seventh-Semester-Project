import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../api/endpoints";
import { useAuth } from "../auth/AuthContext.jsx";
import { nameById } from "../utils/lookups.js";

const STATUS_BADGE = {
  Pending: "status-open",
  Confirmed: "status-acknowledged",
  Completed: "status-resolved",
  Cancelled: "status-acknowledged",
  "No-show": "status-acknowledged",
};

export default function Appointments() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const canManage = user.role === "admin" || user.role === "receptionist";
  const isDoctor = user.role === "doctor";
  const canAction = canManage || isDoctor;
  const [appointments, setAppointments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");

  const load = () =>
    api.listAppointments({ status: statusFilter || undefined }).then((res) => setAppointments(res.data));

  useEffect(() => {
    load();
  }, [statusFilter]);

  useEffect(() => {
    // Load name lookup maps for admin/receptionist/doctor (once)
    if (canAction) {
      api.listPatients().then((res) => setPatients(res.data));
    }
    if (canManage) {
      api.listDoctors().then((res) => setDoctors(res.data));
    }
  }, []);

  const handleStatus = async (appt, status) => {
    await api.updateAppointmentStatus(appt.id, status);
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
        <div className="page-header" style={{ marginBottom: 12 }}>
          <div className="section-title" style={{ margin: 0 }}>
            {canManage ? `All appointments (${appointments.length})` : "My appointments"}
          </div>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All statuses</option>
            <option value="Pending">Pending</option>
            <option value="Confirmed">Confirmed</option>
            <option value="Completed">Completed</option>
            <option value="Cancelled">Cancelled</option>
            <option value="No-show">No-show</option>
          </select>
        </div>
        <table>
          <thead>
            <tr>
              <th>When</th>
              <th>Patient</th>
              <th>Doctor</th>
              <th>Reason</th>
              <th>Status</th>
              <th></th>
              {canAction && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {appointments.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.appointment_date).toLocaleString()}</td>
                <td>{canAction ? nameById(patients, a.patient_id) : `#${a.patient_id}`}</td>
                <td>{canManage ? nameById(doctors, a.doctor_id) : (isDoctor ? "Me" : `#${a.doctor_id}`)}</td>
                <td>{a.reason || "—"}</td>
                <td>
                  <span className={`badge ${STATUS_BADGE[a.status] || "status-open"}`}>{a.status}</span>
                </td>
                <td>
                  <button className="btn secondary" onClick={() => api.downloadAppointmentReceiptPdf(a.id)}>
                    PDF
                  </button>
                </td>
                {canAction && (
                  <td style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {a.status === "Pending" && (
                      <button className="btn secondary" onClick={() => handleStatus(a, "Confirmed")}>
                        Confirm
                      </button>
                    )}
                    {(a.status === "Pending" || a.status === "Confirmed") && (
                      <>
                        <button className="btn secondary" onClick={() => handleStatus(a, "Completed")}>
                          Complete
                        </button>
                        <button className="btn secondary" onClick={() => handleStatus(a, "No-show")}>
                          No-show
                        </button>
                        <button className="btn danger" onClick={() => handleStatus(a, "Cancelled")}>
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
                <td colSpan={canAction ? 7 : 6} className="empty-state">
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

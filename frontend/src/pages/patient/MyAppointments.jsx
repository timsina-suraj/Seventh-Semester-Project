import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";

export default function MyAppointments() {
  const [appointments, setAppointments] = useState([]);

  useEffect(() => {
    api.listAppointments().then((res) => setAppointments(res.data));
  }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>My Appointments</h1>
        </div>
      </div>

      {appointments.length === 0 ? (
        <div className="empty-state">No appointments on file.</div>
      ) : (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>When</th>
                <th>Doctor</th>
                <th>Reason</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((a) => (
                <tr key={a.id}>
                  <td>{new Date(a.appointment_date).toLocaleString()}</td>
                  <td>#{a.doctor_id}</td>
                  <td>{a.reason || "—"}</td>
                  <td>{a.status}</td>
                  <td>
                    <button className="btn secondary" onClick={() => api.downloadAppointmentReceiptPdf(a.id)}>
                      PDF
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

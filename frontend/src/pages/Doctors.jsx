import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../api/endpoints";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Doctors() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user.role === "admin";
  const [doctors, setDoctors] = useState([]);

  const load = () => api.listDoctors().then((res) => setDoctors(res.data));

  useEffect(() => {
    load();
  }, []);

  const toggleAvailability = async (doctor) => {
    await api.updateDoctor(doctor.id, { is_available: !doctor.is_available });
    load();
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Doctors</h1>
        </div>
        {isAdmin && (
          <button className="btn" onClick={() => navigate("/doctors/add")}>
            + Add Doctor
          </button>
        )}
      </div>

      <div className="card">
        <div className="section-title">Doctor roster ({doctors.length})</div>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Specialization</th>
              <th>Phone</th>
              <th>Availability</th>
            </tr>
          </thead>
          <tbody>
            {doctors.map((d) => (
              <tr key={d.id}>
                <td>{d.full_name}</td>
                <td>{d.specialization}</td>
                <td>{d.phone || "—"}</td>
                <td>
                  {isAdmin ? (
                    <button className="btn secondary" onClick={() => toggleAvailability(d)}>
                      {d.is_available ? "✅ Available" : "❌ Unavailable"}
                    </button>
                  ) : (
                    <span>{d.is_available ? "✅ Available" : "❌ Unavailable"}</span>
                  )}
                </td>
              </tr>
            ))}
            {doctors.length === 0 && (
              <tr>
                <td colSpan={4} className="empty-state">
                  No doctors added yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

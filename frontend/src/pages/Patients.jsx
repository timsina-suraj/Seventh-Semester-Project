import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../api/endpoints";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Patients() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const canManage = user.role === "admin" || user.role === "receptionist";
  const [patients, setPatients] = useState([]);

  useEffect(() => {
    api.listPatients().then((res) => setPatients(res.data));
  }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Patients</h1>
        </div>
        {canManage && (
          <button className="btn" onClick={() => navigate("/patients/register")}>
            + Register Patient
          </button>
        )}
      </div>

      <div className="card">
        <div className="section-title">All patients ({patients.length})</div>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Age</th>
              <th>Gender</th>
              <th>District</th>
              <th>Phone</th>
              {canManage && <th>Login</th>}
            </tr>
          </thead>
          <tbody>
            {patients.map((p) => (
              <tr key={p.id}>
                <td>{p.name}</td>
                <td>{p.age}</td>
                <td>{p.gender}</td>
                <td>{p.district}</td>
                <td>{p.phone || "—"}</td>
                {canManage && (
                  <td>
                    {p.login_email
                      ? `${p.login_email} (${p.must_change_password ? "temporary" : "set"})`
                      : "—"}
                  </td>
                )}
              </tr>
            ))}
            {patients.length === 0 && (
              <tr>
                <td colSpan={canManage ? 6 : 5} className="empty-state">
                  No patients registered yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
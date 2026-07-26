import { useEffect, useState } from "react";
import * as api from "../api/endpoints";
import { useAuth } from "../auth/AuthContext.jsx";
import useDebouncedValue from "../hooks/useDebouncedValue.js";

export default function Doctors() {
  const { user } = useAuth();
  const isAdmin = user.role === "admin";
  const [doctors, setDoctors] = useState([]);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search);

  useEffect(() => {
    api.listDoctors({ search: debouncedSearch || undefined }).then((res) => setDoctors(res.data));
  }, [debouncedSearch]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Doctors</h1>
          {isAdmin && (
            <div className="page-subtitle">
              New doctor accounts are created from the <strong>Users</strong> page, so their login and
              roster entry are always linked.
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="page-header" style={{ marginBottom: 12 }}>
          <div className="section-title" style={{ margin: 0 }}>Doctor roster ({doctors.length})</div>
          <input
            type="text"
            placeholder="Search by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ maxWidth: 260 }}
          />
        </div>
        <table>
          <thead>
            <tr>
              <th>Employee ID</th>
              <th>Name</th>
              <th>Department</th>
              <th>Specialization</th>
              <th>License #</th>
            </tr>
          </thead>
          <tbody>
            {doctors.map((d) => (
              <tr key={d.id}>
                <td>{d.employee_id}</td>
                <td>{d.full_name}</td>
                <td>{d.department}</td>
                <td>{d.specialization}</td>
                <td>{d.license_number}</td>
              </tr>
            ))}
            {doctors.length === 0 && (
              <tr>
                <td colSpan={5} className="empty-state">
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

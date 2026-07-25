import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";

export default function Receptionists() {
  const [receptionists, setReceptionists] = useState([]);

  const load = () =>
    api.listUsers().then((res) => {
      const recs = res.data.filter((u) => u.role === "receptionist");
      setReceptionists(recs);
    });

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Receptionists</h1>
        </div>
      </div>

      <div className="card">
        <div className="section-title">Receptionist roster ({receptionists.length})</div>
        <table>
          <thead>
            <tr>
              <th>Email</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {receptionists.map((r) => (
              <tr key={r.id}>
                <td>{r.email}</td>
                <td>
                  <span>{r.is_active ? "✅ Active" : "❌ Disabled"}</span>
                </td>
              </tr>
            ))}
            {receptionists.length === 0 && (
              <tr>
                <td colSpan={3} className="empty-state">
                  No receptionists found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";

export default function Logs() {
  const [activeTab, setActiveTab] = useState("audit");
  const [auditLogs, setAuditLogs] = useState([]);
  const [loginLogs, setLoginLogs] = useState([]);
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    if (activeTab === "audit") {
      api.listAuditLogs({ limit: 100 }).then((res) => setAuditLogs(res.data)).catch(() => setError("Could not load audit logs."));
    } else {
      api.listLoginLogs({ limit: 100 }).then((res) => setLoginLogs(res.data)).catch(() => setError("Could not load login logs."));
    }
  };

  useEffect(load, [activeTab]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Logs</h1>
          <div className="page-subtitle">Who did what (audit logs) and who logged in (login logs)</div>
        </div>
        <button className="btn secondary" onClick={load}>
          Refresh
        </button>
      </div>

      <div className="tabs" style={{ display: "flex", gap: "16px", marginBottom: "20px", borderBottom: "1px solid var(--color-border)", paddingBottom: "10px" }}>
        <button className={`btn ${activeTab === "audit" ? "" : "secondary"}`} onClick={() => setActiveTab("audit")}>
          Audit Logs
        </button>
        <button className={`btn ${activeTab === "login" ? "" : "secondary"}`} onClick={() => setActiveTab("login")}>
          Login Logs
        </button>
      </div>

      {error && <div className="error-text" style={{ marginBottom: 12 }}>{error}</div>}

      {activeTab === "audit" && (
        <div className="card">
          <div className="section-title" style={{ marginTop: 0 }}>Recent activity ({auditLogs.length})</div>
          <table>
            <thead>
              <tr>
                <th>When</th>
                <th>User ID</th>
                <th>Action</th>
                <th>Entity</th>
                <th>IP Address</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.timestamp).toLocaleString()}</td>
                  <td>{log.user_id ?? "—"}</td>
                  <td>{log.action}</td>
                  <td>{log.entity_type}{log.entity_id ? ` #${log.entity_id}` : ""}</td>
                  <td>{log.ip_address || "—"}</td>
                </tr>
              ))}
              {auditLogs.length === 0 && (
                <tr>
                  <td colSpan={5} className="empty-state">No audit log entries yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === "login" && (
        <div className="card">
          <div className="section-title" style={{ marginTop: 0 }}>Recent logins ({loginLogs.length})</div>
          <table>
            <thead>
              <tr>
                <th>When</th>
                <th>Email</th>
                <th>Status</th>
                <th>IP Address</th>
                <th>Device</th>
              </tr>
            </thead>
            <tbody>
              {loginLogs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.login_time).toLocaleString()}</td>
                  <td>{log.attempted_email}</td>
                  <td>
                    <span className={`badge ${log.status === "success" ? "status-resolved" : "status-open"}`}>
                      {log.status}
                    </span>
                  </td>
                  <td>{log.ip_address || "—"}</td>
                  <td style={{ maxWidth: 260, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {log.device || "—"}
                  </td>
                </tr>
              ))}
              {loginLogs.length === 0 && (
                <tr>
                  <td colSpan={5} className="empty-state">No login log entries yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

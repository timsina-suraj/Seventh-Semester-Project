const STATUS_CLASS = {
  open: "status-open",
  acknowledged: "status-acknowledged",
  resolved: "status-resolved",
};

export default function AlertCard({ alert, onUpdateStatus }) {
  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <strong>{alert.alert_type === "district_risk" ? "District Risk Alert" : "Patient Diagnosis Alert"}</strong>
          <div className="page-subtitle">{new Date(alert.date).toLocaleString()}</div>
        </div>
        <span className={`badge ${STATUS_CLASS[alert.status] || "status-open"}`}>{alert.status}</span>
      </div>
      <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", fontSize: 14, margin: "12px 0" }}>
        {alert.message}
      </pre>
      {alert.status !== "resolved" && (
        <div style={{ display: "flex", gap: 8 }}>
          {alert.status === "open" && (
            <button className="btn secondary" onClick={() => onUpdateStatus(alert.id, "acknowledged")}>
              Acknowledge
            </button>
          )}
          <button className="btn" onClick={() => onUpdateStatus(alert.id, "resolved")}>
            Resolve
          </button>
        </div>
      )}
    </div>
  );
}

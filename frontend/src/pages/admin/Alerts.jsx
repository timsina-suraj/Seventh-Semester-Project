import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";
import AlertCard from "../../components/AlertCard.jsx";

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState("");

  const load = () => {
    api.listAlerts(filter || undefined).then((res) => setAlerts(res.data));
  };

  useEffect(load, [filter]);

  const handleUpdateStatus = async (id, status) => {
    await api.updateAlert(id, status);
    load();
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Alerts</h1>
          <div className="page-subtitle">District risk alerts and new dengue-positive patient alerts</div>
        </div>
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>

      {alerts.length === 0 ? (
        <div className="empty-state">No alerts to show.</div>
      ) : (
        alerts.map((alert) => <AlertCard key={alert.id} alert={alert} onUpdateStatus={handleUpdateStatus} />)
      )}
    </div>
  );
}

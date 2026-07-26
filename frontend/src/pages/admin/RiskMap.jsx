import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";
import NepalRiskMap from "../../components/NepalRiskMap.jsx";
import RiskBadge from "../../components/RiskBadge.jsx";

export default function RiskMap() {
  const [points, setPoints] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    setError("");
    api
      .getRiskMap()
      .then((res) => setPoints(res.data))
      .catch((err) => setError(err.response?.data?.detail || "Could not load the risk map. Train the dengue model first."))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const sorted = [...points].sort((a, b) => b.predicted_cases - a.predicted_cases);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Nepal District Risk Map</h1>
        </div>
        <button className="btn secondary" onClick={load} disabled={loading}>
          Refresh
        </button>
      </div>

      {error && <div className="error-text" style={{ marginBottom: 16 }}>{error}</div>}

      {points.length > 0 && (
        <div className="card" style={{ marginBottom: 20, padding: 0 }}>
          <NepalRiskMap points={points} />
        </div>
      )}

      {points.length > 0 && (
        <div className="card">
          <div className="section-title">Districts by predicted risk</div>
          <table>
            <thead>
              <tr>
                <th>District</th>
                <th>Predicted Cases</th>
                <th>Previous Cases</th>
                <th>Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((p) => (
                <tr key={p.district}>
                  <td>{p.district}</td>
                  <td>{p.predicted_cases}</td>
                  <td>{p.previous_cases ?? "N/A"}</td>
                  <td><RiskBadge level={p.risk_level} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";
import { useAuth } from "../../auth/AuthContext.jsx";
import StatTile from "../../components/StatTile.jsx";
import useDebouncedValue from "../../hooks/useDebouncedValue.js";

function isToday(isoString) {
  const d = new Date(isoString);
  const now = new Date();
  return d.toDateString() === now.toDateString();
}

export default function LabTechnicianDashboard() {
  const { user } = useAuth();
  const [tests, setTests] = useState([]);
  const [allTests, setAllTests] = useState([]);
  const [resultDrafts, setResultDrafts] = useState({});
  const [error, setError] = useState("");
  const [savingId, setSavingId] = useState(null);
  const [showCompleted, setShowCompleted] = useState(false);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search);

  const load = () => {
    const params = showCompleted ? {} : { status: "Requested" };
    if (debouncedSearch) params.search = debouncedSearch;
    api.listLabTests(params).then((res) => setTests(res.data)).catch(() => setTests([]));
  };

  const loadStats = () => {
    api.listLabTests({}).then((res) => setAllTests(res.data)).catch(() => {});
  };

  useEffect(load, [showCompleted, debouncedSearch]);
  useEffect(loadStats, []);

  const pendingCount = allTests.filter((t) => t.status === "Requested").length;
  const completedToday = allTests.filter((t) => t.status === "Completed" && t.result && isToday(t.result.completed_at)).length;

  const handleUpload = async (testId) => {
    const value = (resultDrafts[testId] || "").trim();
    if (!value) return;
    setError("");
    setSavingId(testId);
    try {
      await api.uploadLabResult(testId, { result_value: value });
      setResultDrafts((d) => ({ ...d, [testId]: "" }));
      load();
      loadStats();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not upload result.");
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Welcome, {user.fullName || user.email} 🧪</h1>
        </div>
        <button className="btn secondary" onClick={() => setShowCompleted((v) => !v)}>
          {showCompleted ? "Show pending only" : "Show all tests"}
        </button>
      </div>

      <div className="stat-grid" style={{ marginBottom: 20 }}>
        <StatTile label="Pending Tests" value={pendingCount} />
        <StatTile label="Completed Today" value={completedToday} />
        <StatTile label="Total Tests" value={allTests.length} />
      </div>

      {error && <div className="error-text" style={{ marginBottom: 12 }}>{error}</div>}

      <div className="card">
        <div className="page-header" style={{ marginBottom: 12 }}>
          <div className="section-title" style={{ margin: 0 }}>
            {showCompleted ? `All lab tests (${tests.length})` : `Pending lab tests (${tests.length})`}
          </div>
          <input
            type="text"
            placeholder="Search by test name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ maxWidth: 220 }}
          />
        </div>
        <table>
          <thead>
            <tr>
              <th>Patient ID</th>
              <th>Test</th>
              <th>Requested</th>
              <th>Status</th>
              <th>Result</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {tests.map((t) => (
              <tr key={t.id}>
                <td>#{t.patient_id}</td>
                <td>{t.test_name}</td>
                <td>{new Date(t.requested_at).toLocaleDateString()}</td>
                <td>{t.status}</td>
                <td>
                  {t.status === "Requested" ? (
                    <div style={{ display: "flex", gap: 6 }}>
                      <input
                        style={{ width: 140 }}
                        placeholder="Enter result"
                        value={resultDrafts[t.id] || ""}
                        onChange={(e) => setResultDrafts((d) => ({ ...d, [t.id]: e.target.value }))}
                      />
                      <button className="btn secondary" onClick={() => handleUpload(t.id)} disabled={savingId === t.id}>
                        {savingId === t.id ? "Saving…" : "Submit"}
                      </button>
                    </div>
                  ) : (
                    t.result?.result_value ?? "—"
                  )}
                </td>
                <td>
                  {t.status === "Completed" && (
                    <button className="btn secondary" onClick={() => api.downloadLabReportPdf(t.id)}>
                      PDF
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {tests.length === 0 && (
              <tr>
                <td colSpan={6} className="empty-state">
                  {showCompleted ? "No lab tests yet." : "No pending lab tests."}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

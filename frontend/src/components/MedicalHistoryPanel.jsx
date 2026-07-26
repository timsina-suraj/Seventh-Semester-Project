import { useEffect, useState } from "react";
import * as api from "../api/endpoints";

const CONDITION_STATUSES = ["Active", "Managed", "Resolved"];
const EMPTY_HISTORY = { condition_name: "", diagnosed_date: "", notes: "" };
const EMPTY_CONDITION = { condition: "", status: "Active", diagnosed_date: "" };

// Shared by the doctor's diagnosis flow (canEdit), the nurse dashboard, and
// the patient's own reports page (both read-only) — one implementation of
// "structured medical history + chronic conditions" instead of three.
export default function MedicalHistoryPanel({ patientId, canEdit = false }) {
  const [history, setHistory] = useState([]);
  const [conditions, setConditions] = useState([]);
  const [historyForm, setHistoryForm] = useState(EMPTY_HISTORY);
  const [conditionForm, setConditionForm] = useState(EMPTY_CONDITION);
  const [error, setError] = useState("");

  const load = () => {
    if (!patientId) return;
    api.listMedicalHistory(patientId).then((res) => setHistory(res.data)).catch(() => setHistory([]));
    api.listPatientConditions(patientId).then((res) => setConditions(res.data)).catch(() => setConditions([]));
  };

  useEffect(load, [patientId]);

  const handleAddHistory = async (e) => {
    e.preventDefault();
    if (!historyForm.condition_name.trim()) return;
    setError("");
    try {
      await api.addMedicalHistory({
        patient_id: Number(patientId),
        ...historyForm,
        diagnosed_date: historyForm.diagnosed_date || null,
      });
      setHistoryForm(EMPTY_HISTORY);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add medical history entry.");
    }
  };

  const handleAddCondition = async (e) => {
    e.preventDefault();
    if (!conditionForm.condition.trim()) return;
    setError("");
    try {
      await api.addPatientCondition({
        patient_id: Number(patientId),
        ...conditionForm,
        diagnosed_date: conditionForm.diagnosed_date || null,
      });
      setConditionForm(EMPTY_CONDITION);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add condition.");
    }
  };

  if (!patientId) return null;

  return (
    <div>
      {error && <div className="error-text" style={{ marginBottom: 12 }}>{error}</div>}
      <div className="grid-2">
        <div className="card">
          <div className="section-title" style={{ marginTop: 0 }}>Medical History (past conditions)</div>
          {canEdit && (
            <form onSubmit={handleAddHistory} style={{ marginBottom: 16 }}>
              <div className="form-row">
                <div className="form-group">
                  <label>Condition</label>
                  <input
                    value={historyForm.condition_name}
                    onChange={(e) => setHistoryForm({ ...historyForm, condition_name: e.target.value })}
                    placeholder="e.g. Typhoid Fever"
                  />
                </div>
                <div className="form-group">
                  <label>Diagnosed date</label>
                  <input
                    type="date"
                    value={historyForm.diagnosed_date}
                    onChange={(e) => setHistoryForm({ ...historyForm, diagnosed_date: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Notes</label>
                <input
                  value={historyForm.notes}
                  onChange={(e) => setHistoryForm({ ...historyForm, notes: e.target.value })}
                  placeholder="e.g. Fully recovered, no ongoing treatment"
                />
              </div>
              <button className="btn secondary" type="submit">+ Add history entry</button>
            </form>
          )}
          {history.length === 0 ? (
            <div className="empty-state">No past medical history on file.</div>
          ) : (
            <table>
              <thead><tr><th>Condition</th><th>Diagnosed</th><th>Notes</th></tr></thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.id}>
                    <td>{h.condition_name}</td>
                    <td>{h.diagnosed_date || "—"}</td>
                    <td>{h.notes || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card">
          <div className="section-title" style={{ marginTop: 0 }}>Chronic Conditions</div>
          {canEdit && (
            <form onSubmit={handleAddCondition} style={{ marginBottom: 16 }}>
              <div className="form-row">
                <div className="form-group">
                  <label>Condition</label>
                  <input
                    value={conditionForm.condition}
                    onChange={(e) => setConditionForm({ ...conditionForm, condition: e.target.value })}
                    placeholder="e.g. Diabetes"
                  />
                </div>
                <div className="form-group">
                  <label>Status</label>
                  <select
                    value={conditionForm.status}
                    onChange={(e) => setConditionForm({ ...conditionForm, status: e.target.value })}
                  >
                    {CONDITION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Diagnosed date</label>
                  <input
                    type="date"
                    value={conditionForm.diagnosed_date}
                    onChange={(e) => setConditionForm({ ...conditionForm, diagnosed_date: e.target.value })}
                  />
                </div>
              </div>
              <button className="btn secondary" type="submit">+ Add condition</button>
            </form>
          )}
          {conditions.length === 0 ? (
            <div className="empty-state">No chronic conditions on file.</div>
          ) : (
            <table>
              <thead><tr><th>Condition</th><th>Status</th><th>Diagnosed</th></tr></thead>
              <tbody>
                {conditions.map((c) => (
                  <tr key={c.id}>
                    <td>{c.condition}</td>
                    <td>{c.status}</td>
                    <td>{c.diagnosed_date || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

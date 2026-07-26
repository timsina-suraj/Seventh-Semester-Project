import { useEffect, useMemo, useState } from "react";
import * as api from "../api/endpoints";
import { nameById } from "../utils/lookups.js";
import { filterPatientsBySearch } from "../utils/patientFilter.js";

export default function Prescriptions() {
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [search, setSearch] = useState("");
  const [patientId, setPatientId] = useState("");

  useEffect(() => {
    api.listPatients().then((res) => setPatients(res.data)).catch(() => {});
    api.listDoctors().then((res) => setDoctors(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    api.listPrescriptions(patientId || undefined).then((res) => setPrescriptions(res.data)).catch(() => setPrescriptions([]));
  }, [patientId]);

  const filteredPatients = useMemo(() => filterPatientsBySearch(patients, search), [patients, search]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Prescriptions</h1>
          <div className="page-subtitle">Every prescription issued, filterable by patient</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="form-row">
          <div className="form-group" style={{ maxWidth: 260 }}>
            <label>Search patients</label>
            <input
              type="text"
              placeholder="Name or patient #..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="form-group" style={{ maxWidth: 360 }}>
            <label>Filter by patient</label>
            <select value={patientId} onChange={(e) => setPatientId(e.target.value)}>
              <option value="">All patients</option>
              {filteredPatients.map((p) => (
                <option key={p.id} value={p.id}>{p.full_name} ({p.patient_number})</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="section-title">{prescriptions.length} prescription(s)</div>
      {prescriptions.length === 0 ? (
        <div className="empty-state">No prescriptions found.</div>
      ) : (
        prescriptions.map((p) => (
          <div className="card" key={p.id} style={{ marginBottom: 12 }}>
            <div className="page-header" style={{ marginBottom: 8 }}>
              <div>
                <strong>{nameById(patients, p.patient_id)}</strong>
                <div className="page-subtitle" style={{ margin: 0 }}>
                  Prescribed by {nameById(doctors, p.doctor_id)} · {new Date(p.created_at).toLocaleString()}
                </div>
              </div>
              <button className="btn secondary" onClick={() => api.downloadPrescriptionPdf(p.id)}>
                Download PDF
              </button>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>Dosage</th>
                  <th>Frequency</th>
                  <th>Duration</th>
                  <th>Instructions</th>
                </tr>
              </thead>
              <tbody>
                {p.items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.medicine_name}</td>
                    <td>{item.dosage || "—"}</td>
                    <td>{item.frequency || "—"}</td>
                    <td>{item.duration || "—"}</td>
                    <td>{item.instructions || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))
      )}
    </div>
  );
}

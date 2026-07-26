import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";
import { nameById } from "../../utils/lookups.js";

export default function MedicalRecords() {
  const [records, setRecords] = useState([]);
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [doctorFilter, setDoctorFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [diagnosisFilter, setDiagnosisFilter] = useState("");
  const [error, setError] = useState("");

  const load = () => {
    setError("");
    api
      .listMedicalRecords(undefined, {
        doctor_id: doctorFilter || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        diagnosis: diagnosisFilter || undefined,
      })
      .then((res) => setRecords(res.data))
      .catch(() => setError("Could not load medical records."));
  };

  useEffect(() => {
    const handle = setTimeout(load, 300);
    return () => clearTimeout(handle);
  }, [doctorFilter, dateFrom, dateTo, diagnosisFilter]);

  useEffect(() => {
    api.listPatients().then((res) => setPatients(res.data)).catch(() => {});
    api.listDoctors().then((res) => setDoctors(res.data)).catch(() => {});
  }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Medical Records</h1>
          <div className="page-subtitle">Browse and filter EMR entries across all patients</div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="form-row">
          <div className="form-group">
            <label>Doctor</label>
            <select value={doctorFilter} onChange={(e) => setDoctorFilter(e.target.value)}>
              <option value="">All doctors</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>{d.full_name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>From date</label>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </div>
          <div className="form-group">
            <label>To date</label>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
          <div className="form-group">
            <label>Diagnosis contains</label>
            <input
              type="text"
              placeholder="e.g. dengue"
              value={diagnosisFilter}
              onChange={(e) => setDiagnosisFilter(e.target.value)}
            />
          </div>
        </div>
      </div>

      {error && <div className="error-text" style={{ marginBottom: 12 }}>{error}</div>}

      <div className="card">
        <div className="section-title" style={{ marginTop: 0 }}>Records ({records.length})</div>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Patient</th>
              <th>Doctor</th>
              <th>Diagnosis</th>
              <th>Follow-up</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={r.id}>
                <td>{new Date(r.created_at).toLocaleString()}</td>
                <td>{nameById(patients, r.patient_id)}</td>
                <td>{r.doctor_id ? nameById(doctors, r.doctor_id) : "—"}</td>
                <td>{r.diagnosis || "—"}</td>
                <td>{r.follow_up_date || "—"}</td>
                <td>
                  <button className="btn secondary" onClick={() => api.downloadMedicalRecordPdf(r.id)}>
                    PDF
                  </button>
                </td>
              </tr>
            ))}
            {records.length === 0 && (
              <tr>
                <td colSpan={6} className="empty-state">No medical records match these filters.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

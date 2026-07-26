import { useEffect, useMemo, useState } from "react";
import * as api from "../../api/endpoints";
import { useAuth } from "../../auth/AuthContext.jsx";
import StatTile from "../../components/StatTile.jsx";
import DocumentPreviewModal from "../../components/DocumentPreviewModal.jsx";
import { filterPatientsBySearch } from "../../utils/patientFilter.js";
import { DOCUMENT_CATEGORIES } from "../../constants/documents.js";
import MedicalHistoryPanel from "../../components/MedicalHistoryPanel.jsx";

const EMPTY_VITALS = { temperature: "", blood_pressure: "", heart_rate: "", oxygen_level: "", weight: "" };
const EMPTY_MED = { medicine: "", dose: "" };

export default function NurseDashboard() {
  const { user } = useAuth();
  const [patients, setPatients] = useState([]);
  const [patientId, setPatientId] = useState("");
  const [patientSearch, setPatientSearch] = useState("");
  const [previewDoc, setPreviewDoc] = useState(null);

  const filteredPatients = useMemo(
    () => filterPatientsBySearch(patients, patientSearch),
    [patients, patientSearch]
  );

  const selectedPatient = patients.find((p) => String(p.id) === String(patientId));

  const [vitalsForm, setVitalsForm] = useState(EMPTY_VITALS);
  const [vitals, setVitals] = useState([]);
  const [vitalsError, setVitalsError] = useState("");
  const [savingVitals, setSavingVitals] = useState(false);

  const [medForm, setMedForm] = useState(EMPTY_MED);
  const [administrations, setAdministrations] = useState([]);

  const [records, setRecords] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [labTests, setLabTests] = useState([]);

  const [documents, setDocuments] = useState([]);
  const [uploadCategory, setUploadCategory] = useState(DOCUMENT_CATEGORIES[0]);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadError, setUploadError] = useState("");
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    api.listPatients().then((res) => setPatients(res.data)).catch(() => {});
  }, []);

  const loadPatientData = (id) => {
    api.listPatientVitals(id).then((res) => setVitals(res.data)).catch(() => setVitals([]));
    api.listMedicineAdministrations(id).then((res) => setAdministrations(res.data)).catch(() => setAdministrations([]));
    api.listMedicalRecords(id).then((res) => setRecords(res.data)).catch(() => setRecords([]));
    api.listPrescriptions(id).then((res) => setPrescriptions(res.data)).catch(() => setPrescriptions([]));
    api.listLabTests({ patient_id: id }).then((res) => setLabTests(res.data)).catch(() => setLabTests([]));
    api.listDocuments(id).then((res) => setDocuments(res.data)).catch(() => setDocuments([]));
  };

  const handleUploadDocument = async (e) => {
    e.preventDefault();
    setUploadError("");
    if (!uploadFile || !patientId) return;
    setUploading(true);
    try {
      await api.uploadDocument(Number(patientId), uploadCategory, uploadFile);
      setUploadFile(null);
      e.target.reset();
      loadPatientData(patientId);
    } catch (err) {
      setUploadError(err.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  useEffect(() => {
    if (patientId) loadPatientData(patientId);
  }, [patientId]);

  const handleVitalsSubmit = async (e) => {
    e.preventDefault();
    setVitalsError("");
    setSavingVitals(true);
    try {
      await api.recordPatientVitals({
        patient_id: Number(patientId),
        temperature: vitalsForm.temperature ? Number(vitalsForm.temperature) : null,
        blood_pressure: vitalsForm.blood_pressure || null,
        heart_rate: vitalsForm.heart_rate ? Number(vitalsForm.heart_rate) : null,
        oxygen_level: vitalsForm.oxygen_level ? Number(vitalsForm.oxygen_level) : null,
        weight: vitalsForm.weight ? Number(vitalsForm.weight) : null,
      });
      setVitalsForm(EMPTY_VITALS);
      loadPatientData(patientId);
    } catch (err) {
      setVitalsError(err.response?.data?.detail || "Could not record vitals.");
    } finally {
      setSavingVitals(false);
    }
  };

  const handleMedSubmit = async (e) => {
    e.preventDefault();
    if (!medForm.medicine.trim()) return;
    await api.recordMedicineAdministration({ patient_id: Number(patientId), medicine: medForm.medicine, dose: medForm.dose || null });
    setMedForm(EMPTY_MED);
    loadPatientData(patientId);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Welcome, {user.fullName || user.email} 🩺</h1>
        </div>
      </div>

      <div className="stat-grid" style={{ marginBottom: 20 }}>
        <StatTile label="Patients Under Care" value={patients.length} />
        {selectedPatient && <StatTile label="Vitals Recorded (this patient)" value={vitals.length} />}
        {selectedPatient && <StatTile label="Medications Given (this patient)" value={administrations.length} />}
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="form-row">
          <div className="form-group" style={{ maxWidth: 260 }}>
            <label>Search patients</label>
            <input
              type="text"
              placeholder="Name or patient #..."
              value={patientSearch}
              onChange={(e) => setPatientSearch(e.target.value)}
            />
          </div>
          <div className="form-group" style={{ maxWidth: 420 }}>
            <label>Select patient</label>
            <select value={patientId} onChange={(e) => setPatientId(e.target.value)}>
              <option value="">— Select a patient —</option>
              {filteredPatients.map((p) => (
                <option key={p.id} value={p.id}>{p.full_name} ({p.patient_number})</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {patientId && (
        <>
          <div className="grid-2" style={{ marginBottom: 20 }}>
            <div className="card">
              <div className="section-title" style={{ marginTop: 0 }}>Record Vitals</div>
              <form onSubmit={handleVitalsSubmit}>
                <div className="form-row">
                  <div className="form-group">
                    <label>Temperature (°C)</label>
                    <input type="number" step="0.1" value={vitalsForm.temperature} onChange={(e) => setVitalsForm({ ...vitalsForm, temperature: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>Blood Pressure</label>
                    <input placeholder="120/80" value={vitalsForm.blood_pressure} onChange={(e) => setVitalsForm({ ...vitalsForm, blood_pressure: e.target.value })} />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Heart Rate (bpm)</label>
                    <input type="number" value={vitalsForm.heart_rate} onChange={(e) => setVitalsForm({ ...vitalsForm, heart_rate: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>Oxygen Level (%)</label>
                    <input type="number" step="0.1" value={vitalsForm.oxygen_level} onChange={(e) => setVitalsForm({ ...vitalsForm, oxygen_level: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>Weight (kg)</label>
                    <input type="number" step="0.1" value={vitalsForm.weight} onChange={(e) => setVitalsForm({ ...vitalsForm, weight: e.target.value })} />
                  </div>
                </div>
                {vitalsError && <div className="error-text">{vitalsError}</div>}
                <button className="btn" type="submit" disabled={savingVitals}>
                  {savingVitals ? "Saving..." : "Save vitals"}
                </button>
              </form>

              <div className="section-title" style={{ marginTop: 20 }}>Recent Vitals</div>
              <table>
                <thead>
                  <tr><th>When</th><th>Temp</th><th>BP</th><th>HR</th><th>O2</th></tr>
                </thead>
                <tbody>
                  {vitals.map((v) => (
                    <tr key={v.id}>
                      <td>{new Date(v.recorded_at).toLocaleString()}</td>
                      <td>{v.temperature ?? "—"}</td>
                      <td>{v.blood_pressure ?? "—"}</td>
                      <td>{v.heart_rate ?? "—"}</td>
                      <td>{v.oxygen_level ?? "—"}</td>
                    </tr>
                  ))}
                  {vitals.length === 0 && <tr><td colSpan={5} className="empty-state">No vitals recorded yet.</td></tr>}
                </tbody>
              </table>
            </div>

            <div className="card">
              <div className="section-title" style={{ marginTop: 0 }}>Medication Administration</div>
              <form onSubmit={handleMedSubmit} style={{ marginBottom: 16 }}>
                <div className="form-row">
                  <div className="form-group">
                    <label>Medicine</label>
                    <input value={medForm.medicine} onChange={(e) => setMedForm({ ...medForm, medicine: e.target.value })} placeholder="e.g. Paracetamol 500mg" />
                  </div>
                  <div className="form-group">
                    <label>Dose</label>
                    <input value={medForm.dose} onChange={(e) => setMedForm({ ...medForm, dose: e.target.value })} placeholder="1 tablet" />
                  </div>
                </div>
                <button className="btn secondary" type="submit">Log administration</button>
              </form>
              <table>
                <thead><tr><th>When</th><th>Medicine</th><th>Dose</th></tr></thead>
                <tbody>
                  {administrations.map((a) => (
                    <tr key={a.id}>
                      <td>{new Date(a.time_given).toLocaleString()}</td>
                      <td>{a.medicine}</td>
                      <td>{a.dose ?? "—"}</td>
                    </tr>
                  ))}
                  {administrations.length === 0 && <tr><td colSpan={3} className="empty-state">Nothing logged yet.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 20 }}>
            <div className="section-title" style={{ marginTop: 0 }}>Doctor Instructions &amp; Diagnosis (read-only)</div>
            {records.length === 0 ? (
              <div className="empty-state">No medical records on file.</div>
            ) : (
              records.map((r) => (
                <div key={r.id} style={{ marginBottom: 10, paddingBottom: 10, borderBottom: "1px solid var(--color-border)" }}>
                  <div className="page-subtitle">{new Date(r.created_at).toLocaleString()}</div>
                  <p><strong>Diagnosis:</strong> {r.diagnosis || "—"}</p>
                  <p><strong>Treatment Plan:</strong> {r.treatment_plan || "—"}</p>
                </div>
              ))
            )}
          </div>

          <div style={{ marginBottom: 20 }}>
            <div className="section-title">Patient History &amp; Conditions (read-only)</div>
            <MedicalHistoryPanel patientId={patientId} />
          </div>

          <div className="grid-2">
            <div className="card">
              <div className="section-title" style={{ marginTop: 0 }}>Prescriptions (read-only)</div>
              {prescriptions.length === 0 ? (
                <div className="empty-state">No prescriptions on file.</div>
              ) : (
                prescriptions.map((p) => (
                  <div key={p.id} style={{ marginBottom: 8 }}>
                    {p.items.map((item) => (
                      <div key={item.id} style={{ fontSize: 13 }}>{item.medicine_name} — {item.dosage} {item.frequency}</div>
                    ))}
                  </div>
                ))
              )}
            </div>
            <div className="card">
              <div className="section-title" style={{ marginTop: 0 }}>Lab Results (read-only)</div>
              {labTests.length === 0 ? (
                <div className="empty-state">No lab tests on file.</div>
              ) : (
                <table>
                  <thead><tr><th>Test</th><th>Status</th><th>Result</th></tr></thead>
                  <tbody>
                    {labTests.map((t) => (
                      <tr key={t.id}>
                        <td>{t.test_name}</td>
                        <td>{t.status}</td>
                        <td>{t.result?.result_value ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>

          <div className="card" style={{ marginTop: 20 }}>
            <div className="section-title" style={{ marginTop: 0 }}>Documents</div>
            <form onSubmit={handleUploadDocument} className="form-row" style={{ alignItems: "flex-end", marginBottom: 16 }}>
              <div className="form-group">
                <label>Category</label>
                <select value={uploadCategory} onChange={(e) => setUploadCategory(e.target.value)}>
                  {DOCUMENT_CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>File</label>
                <input type="file" onChange={(e) => setUploadFile(e.target.files?.[0] || null)} required />
              </div>
              <button className="btn" type="submit" disabled={uploading} style={{ marginBottom: 14 }}>
                {uploading ? "Uploading..." : "Upload"}
              </button>
            </form>
            {uploadError && <div className="error-text" style={{ marginBottom: 12 }}>{uploadError}</div>}
            {documents.length === 0 ? (
              <div className="empty-state">No documents on file for this patient.</div>
            ) : (
              <table>
                <thead>
                  <tr><th>File</th><th>Category</th><th>Uploaded</th><th></th></tr>
                </thead>
                <tbody>
                  {documents.map((d) => (
                    <tr key={d.id}>
                      <td>{d.original_filename}</td>
                      <td>{d.category}</td>
                      <td>{new Date(d.uploaded_at).toLocaleString()}</td>
                      <td style={{ display: "flex", gap: 6 }}>
                        <button className="btn secondary" onClick={() => setPreviewDoc(d)}>
                          View
                        </button>
                        <button className="btn secondary" onClick={() => api.downloadDocument(d.id, d.original_filename)}>
                          Download
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {previewDoc && <DocumentPreviewModal document={previewDoc} onClose={() => setPreviewDoc(null)} />}
    </div>
  );
}

import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";
import DocumentPreviewModal from "../../components/DocumentPreviewModal.jsx";
import MedicalHistoryPanel from "../../components/MedicalHistoryPanel.jsx";
import { DOCUMENT_CATEGORIES } from "../../constants/documents.js";

export default function Reports() {
  const [records, setRecords] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [labTests, setLabTests] = useState([]);
  const [patientId, setPatientId] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [previewDoc, setPreviewDoc] = useState(null);
  const [uploadCategory, setUploadCategory] = useState(DOCUMENT_CATEGORIES[0]);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadError, setUploadError] = useState("");
  const [uploading, setUploading] = useState(false);

  const loadDocuments = (id) => {
    api.listDocuments(id).then((res) => setDocuments(res.data)).catch(() => {});
  };

  useEffect(() => {
    api.listMedicalRecords().then((res) => setRecords(res.data));
    api.listPrescriptions().catch(() => ({ data: [] })).then((res) => setPrescriptions(res?.data || []));
    api.listLabTests().catch(() => ({ data: [] })).then((res) => setLabTests(res?.data || []));
    api.getMyPatientRecord().then((res) => {
      setPatientId(res.data.id);
      loadDocuments(res.data.id);
    }).catch(() => {});
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    setUploadError("");
    if (!uploadFile || !patientId) return;
    setUploading(true);
    try {
      await api.uploadDocument(patientId, uploadCategory, uploadFile);
      setUploadFile(null);
      e.target.reset();
      loadDocuments(patientId);
    } catch (err) {
      setUploadError(err.response?.data?.detail || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (id) => {
    await api.deleteDocument(id);
    loadDocuments(patientId);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>My Reports</h1>
          <div className="page-subtitle">Medical records, diagnoses, prescriptions, lab results, and documents</div>
        </div>
      </div>

      <div className="section-title">Medical Records</div>
      {records.length === 0 ? (
        <div className="empty-state">No medical records on file yet.</div>
      ) : (
        records.map((r) => (
          <div className="card" key={r.id} style={{ marginBottom: 12 }}>
            <div className="page-header" style={{ marginBottom: 0 }}>
              <div className="page-subtitle" style={{ margin: 0 }}>{new Date(r.created_at).toLocaleString()}</div>
              <button className="btn secondary" onClick={() => api.downloadMedicalRecordPdf(r.id)}>
                Download PDF
              </button>
            </div>
            <p><strong>Symptoms:</strong> {r.symptoms || "—"}</p>
            <p><strong>Diagnosis:</strong> {r.diagnosis || "—"}</p>
            <p><strong>Treatment Plan:</strong> {r.treatment_plan || "—"}</p>
            <p><strong>Follow-up Date:</strong> {r.follow_up_date || "—"}</p>
            <p><strong>Doctor Progress Note:</strong> {r.notes || "—"}</p>
            {r.ml_dengue_predicted !== null && (
              <p>
                <strong>AI screening:</strong>{" "}
                {r.ml_dengue_predicted ? "Dengue positive" : "Dengue negative"}{" "}
                ({(r.ml_dengue_probability * 100).toFixed(1)}% confidence)
              </p>
            )}
          </div>
        ))
      )}

      <div className="section-title" style={{ marginTop: 24 }}>Medical History &amp; Conditions</div>
      <MedicalHistoryPanel patientId={patientId} />

      <div className="section-title" style={{ marginTop: 24 }}>Prescriptions</div>
      {prescriptions.length === 0 ? (
        <div className="empty-state">No prescriptions on file yet.</div>
      ) : (
        prescriptions.map((p) => (
          <div className="card" key={p.id} style={{ marginBottom: 12 }}>
            <div className="page-header" style={{ marginBottom: 0 }}>
              <div className="page-subtitle" style={{ margin: 0 }}>{new Date(p.created_at).toLocaleString()}</div>
              <button className="btn secondary" onClick={() => api.downloadPrescriptionPdf(p.id)}>
                Download PDF
              </button>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>Qty</th>
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
                    <td>{item.quantity ?? "—"}</td>
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

      <div className="section-title" style={{ marginTop: 24 }}>Lab Tests &amp; Results</div>
      {labTests.length === 0 ? (
        <div className="empty-state">No lab tests on file yet.</div>
      ) : (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>Test</th>
                <th>Requested</th>
                <th>Status</th>
                <th>Result</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {labTests.map((t) => (
                <tr key={t.id}>
                  <td>{t.test_name}</td>
                  <td>{new Date(t.requested_at).toLocaleDateString()}</td>
                  <td>{t.status}</td>
                  <td>{t.result?.result_value || "—"}</td>
                  <td>
                    <button className="btn secondary" onClick={() => api.downloadLabReportPdf(t.id)}>
                      PDF
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="section-title" style={{ marginTop: 24 }}>My Documents</div>
      <div className="card">
        <form onSubmit={handleUpload} className="form-row" style={{ alignItems: "flex-end", marginBottom: 16 }}>
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
          <button className="btn" type="submit" disabled={uploading || !patientId} style={{ marginBottom: 14 }}>
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </form>
        {uploadError && <div className="error-text" style={{ marginBottom: 12 }}>{uploadError}</div>}

        {documents.length === 0 ? (
          <div className="empty-state">No documents uploaded yet.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>File</th>
                <th>Category</th>
                <th>Uploaded</th>
                <th></th>
              </tr>
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
                    <button className="btn danger" onClick={() => handleDeleteDocument(d.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {previewDoc && <DocumentPreviewModal document={previewDoc} onClose={() => setPreviewDoc(null)} />}
    </div>
  );
}

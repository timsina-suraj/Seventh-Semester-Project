import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";

export default function Reports() {
  const [records, setRecords] = useState([]);

  useEffect(() => {
    api.listMedicalRecords().then((res) => setRecords(res.data));
  }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>My Reports</h1>
          <div className="page-subtitle">Medical records, diagnoses, and prescriptions</div>
        </div>
      </div>

      {records.length === 0 ? (
        <div className="empty-state">No medical records on file yet.</div>
      ) : (
        records.map((r) => (
          <div className="card" key={r.id} style={{ marginBottom: 12 }}>
            <div className="page-subtitle">{new Date(r.date).toLocaleString()}</div>
            <p><strong>Symptoms:</strong> {r.symptoms || "—"}</p>
            <p><strong>Medical History:</strong> {r.medical_history || "—"}</p>
            <p><strong>Clinical &amp; Medication History:</strong> {r.clinical_history || "—"}</p>
            <p><strong>Diagnosis:</strong> {r.diagnosis || "—"}</p>
            <p><strong>Test Results:</strong> {r.lab_result || "—"}</p>
            <p><strong>Tests Prescribed:</strong> {r.prescribed_tests || "—"}</p>
            <p><strong>Medicines Prescribed:</strong> {r.prescription || "—"}</p>
            <p><strong>Doctor Progress Note:</strong> {r.doctor_note || "—"}</p>
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
    </div>
  );
}

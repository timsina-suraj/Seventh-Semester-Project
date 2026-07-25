import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";

const EMPTY_FORM = {
  patient_id: "",
  symptoms: "",
  diagnosis: "",
  lab_result: "",
  prescription: "",
  prescribed_tests: "",
  medical_history: "",
  clinical_history: "",
  doctor_note: "",
};

export default function DiagnosisPrediction() {
  const [patients, setPatients] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Doctors only see their linked patients now based on backend logic
    api.listPatients().then((res) => setPatients(res.data)).catch(() => {});
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess(false);
    setLoading(true);
    try {
      if (!form.patient_id) {
        throw new Error("Please select a patient.");
      }
      await api.createMedicalRecord({
        ...form,
        patient_id: Number(form.patient_id),
      });
      setSuccess(true);
      setForm(EMPTY_FORM);
    } catch (err) {
      setError(err.message || err.response?.data?.detail || "Failed to save medical record.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Fill Diagnosis &amp; Record</h1>
          <div className="page-subtitle">Manually record a patient's diagnosis, prescribed tests, and medication.</div>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 800 }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Patient *</label>
            <select name="patient_id" value={form.patient_id} onChange={handleChange} required>
              <option value="">— Select a patient —</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>{p.name} ({p.district})</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Symptoms</label>
            <textarea name="symptoms" rows={3} value={form.symptoms} onChange={handleChange} placeholder="e.g. High fever, joint pain, headache" />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Medical History</label>
              <textarea name="medical_history" rows={3} value={form.medical_history} onChange={handleChange} placeholder="Past medical conditions, allergies, etc." />
            </div>
            <div className="form-group">
              <label>Clinical &amp; Medication History</label>
              <textarea name="clinical_history" rows={3} value={form.clinical_history} onChange={handleChange} placeholder="Previous medications or clinical observations" />
            </div>
          </div>

          <div className="form-group">
            <label>Diagnosis</label>
            <input type="text" name="diagnosis" value={form.diagnosis} onChange={handleChange} placeholder="Primary diagnosis" />
          </div>

          <div className="form-group">
            <label>Lab Results</label>
            <input type="text" name="lab_result" value={form.lab_result} onChange={handleChange} placeholder="Key lab findings (if any)" />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Prescribed Tests</label>
              <input type="text" name="prescribed_tests" value={form.prescribed_tests} onChange={handleChange} placeholder="e.g. CBC, Dengue NS1" />
            </div>
            <div className="form-group">
              <label>Prescribed Medicines</label>
              <input type="text" name="prescription" value={form.prescription} onChange={handleChange} placeholder="e.g. Paracetamol 500mg" />
            </div>
          </div>

          <div className="form-group">
            <label>Doctor Progress Note</label>
            <textarea name="doctor_note" rows={4} value={form.doctor_note} onChange={handleChange} placeholder="Detailed notes for follow-up and monitoring..." />
          </div>

          {error && <div className="error-text" style={{ marginBottom: 12 }}>{String(error)}</div>}
          {success && <div className="success-text" style={{ marginBottom: 12, color: "var(--color-success)" }}>Medical record saved successfully!</div>}
          
          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Saving..." : "Save Record"}
          </button>
        </form>
      </div>
    </div>
  );
}

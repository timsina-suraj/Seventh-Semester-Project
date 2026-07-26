import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";
import MedicalHistoryPanel from "../../components/MedicalHistoryPanel.jsx";

const EMPTY_FORM = {
  patient_id: "",
  symptoms: "",
  diagnosis: "",
  notes: "",
  treatment_plan: "",
  follow_up_date: "",
};

const EMPTY_ITEM = { medicine_name: "", dosage: "", frequency: "", duration: "", instructions: "" };

export default function DiagnosisPrediction() {
  const [patients, setPatients] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [items, setItems] = useState([{ ...EMPTY_ITEM }]);
  const [labTests, setLabTests] = useState([""]);
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

  const handleItemChange = (index, field, value) => {
    setItems((rows) => rows.map((row, i) => (i === index ? { ...row, [field]: value } : row)));
  };
  const addItemRow = () => setItems((rows) => [...rows, { ...EMPTY_ITEM }]);
  const removeItemRow = (index) => setItems((rows) => rows.filter((_, i) => i !== index));

  const handleLabTestChange = (index, value) => {
    setLabTests((rows) => rows.map((row, i) => (i === index ? value : row)));
  };
  const addLabTestRow = () => setLabTests((rows) => [...rows, ""]);
  const removeLabTestRow = (index) => setLabTests((rows) => rows.filter((_, i) => i !== index));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess(false);
    setLoading(true);
    try {
      if (!form.patient_id) {
        throw new Error("Please select a patient.");
      }

      const { data: record } = await api.createMedicalRecord({
        ...form,
        patient_id: Number(form.patient_id),
        follow_up_date: form.follow_up_date || null,
      });

      const prescriptionItems = items.filter((row) => row.medicine_name.trim());
      if (prescriptionItems.length > 0) {
        await api.createPrescription({
          patient_id: Number(form.patient_id),
          medical_record_id: record.id,
          items: prescriptionItems,
        });
      }

      const testNames = labTests.map((t) => t.trim()).filter(Boolean);
      for (const test_name of testNames) {
        await api.requestLabTest({ patient_id: Number(form.patient_id), test_name });
      }

      setSuccess(true);
      setForm(EMPTY_FORM);
      setItems([{ ...EMPTY_ITEM }]);
      setLabTests([""]);
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
          <div className="page-subtitle">Record diagnosis, prescribe medicines, and request lab tests in one flow.</div>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 820 }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Patient *</label>
            <select name="patient_id" value={form.patient_id} onChange={handleChange} required>
              <option value="">— Select a patient —</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>{p.full_name} ({p.district})</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Symptoms</label>
            <textarea name="symptoms" rows={3} value={form.symptoms} onChange={handleChange} placeholder="e.g. High fever, joint pain, headache" />
          </div>

          <div className="form-group">
            <label>Diagnosis</label>
            <input type="text" name="diagnosis" value={form.diagnosis} onChange={handleChange} placeholder="Primary diagnosis" />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Treatment Plan</label>
              <textarea name="treatment_plan" rows={3} value={form.treatment_plan} onChange={handleChange} placeholder="e.g. Bed rest, monitor platelet count daily" />
            </div>
            <div className="form-group">
              <label>Follow-up Date</label>
              <input type="date" name="follow_up_date" value={form.follow_up_date} onChange={handleChange} />
            </div>
          </div>

          <div className="form-group">
            <label>Doctor Progress Note</label>
            <textarea name="notes" rows={3} value={form.notes} onChange={handleChange} placeholder="Detailed notes for follow-up and monitoring..." />
          </div>

          <div className="section-title" style={{ marginTop: 20 }}>Prescription (optional)</div>
          {items.map((row, i) => (
            <div key={i} className="form-row" style={{ alignItems: "flex-end", marginBottom: 8 }}>
              <div className="form-group">
                <label>Medicine</label>
                <input value={row.medicine_name} onChange={(e) => handleItemChange(i, "medicine_name", e.target.value)} placeholder="e.g. Paracetamol 500mg" />
              </div>
              <div className="form-group">
                <label>Dosage</label>
                <input value={row.dosage} onChange={(e) => handleItemChange(i, "dosage", e.target.value)} placeholder="500mg" />
              </div>
              <div className="form-group">
                <label>Frequency</label>
                <input value={row.frequency} onChange={(e) => handleItemChange(i, "frequency", e.target.value)} placeholder="3x/day" />
              </div>
              <div className="form-group">
                <label>Duration</label>
                <input value={row.duration} onChange={(e) => handleItemChange(i, "duration", e.target.value)} placeholder="5 days" />
              </div>
              <div className="form-group">
                <label>Instructions</label>
                <input value={row.instructions} onChange={(e) => handleItemChange(i, "instructions", e.target.value)} placeholder="After meals" />
              </div>
              {items.length > 1 && (
                <button type="button" className="btn secondary" onClick={() => removeItemRow(i)} style={{ marginBottom: 14 }}>
                  Remove
                </button>
              )}
            </div>
          ))}
          <button type="button" className="btn secondary" onClick={addItemRow} style={{ marginBottom: 20 }}>
            + Add medicine
          </button>

          <div className="section-title">Lab Tests to Request (optional)</div>
          {labTests.map((name, i) => (
            <div key={i} className="form-row" style={{ alignItems: "flex-end", marginBottom: 8 }}>
              <div className="form-group">
                <label>Test name</label>
                <input value={name} onChange={(e) => handleLabTestChange(i, e.target.value)} placeholder="e.g. CBC, Dengue NS1" />
              </div>
              {labTests.length > 1 && (
                <button type="button" className="btn secondary" onClick={() => removeLabTestRow(i)} style={{ marginBottom: 14 }}>
                  Remove
                </button>
              )}
            </div>
          ))}
          <button type="button" className="btn secondary" onClick={addLabTestRow} style={{ marginBottom: 20 }}>
            + Add lab test
          </button>

          {error && <div className="error-text" style={{ marginBottom: 12 }}>{String(error)}</div>}
          {success && <div className="success-text" style={{ marginBottom: 12, color: "var(--color-success)" }}>Medical record saved successfully!</div>}

          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Saving..." : "Save Record"}
          </button>
        </form>
      </div>

      {form.patient_id && (
        <>
          <div className="section-title" style={{ marginTop: 24 }}>Patient History &amp; Conditions</div>
          <MedicalHistoryPanel patientId={form.patient_id} canEdit />
        </>
      )}
    </div>
  );
}

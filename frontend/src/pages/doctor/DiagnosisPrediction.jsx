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

const ML_NUMERIC_FIELDS = [
  "age", "days_since_fever_onset", "body_temperature",
  "platelet_day1", "platelet_day3", "hematocrit_day1", "hematocrit_day3", "wbc_count",
];

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const EMPTY_ML_FORM = {
  gender: "Male",
  age: "",
  district: "",
  visit_month: "",
  days_since_fever_onset: "",
  body_temperature: "",
  platelet_day1: "250000",
  platelet_day3: "250000",
  hematocrit_day1: "42",
  hematocrit_day3: "42",
  wbc_count: "7000",
  ns1: false,
  igg: false,
  igm: false,
  joint_pain: "No_Joint_Pain",
  headache: false,
  retro_orbital_pain: false,
  myalgia: false,
  rash: false,
  persistent_vomiting: false,
  abdominal_pain: false,
  bleeding: false,
  restlessness: false,
  lethargy: false,
  liver_enlargement: false,
  previous_dengue_history: false,
  diabetes: false,
  hypertension: false,
  obesity: false,
  pregnancy: false,
};

function calcAge(dateOfBirth) {
  if (!dateOfBirth) return "";
  const ageMs = Date.now() - new Date(dateOfBirth).getTime();
  return String(Math.max(0, Math.floor(ageMs / (365.25 * 24 * 60 * 60 * 1000))));
}

const MlCheckboxRow = ({ label, name, form, onChange }) => (
  <label className="checkbox-row">
    <input type="checkbox" name={name} checked={form[name]} onChange={onChange} /> {label}
  </label>
);

export default function DiagnosisPrediction() {
  const [patients, setPatients] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [items, setItems] = useState([{ ...EMPTY_ITEM }]);
  const [labTests, setLabTests] = useState([""]);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [mlForm, setMlForm] = useState(EMPTY_ML_FORM);
  const [mlResult, setMlResult] = useState(null);
  const [mlError, setMlError] = useState("");
  const [mlLoading, setMlLoading] = useState(false);

  useEffect(() => {
    // Doctors only see their linked patients now based on backend logic
    api.listPatients().then((res) => setPatients(res.data)).catch(() => {});
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
  };

  const handlePatientChange = (e) => {
    const patientId = e.target.value;
    setForm((f) => ({ ...f, patient_id: patientId }));
    const patient = patients.find((p) => String(p.id) === patientId);
    setMlForm({
      ...EMPTY_ML_FORM,
      gender: patient?.gender === "Female" ? "Female" : "Male",
      age: calcAge(patient?.date_of_birth),
      district: patient?.district || "",
    });
    setMlResult(null);
    setMlError("");
  };

  const handleMlChange = (e) => {
    const { name, value, type, checked } = e.target;
    setMlForm((f) => ({ ...f, [name]: type === "checkbox" ? checked : value }));
  };

  const handleRunAssessment = async () => {
    if (!form.patient_id) return;
    setMlError("");
    setMlResult(null);
    setMlLoading(true);
    try {
      const payload = { ...mlForm, patient_id: Number(form.patient_id) };
      for (const field of ML_NUMERIC_FIELDS) {
        payload[field] = Number(mlForm[field]);
      }
      const { data } = await api.predictPatientDiagnosis(payload);
      setMlResult(data);
    } catch (err) {
      setMlError(err.response?.data?.detail || "Prediction failed. Please try again.");
    } finally {
      setMlLoading(false);
    }
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
            <select name="patient_id" value={form.patient_id} onChange={handlePatientChange} required>
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
        <div className="card" style={{ maxWidth: 820, marginTop: 24 }}>
          <div className="section-title">Symptom-Based Dengue Risk Assessment (AI)</div>
          <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginTop: -6 }}>
            Enter what you observed during the consultation. Running the assessment logs an AI screening
            entry to the patient's record and — if positive — raises a district alert.
          </p>

          <div className="form-row">
            <div className="form-group">
              <label>Gender</label>
              <select name="gender" value={mlForm.gender} onChange={handleMlChange}>
                <option>Male</option>
                <option>Female</option>
              </select>
            </div>
            <div className="form-group">
              <label>Age</label>
              <input type="number" name="age" min={0} max={120} value={mlForm.age} onChange={handleMlChange} required />
            </div>
            <div className="form-group">
              <label>Days since fever onset</label>
              <input type="number" name="days_since_fever_onset" min={0} max={30} value={mlForm.days_since_fever_onset} onChange={handleMlChange} required />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>District</label>
              <input name="district" value={mlForm.district} onChange={handleMlChange} placeholder="e.g. Kathmandu" />
            </div>
            <div className="form-group">
              <label>Visit month</label>
              <select name="visit_month" value={mlForm.visit_month} onChange={handleMlChange}>
                <option value="">— Not specified —</option>
                {MONTHS.map((m) => <option key={m}>{m}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Body temperature (&deg;C)</label>
              <input type="number" step="0.1" name="body_temperature" min={35} max={42} value={mlForm.body_temperature} onChange={handleMlChange} required />
            </div>
          </div>

          <div className="form-group">
            <label>Joint pain</label>
            <select name="joint_pain" value={mlForm.joint_pain} onChange={handleMlChange}>
              <option value="No_Joint_Pain">None</option>
              <option value="Moderate">Moderate</option>
              <option value="Severe">Severe</option>
            </select>
          </div>

          <div className="section-title" style={{ marginTop: 12, fontSize: 14 }}>Symptoms</div>
          <div className="form-row">
            <MlCheckboxRow label="Headache" name="headache" form={mlForm} onChange={handleMlChange} />
            <MlCheckboxRow label="Pain behind eyes" name="retro_orbital_pain" form={mlForm} onChange={handleMlChange} />
            <MlCheckboxRow label="Muscle pain" name="myalgia" form={mlForm} onChange={handleMlChange} />
            <MlCheckboxRow label="Skin rash" name="rash" form={mlForm} onChange={handleMlChange} />
          </div>

          <div className="section-title" style={{ marginTop: 12, fontSize: 14 }}>
            Warning signs (tick any that apply — these matter most for severity)
          </div>
          <div className="form-row">
            <MlCheckboxRow label="Persistent vomiting" name="persistent_vomiting" form={mlForm} onChange={handleMlChange} />
            <MlCheckboxRow label="Abdominal pain" name="abdominal_pain" form={mlForm} onChange={handleMlChange} />
            <MlCheckboxRow label="Bleeding (gums/nose)" name="bleeding" form={mlForm} onChange={handleMlChange} />
          </div>
          <div className="form-row">
            <MlCheckboxRow label="Restlessness" name="restlessness" form={mlForm} onChange={handleMlChange} />
            <MlCheckboxRow label="Lethargy" name="lethargy" form={mlForm} onChange={handleMlChange} />
            <MlCheckboxRow label="Liver enlargement" name="liver_enlargement" form={mlForm} onChange={handleMlChange} />
          </div>

          <div className="section-title" style={{ marginTop: 12, fontSize: 14 }}>History &amp; comorbidities</div>
          <div className="form-row">
            <MlCheckboxRow label="Previous dengue" name="previous_dengue_history" form={mlForm} onChange={handleMlChange} />
            <MlCheckboxRow label="Diabetes" name="diabetes" form={mlForm} onChange={handleMlChange} />
            <MlCheckboxRow label="Hypertension" name="hypertension" form={mlForm} onChange={handleMlChange} />
          </div>
          <div className="form-row">
            <MlCheckboxRow label="Obesity" name="obesity" form={mlForm} onChange={handleMlChange} />
            <MlCheckboxRow label="Pregnancy" name="pregnancy" form={mlForm} onChange={handleMlChange} />
          </div>

          <div className="section-title" style={{ marginTop: 24, fontSize: 14 }}>
            Lab Results (leave defaults if not tested yet — completed lab results on file override these automatically)
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Platelet count — day 1</label>
              <input type="number" name="platelet_day1" min={1} value={mlForm.platelet_day1} onChange={handleMlChange} required />
            </div>
            <div className="form-group">
              <label>Platelet count — day 3</label>
              <input type="number" name="platelet_day3" min={1} value={mlForm.platelet_day3} onChange={handleMlChange} required />
            </div>
            <div className="form-group">
              <label>WBC count</label>
              <input type="number" name="wbc_count" min={1} value={mlForm.wbc_count} onChange={handleMlChange} required />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Hematocrit % — day 1</label>
              <input type="number" step="0.1" name="hematocrit_day1" min={1} value={mlForm.hematocrit_day1} onChange={handleMlChange} required />
            </div>
            <div className="form-group">
              <label>Hematocrit % — day 3</label>
              <input type="number" step="0.1" name="hematocrit_day3" min={1} value={mlForm.hematocrit_day3} onChange={handleMlChange} required />
            </div>
          </div>
          <div className="form-row">
            <MlCheckboxRow label="NS1 positive" name="ns1" form={mlForm} onChange={handleMlChange} />
            <MlCheckboxRow label="IgG positive" name="igg" form={mlForm} onChange={handleMlChange} />
            <MlCheckboxRow label="IgM positive" name="igm" form={mlForm} onChange={handleMlChange} />
          </div>

          {mlError && <div className="error-text" style={{ marginTop: 12 }}>{String(mlError)}</div>}

          <button className="btn" type="button" disabled={mlLoading} onClick={handleRunAssessment} style={{ marginTop: 16 }}>
            {mlLoading ? "Assessing..." : "Run Risk Assessment"}
          </button>

          {mlResult && (
            <div
              className="stat-tile"
              style={{ marginTop: 16, borderColor: mlResult.dengue_positive ? "#fecaca" : "#bbf7d0" }}
            >
              <div className="label">Prediction</div>
              <div className="value" style={{ color: mlResult.dengue_positive ? "var(--color-danger)" : "var(--color-success)" }}>
                {mlResult.dengue_positive ? "Likely Dengue Positive" : "Likely Dengue Negative"}
              </div>
              <p style={{ margin: "8px 0 0" }}>
                <strong>Confidence:</strong> {(mlResult.probability * 100).toFixed(1)}%
              </p>
              <p style={{ margin: "4px 0 0" }}>
                <strong>Severity hint:</strong> {mlResult.severity_hint} ({mlResult.warning_sign_count} warning sign(s) present)
              </p>
            </div>
          )}
        </div>
      )}

      {form.patient_id && (
        <>
          <div className="section-title" style={{ marginTop: 24 }}>Patient History &amp; Conditions</div>
          <MedicalHistoryPanel patientId={form.patient_id} canEdit />
        </>
      )}
    </div>
  );
}

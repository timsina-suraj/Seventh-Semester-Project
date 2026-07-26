import { useState } from "react";
import * as api from "../../api/endpoints";

const EMPTY_FORM = {
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

const NUMERIC_FIELDS = [
  "age", "days_since_fever_onset", "body_temperature",
  "platelet_day1", "platelet_day3", "hematocrit_day1", "hematocrit_day3", "wbc_count",
];

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const CheckboxRow = ({ label, name, form, onChange }) => (
  <label className="checkbox-row">
    <input type="checkbox" name={name} checked={form[name]} onChange={onChange} /> {label}
  </label>
);

export default function DengueCheck() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm({ ...form, [name]: type === "checkbox" ? checked : value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const payload = { ...form };
      for (const field of NUMERIC_FIELDS) {
        payload[field] = Number(form[field]);
      }
      const { data } = await api.predictPatientDiagnosis(payload);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Prediction failed. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Self Dengue Check</h1>
          <div className="page-subtitle">Check your symptoms to see if you might have Dengue fever.</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="section-title">Enter your symptoms</div>
          <form onSubmit={handleSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label>Gender</label>
                <select name="gender" value={form.gender} onChange={handleChange}>
                  <option>Male</option>
                  <option>Female</option>
                </select>
              </div>
              <div className="form-group">
                <label>Age</label>
                <input type="number" name="age" min={0} max={120} value={form.age} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Days since fever onset</label>
                <input type="number" name="days_since_fever_onset" min={0} max={30} value={form.days_since_fever_onset} onChange={handleChange} required />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>District (optional)</label>
                <input name="district" value={form.district} onChange={handleChange} placeholder="e.g. Kathmandu" />
              </div>
              <div className="form-group">
                <label>Visit month (optional)</label>
                <select name="visit_month" value={form.visit_month} onChange={handleChange}>
                  <option value="">— Not specified —</option>
                  {MONTHS.map((m) => <option key={m}>{m}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>Body temperature (&deg;C)</label>
                <input type="number" step="0.1" name="body_temperature" min={35} max={42} value={form.body_temperature} onChange={handleChange} required />
              </div>
            </div>

            <div className="form-group">
              <label>Joint pain</label>
              <select name="joint_pain" value={form.joint_pain} onChange={handleChange}>
                <option value="No_Joint_Pain">None</option>
                <option value="Moderate">Moderate</option>
                <option value="Severe">Severe</option>
              </select>
            </div>

            <div className="section-title" style={{ marginTop: 12, fontSize: 14 }}>Symptoms</div>
            <div className="form-row">
              <CheckboxRow label="Headache" name="headache" form={form} onChange={handleChange} />
              <CheckboxRow label="Pain behind eyes" name="retro_orbital_pain" form={form} onChange={handleChange} />
              <CheckboxRow label="Muscle pain" name="myalgia" form={form} onChange={handleChange} />
              <CheckboxRow label="Skin rash" name="rash" form={form} onChange={handleChange} />
            </div>

            <div className="section-title" style={{ marginTop: 12, fontSize: 14 }}>
              Warning signs (tick any that apply — these matter most for severity)
            </div>
            <div className="form-row">
              <CheckboxRow label="Persistent vomiting" name="persistent_vomiting" form={form} onChange={handleChange} />
              <CheckboxRow label="Abdominal pain" name="abdominal_pain" form={form} onChange={handleChange} />
              <CheckboxRow label="Bleeding (gums/nose)" name="bleeding" form={form} onChange={handleChange} />
            </div>
            <div className="form-row">
              <CheckboxRow label="Restlessness" name="restlessness" form={form} onChange={handleChange} />
              <CheckboxRow label="Lethargy" name="lethargy" form={form} onChange={handleChange} />
              <CheckboxRow label="Liver enlargement" name="liver_enlargement" form={form} onChange={handleChange} />
            </div>

            <div className="section-title" style={{ marginTop: 12, fontSize: 14 }}>History &amp; comorbidities</div>
            <div className="form-row">
              <CheckboxRow label="Previous dengue" name="previous_dengue_history" form={form} onChange={handleChange} />
              <CheckboxRow label="Diabetes" name="diabetes" form={form} onChange={handleChange} />
              <CheckboxRow label="Hypertension" name="hypertension" form={form} onChange={handleChange} />
            </div>
            <div className="form-row">
              <CheckboxRow label="Obesity" name="obesity" form={form} onChange={handleChange} />
              <CheckboxRow label="Pregnancy" name="pregnancy" form={form} onChange={handleChange} />
            </div>

            <div className="section-title" style={{ marginTop: 24, fontSize: 14 }}>
              Lab Results (leave defaults if you haven't had a blood test)
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Platelet count — day 1</label>
                <input type="number" name="platelet_day1" min={1} value={form.platelet_day1} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Platelet count — day 3</label>
                <input type="number" name="platelet_day3" min={1} value={form.platelet_day3} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>WBC count</label>
                <input type="number" name="wbc_count" min={1} value={form.wbc_count} onChange={handleChange} required />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Hematocrit % — day 1</label>
                <input type="number" step="0.1" name="hematocrit_day1" min={1} value={form.hematocrit_day1} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Hematocrit % — day 3</label>
                <input type="number" step="0.1" name="hematocrit_day3" min={1} value={form.hematocrit_day3} onChange={handleChange} required />
              </div>
            </div>
            <div className="form-row">
              <CheckboxRow label="NS1 positive" name="ns1" form={form} onChange={handleChange} />
              <CheckboxRow label="IgG positive" name="igg" form={form} onChange={handleChange} />
              <CheckboxRow label="IgM positive" name="igm" form={form} onChange={handleChange} />
            </div>

            {error && <div className="error-text">{String(error)}</div>}
            <button className="btn" type="submit" disabled={loading} style={{ marginTop: 16 }}>
              {loading ? "Checking..." : "Check Symptoms"}
            </button>
          </form>
        </div>

        <div className="card">
          <div className="section-title">Result</div>
          {result ? (
            <>
              <div
                className="stat-tile"
                style={{ marginBottom: 16, borderColor: result.dengue_positive ? "#fecaca" : "#bbf7d0" }}
              >
                <div className="label">Prediction</div>
                <div className="value" style={{ color: result.dengue_positive ? "var(--color-danger)" : "var(--color-success)" }}>
                  {result.dengue_positive ? "Likely Dengue Positive" : "Likely Dengue Negative"}
                </div>
              </div>

              <p><strong>Confidence:</strong> {(result.probability * 100).toFixed(1)}%</p>
              <p><strong>Severity hint:</strong> {result.severity_hint} ({result.warning_sign_count} warning sign(s) present)</p>

              {result.dengue_positive && (
                <div style={{ padding: 16, background: "#fef2f2", color: "#991b1b", borderRadius: 8, marginTop: 16, border: "1px solid #fecaca" }}>
                  <h3 style={{ marginTop: 0 }}>⚠️ Please visit a hospital</h3>
                  <p>Based on your symptoms, there is a high likelihood of Dengue fever. Our staff has been alerted.</p>
                  <p>Please visit your nearest hospital or clinic immediately for a proper medical diagnosis.</p>
                </div>
              )}

              {!result.dengue_positive && (
                <p style={{ color: "var(--color-text-muted)" }}>
                  Your symptoms do not strongly indicate Dengue fever. However, if you feel unwell, please consult a doctor.
                </p>
              )}
            </>
          ) : (
            <div className="empty-state">Fill in your symptoms and click Check to see results.</div>
          )}
        </div>
      </div>
    </div>
  );
}

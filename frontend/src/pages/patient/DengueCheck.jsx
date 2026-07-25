import { useState } from "react";
import * as api from "../../api/endpoints";
import { useNavigate } from "react-router-dom";

const EMPTY_FORM = {
  gender: "Male",
  age: "",
  fever_duration: "",
  body_temperature: "",
  platelet_count: "250000",
  wbc_count: "7000",
  joint_pain: "None",
  headache: false,
  retro_orbital_pain: false,
  myalgia: false,
  rash: false,
};

export default function DengueCheck() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

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
      const { data } = await api.predictPatientDiagnosis({
        ...form,
        age: Number(form.age),
        fever_duration: Number(form.fever_duration),
        body_temperature: Number(form.body_temperature),
        platelet_count: Number(form.platelet_count),
        wbc_count: Number(form.wbc_count),
      });
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
                <label>Fever duration (days)</label>
                <input type="number" name="fever_duration" min={0} max={30} value={form.fever_duration} onChange={handleChange} required />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Body temperature (&deg;C)</label>
                <input type="number" step="0.1" name="body_temperature" min={35} max={42} value={form.body_temperature} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Joint pain</label>
                <select name="joint_pain" value={form.joint_pain} onChange={handleChange}>
                  <option>None</option>
                  <option>Moderate</option>
                  <option>Severe</option>
                </select>
              </div>
            </div>

            <div className="section-title" style={{ marginTop: 12, fontSize: 14 }}>Symptoms</div>
            <div className="form-row">
              <label className="checkbox-row"><input type="checkbox" name="headache" checked={form.headache} onChange={handleChange} /> Headache</label>
              <label className="checkbox-row"><input type="checkbox" name="retro_orbital_pain" checked={form.retro_orbital_pain} onChange={handleChange} /> Pain behind eyes</label>
              <label className="checkbox-row"><input type="checkbox" name="myalgia" checked={form.myalgia} onChange={handleChange} /> Muscle pain</label>
              <label className="checkbox-row"><input type="checkbox" name="rash" checked={form.rash} onChange={handleChange} /> Skin Rash</label>
            </div>

            <div className="section-title" style={{ marginTop: 24, fontSize: 14 }}>Lab Results (Leave as is if you haven't done a blood test)</div>
            <div className="form-row">
              <div className="form-group">
                <label>Platelet count</label>
                <input type="number" name="platelet_count" min={1} value={form.platelet_count} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>WBC count</label>
                <input type="number" name="wbc_count" min={1} value={form.wbc_count} onChange={handleChange} required />
              </div>
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

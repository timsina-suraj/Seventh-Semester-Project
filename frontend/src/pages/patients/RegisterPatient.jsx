import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../../api/endpoints";

const EMPTY_FORM = {
  full_name: "",
  email: "",
  date_of_birth: "",
  gender: "Female",
  blood_group: "Unknown",
  district: "",
  province: "",
  municipality: "",
  phone: "",
  emergency_contact: "",
  allergies: "",
};

const BLOOD_GROUPS = ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

export default function RegisterPatient() {
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [lastCreated, setLastCreated] = useState(null);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setCreating(true);
    setError("");
    setLastCreated(null);
    try {
      const { data } = await api.createPatient(form);
      setLastCreated({ email: data.login_email, patientNumber: data.patient_number });
      setForm(EMPTY_FORM);
    } catch (err) {
      setError(
        err.response?.data?.detail?.[0]?.msg ||
          err.response?.data?.detail ||
          "Could not register patient."
      );
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Register Patient</h1>
        </div>
        <button className="btn secondary" onClick={() => navigate("/patients")}>
          ← View All Patients
        </button>
      </div>

      <div className="card" style={{ maxWidth: 560 }}>
        {lastCreated && (
          <div
            className="card"
            style={{ background: "#eff6ff", border: "1px solid #bfdbfe", marginBottom: 20 }}
          >
            <div className="section-title" style={{ marginTop: 0 }}>
              ✅ Patient registered — {lastCreated.patientNumber}
            </div>
            <p style={{ fontSize: 13, margin: "4px 0" }}>
              A registration email has been sent to <strong>{lastCreated.email}</strong>. They'll receive a
              one-time login code the first time they sign in with this email.
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Full name</label>
            <input name="full_name" value={form.full_name} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input type="email" name="email" value={form.email} onChange={handleChange} required />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Date of birth</label>
              <input type="date" name="date_of_birth" value={form.date_of_birth} onChange={handleChange} required />
            </div>
            <div className="form-group">
              <label>Gender</label>
              <select name="gender" value={form.gender} onChange={handleChange}>
                <option>Female</option>
                <option>Male</option>
                <option>Other</option>
              </select>
            </div>
          </div>
          <div className="form-group">
            <label>Blood group</label>
            <select name="blood_group" value={form.blood_group} onChange={handleChange}>
              {BLOOD_GROUPS.map((bg) => (
                <option key={bg}>{bg}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>District</label>
            <input
              name="district"
              value={form.district}
              onChange={handleChange}
              required
              placeholder="e.g. Kathmandu"
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Province</label>
              <input name="province" value={form.province} onChange={handleChange} placeholder="e.g. Bagmati" />
            </div>
            <div className="form-group">
              <label>Municipality</label>
              <input name="municipality" value={form.municipality} onChange={handleChange} placeholder="e.g. Baneshwor" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Phone</label>
              <input name="phone" value={form.phone} onChange={handleChange} placeholder="98XXXXXXXX" />
            </div>
            <div className="form-group">
              <label>Emergency contact</label>
              <input name="emergency_contact" value={form.emergency_contact} onChange={handleChange} placeholder="98XXXXXXXX" />
            </div>
          </div>
          <div className="form-group">
            <label>Allergies</label>
            <input name="allergies" value={form.allergies} onChange={handleChange} placeholder="e.g. Penicillin (optional)" />
          </div>
          {error && <div className="error-text">{String(error)}</div>}
          <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
            <button className="btn" type="submit" disabled={creating}>
              {creating ? "Saving..." : "Register patient"}
            </button>
            <button
              className="btn secondary"
              type="button"
              onClick={() => navigate("/patients")}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

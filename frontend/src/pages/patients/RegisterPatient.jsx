import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../../api/endpoints";

const EMPTY_FORM = { name: "", email: "", address: "", phone: "", age: "", gender: "Female", district: "" };

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
      const { data } = await api.createPatient({ ...form, age: Number(form.age) });
      setLastCreated({ email: data.login_email, temporary_password: data.temporary_password });
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
              ✅ Patient account created
            </div>
            <p style={{ fontSize: 13, margin: "4px 0" }}>
              Share this one-time password with <strong>{lastCreated.email}</strong> — it will not
              be shown again. They'll be required to set their own password on first login.
            </p>
            <code style={{ fontSize: 16, fontWeight: 700, letterSpacing: 1 }}>
              {lastCreated.temporary_password}
            </code>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Full name</label>
            <input name="name" value={form.name} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label>Email</label>
            <input type="email" name="email" value={form.email} onChange={handleChange} required />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Age</label>
              <input
                type="number"
                name="age"
                min={0}
                max={120}
                value={form.age}
                onChange={handleChange}
                required
              />
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
            <label>District</label>
            <input
              name="district"
              value={form.district}
              onChange={handleChange}
              required
              placeholder="e.g. Kathmandu"
            />
          </div>
          <div className="form-group">
            <label>Phone</label>
            <input name="phone" value={form.phone} onChange={handleChange} placeholder="98XXXXXXXX" />
          </div>
          <div className="form-group">
            <label>Address</label>
            <input name="address" value={form.address} onChange={handleChange} />
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

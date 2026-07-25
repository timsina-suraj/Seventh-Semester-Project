import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../../api/endpoints";

const EMPTY_FORM = { full_name: "", specialization: "General Physician", phone: "", is_available: true };

export default function AddDoctor() {
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm({ ...form, [name]: type === "checkbox" ? checked : value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.createDoctor(form);
      navigate("/doctors");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add doctor.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Add Doctor</h1>
        </div>
        <button className="btn secondary" onClick={() => navigate("/doctors")}>
          ← View All Doctors
        </button>
      </div>

      <div className="card" style={{ maxWidth: 560 }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Full name</label>
            <input name="full_name" value={form.full_name} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label>Specialization</label>
            <input name="specialization" value={form.specialization} onChange={handleChange} />
          </div>
          <div className="form-group">
            <label>Phone</label>
            <input name="phone" value={form.phone} onChange={handleChange} />
          </div>
          <div className="checkbox-row" style={{ marginBottom: 14 }}>
            <input
              type="checkbox"
              name="is_available"
              checked={form.is_available}
              onChange={handleChange}
              id="is_available"
            />
            <label htmlFor="is_available">Available for appointments</label>
          </div>
          {error && <div className="error-text">{error}</div>}
          <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
            <button className="btn" type="submit" disabled={saving}>
              {saving ? "Saving..." : "Add doctor"}
            </button>
            <button className="btn secondary" type="button" onClick={() => navigate("/doctors")}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

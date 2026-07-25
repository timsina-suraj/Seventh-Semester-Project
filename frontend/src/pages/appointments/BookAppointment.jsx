import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../../api/endpoints";

const EMPTY_FORM = { patient_id: "", doctor_id: "", scheduled_at: "", reason: "" };

export default function BookAppointment() {
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.listPatients().then((res) => setPatients(res.data));
    api.listDoctors().then((res) => setDoctors(res.data));
  }, []);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.createAppointment({
        patient_id: Number(form.patient_id),
        doctor_id: Number(form.doctor_id),
        scheduled_at: new Date(form.scheduled_at).toISOString(),
        reason: form.reason || null,
      });
      navigate("/appointments");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create appointment.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Book Appointment</h1>
        </div>
        <button className="btn secondary" onClick={() => navigate("/appointments")}>
          ← View All Appointments
        </button>
      </div>

      <div className="card" style={{ maxWidth: 560 }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Patient</label>
            <select name="patient_id" value={form.patient_id} onChange={handleChange} required>
              <option value="">Select patient</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.district})
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Doctor</label>
            <select name="doctor_id" value={form.doctor_id} onChange={handleChange} required>
              <option value="">Select doctor</option>
              {doctors.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.full_name} — {d.specialization}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Date &amp; time</label>
            <input
              type="datetime-local"
              name="scheduled_at"
              value={form.scheduled_at}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label>Reason</label>
            <input name="reason" value={form.reason} onChange={handleChange} />
          </div>
          {error && <div className="error-text">{error}</div>}
          <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
            <button className="btn" type="submit" disabled={saving}>
              {saving ? "Booking..." : "Book appointment"}
            </button>
            <button className="btn secondary" type="button" onClick={() => navigate("/appointments")}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

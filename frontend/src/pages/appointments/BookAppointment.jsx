import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../../api/endpoints";

const EMPTY_FORM = { patient_id: "", doctor_id: "", date: "", time: "", reason: "" };

export default function BookAppointment() {
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [availableTimes, setAvailableTimes] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.listPatients().then((res) => setPatients(res.data));
    api.listDoctors().then((res) => setDoctors(res.data));
  }, []);

  useEffect(() => {
    if (!form.doctor_id || !form.date) {
      setAvailableTimes([]);
      return;
    }
    setSlotsLoading(true);
    api
      .getAvailableSlots(form.doctor_id, form.date)
      .then((res) => setAvailableTimes(res.data.available_times))
      .catch(() => setAvailableTimes([]))
      .finally(() => setSlotsLoading(false));
  }, [form.doctor_id, form.date]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value, ...(name === "doctor_id" || name === "date" ? { time: "" } : {}) }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.createAppointment({
        patient_id: Number(form.patient_id),
        doctor_id: Number(form.doctor_id),
        appointment_date: `${form.date}T${form.time}`,
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
                  {p.full_name} ({p.district})
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
            <label>Date</label>
            <input type="date" name="date" value={form.date} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label>Time</label>
            <select name="time" value={form.time} onChange={handleChange} required disabled={!form.doctor_id || !form.date}>
              <option value="">
                {slotsLoading
                  ? "Loading available times…"
                  : !form.doctor_id || !form.date
                  ? "Select a doctor and date first"
                  : availableTimes.length === 0
                  ? "No open slots on this date"
                  : "Select a time"}
              </option>
              {availableTimes.map((t) => (
                <option key={t} value={t}>
                  {t.slice(0, 5)}
                </option>
              ))}
            </select>
            <p style={{ fontSize: 12, color: "var(--color-text-muted)", marginTop: 4 }}>
              Only shows times inside the doctor's declared availability that aren't already booked.
            </p>
          </div>
          <div className="form-group">
            <label>Reason</label>
            <input name="reason" value={form.reason} onChange={handleChange} />
          </div>
          {error && <div className="error-text">{error}</div>}
          <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
            <button className="btn" type="submit" disabled={saving || !form.time}>
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

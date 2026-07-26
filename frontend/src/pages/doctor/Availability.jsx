import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const EMPTY_FORM = { day_of_week: "0", start_time: "10:00", end_time: "16:00" };

export default function Availability() {
  const [doctorId, setDoctorId] = useState(null);
  const [slots, setSlots] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const loadSlots = (id) => {
    api.listAvailability(id).then((res) => setSlots(res.data)).catch(() => setSlots([]));
  };

  useEffect(() => {
    api.getMyDoctorProfile().then((res) => {
      setDoctorId(res.data.id);
      loadSlots(res.data.id);
    }).catch(() => setError("Could not load your doctor profile."));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api.addAvailability(doctorId, {
        day_of_week: Number(form.day_of_week),
        start_time: `${form.start_time}:00`,
        end_time: `${form.end_time}:00`,
      });
      setForm(EMPTY_FORM);
      loadSlots(doctorId);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add that slot.");
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async (slotId) => {
    await api.removeAvailability(doctorId, slotId);
    loadSlots(doctorId);
  };

  const slotsByDay = DAYS.map((label, index) => ({
    label,
    slots: slots.filter((s) => s.day_of_week === index).sort((a, b) => a.start_time.localeCompare(b.start_time)),
  }));

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>My Availability</h1>
          <div className="page-subtitle">Set the weekly hours patients can book appointments with you.</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="section-title" style={{ marginTop: 0 }}>Add a slot</div>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Day</label>
              <select value={form.day_of_week} onChange={(e) => setForm({ ...form, day_of_week: e.target.value })}>
                {DAYS.map((label, index) => (
                  <option key={label} value={index}>{label}</option>
                ))}
              </select>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Start time</label>
                <input type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>End time</label>
                <input type="time" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} required />
              </div>
            </div>
            {error && <div className="error-text">{error}</div>}
            <button className="btn" type="submit" disabled={saving || !doctorId}>
              {saving ? "Adding..." : "Add slot"}
            </button>
          </form>
        </div>

        <div className="card">
          <div className="section-title" style={{ marginTop: 0 }}>Weekly schedule</div>
          {slotsByDay.every((d) => d.slots.length === 0) ? (
            <div className="empty-state">No availability set yet — add a slot to start accepting bookings.</div>
          ) : (
            slotsByDay.map(({ label, slots: daySlots }) => (
              daySlots.length > 0 && (
                <div key={label} style={{ marginBottom: 14 }}>
                  <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>{label}</div>
                  {daySlots.map((s) => (
                    <div key={s.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 0", borderBottom: "1px solid var(--color-border)" }}>
                      <span>{s.start_time.slice(0, 5)} – {s.end_time.slice(0, 5)}</span>
                      <button className="btn danger" style={{ padding: "3px 10px", fontSize: 12 }} onClick={() => handleRemove(s.id)}>
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )
            ))
          )}
        </div>
      </div>
    </div>
  );
}

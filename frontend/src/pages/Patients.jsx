import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../api/endpoints";
import { useAuth } from "../auth/AuthContext.jsx";
import useDebouncedValue from "../hooks/useDebouncedValue.js";
import Modal from "../components/Modal.jsx";

const BLOOD_GROUPS = ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];

function EditPatientModal({ patient, onClose, onSaved }) {
  const [form, setForm] = useState({
    full_name: patient.full_name || "",
    date_of_birth: patient.date_of_birth || "",
    gender: patient.gender || "Other",
    blood_group: patient.blood_group || "Unknown",
    district: patient.district || "",
    province: patient.province || "",
    municipality: patient.municipality || "",
    phone: patient.phone || "",
    emergency_contact: patient.emergency_contact || "",
    allergies: patient.allergies || "",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await api.updatePatient(patient.id, form);
      onSaved();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save changes.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title={`Edit ${patient.patient_number}`} onClose={onClose} maxWidth={560}>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Full name</label>
          <input name="full_name" value={form.full_name} onChange={handleChange} required />
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
          <input name="district" value={form.district} onChange={handleChange} required />
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Province</label>
            <input name="province" value={form.province} onChange={handleChange} />
          </div>
          <div className="form-group">
            <label>Municipality</label>
            <input name="municipality" value={form.municipality} onChange={handleChange} />
          </div>
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Phone</label>
            <input name="phone" value={form.phone} onChange={handleChange} />
          </div>
          <div className="form-group">
            <label>Emergency contact</label>
            <input name="emergency_contact" value={form.emergency_contact} onChange={handleChange} />
          </div>
        </div>
        <div className="form-group">
          <label>Allergies</label>
          <input name="allergies" value={form.allergies} onChange={handleChange} />
        </div>
        {error && <div className="error-text">{error}</div>}
        <button className="btn" type="submit" disabled={saving}>
          {saving ? "Saving..." : "Save changes"}
        </button>
      </form>
    </Modal>
  );
}

export default function Patients() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const canManage = user.role === "admin" || user.role === "receptionist";
  const canDelete = user.role === "admin";
  const [patients, setPatients] = useState([]);
  const [search, setSearch] = useState("");
  const [bloodGroupFilter, setBloodGroupFilter] = useState("");
  const debouncedSearch = useDebouncedValue(search);
  const [editingPatient, setEditingPatient] = useState(null);
  const [actionError, setActionError] = useState("");

  const load = () =>
    api
      .listPatients({ search: debouncedSearch || undefined, blood_group: bloodGroupFilter || undefined })
      .then((res) => setPatients(res.data));

  useEffect(() => {
    load();
  }, [debouncedSearch, bloodGroupFilter]);

  const handleDelete = async (patient) => {
    if (!window.confirm(`Delete patient ${patient.full_name} (${patient.patient_number})? This cannot be undone.`)) {
      return;
    }
    setActionError("");
    try {
      await api.deletePatient(patient.id);
      load();
    } catch (err) {
      setActionError(err.response?.data?.detail || "Could not delete that patient.");
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Patients</h1>
        </div>
        {canManage && (
          <button className="btn" onClick={() => navigate("/patients/register")}>
            + Register Patient
          </button>
        )}
      </div>

      {actionError && <div className="error-text" style={{ marginBottom: 12 }}>{actionError}</div>}

      <div className="card">
        <div className="page-header" style={{ marginBottom: 12 }}>
          <div className="section-title" style={{ margin: 0 }}>All patients ({patients.length})</div>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              type="text"
              placeholder="Search by name or patient #..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ maxWidth: 260 }}
            />
            <select value={bloodGroupFilter} onChange={(e) => setBloodGroupFilter(e.target.value)}>
              <option value="">All blood groups</option>
              {BLOOD_GROUPS.map((bg) => (
                <option key={bg} value={bg}>{bg}</option>
              ))}
            </select>
          </div>
        </div>
        <table>
          <thead>
            <tr>
              <th>Patient #</th>
              <th>Name</th>
              <th>Gender</th>
              <th>Blood Group</th>
              <th>District</th>
              <th>Phone</th>
              {canManage && <th>Login</th>}
              {canManage && <th></th>}
            </tr>
          </thead>
          <tbody>
            {patients.map((p) => (
              <tr key={p.id}>
                <td>{p.patient_number}</td>
                <td>{p.full_name}</td>
                <td>{p.gender}</td>
                <td>{p.blood_group}</td>
                <td>{p.district}</td>
                <td>{p.phone || "—"}</td>
                {canManage && (
                  <td>
                    {p.login_email
                      ? `${p.login_email} (${p.must_change_password ? "pending first login" : "set"})`
                      : "—"}
                  </td>
                )}
                {canManage && (
                  <td style={{ display: "flex", gap: 6 }}>
                    <button className="btn secondary" onClick={() => setEditingPatient(p)}>
                      Edit
                    </button>
                    {canDelete && (
                      <button className="btn danger" onClick={() => handleDelete(p)}>
                        Delete
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
            {patients.length === 0 && (
              <tr>
                <td colSpan={canManage ? 8 : 6} className="empty-state">
                  No patients registered yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {editingPatient && (
        <EditPatientModal
          patient={editingPatient}
          onClose={() => setEditingPatient(null)}
          onSaved={() => {
            setEditingPatient(null);
            load();
          }}
        />
      )}
    </div>
  );
}

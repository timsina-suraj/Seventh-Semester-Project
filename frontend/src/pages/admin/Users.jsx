import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";
import Modal from "../../components/Modal.jsx";

const EMPTY_FORM = {
  email: "",
  role: "doctor",
  full_name: "",
  department: "",
  specialization: "",
  license_number: "",
  shift: "Morning",
};

const ROLE_LABELS = {
  admin: "Administrator",
  doctor: "Doctor",
  nurse: "Nurse",
  receptionist: "Receptionist",
  lab_technician: "Lab Technician",
  patient: "Patient",
};

const PROFILE_LIST_LOADERS = {
  doctor: api.listDoctors,
  nurse: api.listNurseProfiles,
  receptionist: api.listReceptionistProfiles,
  lab_technician: api.listLabTechnicianProfiles,
};

const PROFILE_UPDATERS = {
  doctor: api.updateDoctor,
  nurse: api.updateNurseProfile,
  receptionist: api.updateReceptionistProfile,
  lab_technician: api.updateLabTechnicianProfile,
};

function EditProfileModal({ user, onClose, onSaved }) {
  const [form, setForm] = useState({
    full_name: user.full_name || "",
    department: user.department || "",
    specialization: user.specialization || "",
    license_number: user.license_number || "",
    shift: user.shift || "Morning",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const updater = PROFILE_UPDATERS[user.role];
      const payload = { full_name: form.full_name };
      if (user.role === "doctor") {
        payload.department = form.department;
        payload.specialization = form.specialization;
        payload.license_number = form.license_number;
      }
      if (user.role === "nurse") {
        payload.department = form.department;
        payload.shift = form.shift;
      }
      if (user.role === "lab_technician") {
        payload.department = form.department;
      }
      await updater(user.profileId, payload);
      onSaved();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save changes.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title={`Edit ${ROLE_LABELS[user.role] || user.role}`} onClose={onClose}>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Full name</label>
          <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
        </div>
        {(user.role === "doctor" || user.role === "nurse" || user.role === "lab_technician") && (
          <div className="form-group">
            <label>Department</label>
            <input value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} required />
          </div>
        )}
        {user.role === "doctor" && (
          <>
            <div className="form-group">
              <label>Specialization</label>
              <input value={form.specialization} onChange={(e) => setForm({ ...form, specialization: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>License number</label>
              <input value={form.license_number} onChange={(e) => setForm({ ...form, license_number: e.target.value })} required />
            </div>
          </>
        )}
        {user.role === "nurse" && (
          <div className="form-group">
            <label>Shift</label>
            <select value={form.shift} onChange={(e) => setForm({ ...form, shift: e.target.value })}>
              <option value="Morning">Morning</option>
              <option value="Evening">Evening</option>
              <option value="Night">Night</option>
            </select>
          </div>
        )}
        {error && <div className="error-text">{error}</div>}
        <button className="btn" type="submit" disabled={saving}>
          {saving ? "Saving..." : "Save changes"}
        </button>
      </form>
    </Modal>
  );
}

export default function Users() {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [lastCreated, setLastCreated] = useState(null); // { email }
  const [actionError, setActionError] = useState("");
  const [activeTab, setActiveTab] = useState("manage");
  const [editingUser, setEditingUser] = useState(null);
  const [resetNotice, setResetNotice] = useState("");
  const [confirmingReset, setConfirmingReset] = useState(null);
  const [resetting, setResetting] = useState(false);

  const load = async () => {
    const [usersRes, ...profileResults] = await Promise.all([
      api.listUsers(),
      ...Object.values(PROFILE_LIST_LOADERS).map((loader) => loader().catch(() => ({ data: [] }))),
    ]);
    const roles = Object.keys(PROFILE_LIST_LOADERS);
    const profilesByUserId = {};
    roles.forEach((role, i) => {
      profileResults[i].data.forEach((profile) => {
        profilesByUserId[profile.user_id] = { ...profile, role };
      });
    });

    setUsers(
      usersRes.data.map((u) => {
        const profile = profilesByUserId[u.id];
        return {
          ...u,
          profileId: profile?.id ?? null,
          employee_id: profile?.employee_id ?? null,
          full_name: profile?.full_name ?? null,
          department: profile?.department ?? null,
          specialization: profile?.specialization ?? null,
          license_number: profile?.license_number ?? null,
          shift: profile?.shift ?? null,
        };
      })
    );
  };

  useEffect(() => {
    load();
  }, []);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setCreating(true);
    setError("");
    setLastCreated(null);
    try {
      // Only send the fields relevant to the selected role — the backend
      // validates required fields per role (StaffCreate).
      const payload = { email: form.email, role: form.role, full_name: form.full_name };
      if (form.role === "doctor") {
        payload.department = form.department;
        payload.specialization = form.specialization;
        payload.license_number = form.license_number;
      }
      if (form.role === "nurse") {
        payload.department = form.department;
        payload.shift = form.shift;
      }
      if (form.role === "lab_technician") {
        payload.department = form.department;
      }
      const { data } = await api.registerUser(payload);
      setLastCreated({ email: data.email });
      setForm(EMPTY_FORM);
      load();
    } catch (err) {
      setError(
        err.response?.data?.detail?.[0]?.msg || err.response?.data?.detail || "Could not create user."
      );
    } finally {
      setCreating(false);
    }
  };

  const handleToggle = async (id) => {
    setActionError("");
    try {
      await api.toggleUserActive(id);
      load();
    } catch (err) {
      setActionError(err.response?.data?.detail || "Could not update that account.");
    }
  };

  const handleResetPassword = (u) => setConfirmingReset(u);

  const confirmResetPassword = async () => {
    const u = confirmingReset;
    if (!u) return;
    setActionError("");
    setResetNotice("");
    setResetting(true);
    try {
      await api.adminResetPassword(u.id);
      setResetNotice(`Password reset for ${u.email} — they'll get a login code by email the next time they sign in.`);
      setConfirmingReset(null);
      load();
    } catch (err) {
      setActionError(err.response?.data?.detail || "Could not reset that account's password.");
      setConfirmingReset(null);
    } finally {
      setResetting(false);
    }
  };

  const roleDetail = (u) => {
    if (u.role === "doctor") return `${u.department || "—"} · ${u.specialization || "—"}`;
    if (u.role === "nurse") return `${u.department || "—"} · ${u.shift || "—"}`;
    if (u.role === "lab_technician") return u.department || "—";
    return "—";
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Users</h1>
          <div className="page-subtitle">Create and manage staff accounts</div>
        </div>
      </div>

      <div className="tabs" style={{ display: "flex", gap: "16px", marginBottom: "20px", borderBottom: "1px solid var(--color-border)", paddingBottom: "10px" }}>
        <button
          className={`btn ${activeTab === "manage" ? "" : "secondary"}`}
          onClick={() => setActiveTab("manage")}
        >
          Manage Staff Accounts
        </button>
        <button
          className={`btn ${activeTab === "create" ? "" : "secondary"}`}
          onClick={() => setActiveTab("create")}
        >
          Create Staff Account
        </button>
      </div>

      <div style={{ display: "block" }}>
        {activeTab === "create" && (
          <div className="card">
            <div className="section-title">Create staff account</div>
            <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginTop: -6 }}>
              Patient accounts are created by a receptionist from the patient registration page, and additional
              admin accounts are created via the bootstrap script — so both stay outside this form on purpose.
            </p>

            {lastCreated && (
              <div className="card" style={{ background: "#eff6ff", border: "1px solid #bfdbfe", marginBottom: 16 }}>
                <div className="section-title" style={{ marginTop: 0 }}>Account created</div>
                <p style={{ fontSize: 13, margin: "4px 0" }}>
                  A registration email has been sent to <strong>{lastCreated.email}.</strong> They'll receive a
                  one-time login code the first time they sign in.
                </p>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Email</label>
                <input type="email" name="email" value={form.email} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Full name</label>
                <input name="full_name" value={form.full_name} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select name="role" value={form.role} onChange={handleChange}>
                  <option value="doctor">Doctor</option>
                  <option value="nurse">Nurse</option>
                  <option value="receptionist">Receptionist</option>
                  <option value="lab_technician">Lab Technician</option>
                </select>
              </div>

              {form.role === "doctor" && (
                <>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Department</label>
                      <input name="department" value={form.department} onChange={handleChange} placeholder="General Medicine" required />
                    </div>
                    <div className="form-group">
                      <label>Specialization</label>
                      <input name="specialization" value={form.specialization} onChange={handleChange} placeholder="General Physician" required />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>License number</label>
                    <input name="license_number" value={form.license_number} onChange={handleChange} required />
                  </div>
                </>
              )}

              {form.role === "nurse" && (
                <div className="form-row">
                  <div className="form-group">
                    <label>Department</label>
                    <input name="department" value={form.department} onChange={handleChange} placeholder="General Ward" required />
                  </div>
                  <div className="form-group">
                    <label>Shift</label>
                    <select name="shift" value={form.shift} onChange={handleChange}>
                      <option value="Morning">Morning</option>
                      <option value="Evening">Evening</option>
                      <option value="Night">Night</option>
                    </select>
                  </div>
                </div>
              )}

              {form.role === "lab_technician" && (
                <div className="form-group">
                  <label>Department</label>
                  <input name="department" value={form.department} onChange={handleChange} placeholder="Hematology" required />
                </div>
              )}

              {error && <div className="error-text">{String(error)}</div>}
              <button className="btn" type="submit" disabled={creating}>
                {creating ? "Creating..." : "Create user"}
              </button>
            </form>
          </div>
        )}

        {activeTab === "manage" && (
          <div className="card">
            <div className="section-title">All accounts ({users.length})</div>

            {actionError && <div className="error-text" style={{ marginBottom: 8 }}>{actionError}</div>}
            {resetNotice && <div className="success-text" style={{ marginBottom: 8, color: "var(--color-success)" }}>{resetNotice}</div>}
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Details</th>
                  <th>Status</th>
                  <th>Password</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>{u.full_name || "—"}</td>
                    <td>{u.email}</td>
                    <td>{ROLE_LABELS[u.role] || u.role}</td>
                    <td style={{ fontSize: 13, color: "var(--color-text-muted)" }}>{roleDetail(u)}</td>
                    <td>{u.is_active ? "Active" : "Inactive (pending first login)"}</td>
                    <td>{u.must_change_password ? "Not set yet" : "Set"}</td>
                    <td>
                      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                        {u.profileId && PROFILE_UPDATERS[u.role] && (
                          <button className="btn secondary" onClick={() => setEditingUser(u)}>
                            Edit
                          </button>
                        )}
                        {u.is_active && u.role === "admin" ? (
                          <button className="btn secondary" disabled title="Admin accounts can't be disabled by another admin.">
                            Disable
                          </button>
                        ) : (
                          <button className="btn secondary" onClick={() => handleToggle(u.id)}>
                            {u.is_active ? "Disable" : "Enable"}
                          </button>
                        )}
                        {u.role !== "admin" && (
                          <button className="btn secondary" onClick={() => handleResetPassword(u)}>
                            Reset Password
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {editingUser && (
        <EditProfileModal
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onSaved={() => {
            setEditingUser(null);
            load();
          }}
        />
      )}

      {confirmingReset && (
        <Modal title="Reset password?" onClose={() => setConfirmingReset(null)} maxWidth={420}>
          <p style={{ fontSize: 14, marginTop: 0 }}>
            Reset <strong>{confirmingReset.email}</strong>'s password? They'll need to sign in again with a
            one-time code sent to their email.
          </p>
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 16 }}>
            <button className="btn secondary" onClick={() => setConfirmingReset(null)} disabled={resetting}>
              Cancel
            </button>
            <button className="btn" onClick={confirmResetPassword} disabled={resetting}>
              {resetting ? "Resetting..." : "Reset password"}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}

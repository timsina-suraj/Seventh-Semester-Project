import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";

const EMPTY_FORM = { email: "", role: "receptionist", full_name: "", specialization: "", phone: "" };

export default function Users() {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [lastCreated, setLastCreated] = useState(null); // { email }
  const [toggleError, setToggleError] = useState("");
  const [activeTab, setActiveTab] = useState("manage");

  const load = () => api.listUsers().then((res) => setUsers(res.data));

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
      const { data } = await api.registerUser(form);
      setLastCreated({ email: data.email });
      setForm(EMPTY_FORM);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create user.");
    } finally {
      setCreating(false);
    }
  };

  const handleToggle = async (id) => {
    setToggleError("");
    try {
      await api.toggleUserActive(id);
      load();
    } catch (err) {
      setToggleError(err.response?.data?.detail || "Could not update that account.");
    }
  };


  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Users</h1>
          <div className="page-subtitle">Create and manage staff accounts (admin, doctor, receptionist)</div>
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
              Patient accounts are created by a receptionist from the patient registration page, so a patient's
              login and their record always stay linked.
            </p>

            {lastCreated && (
              <div className="card" style={{ background: "#eff6ff", border: "1px solid #bfdbfe", marginBottom: 16 }}>
                <div className="section-title" style={{ marginTop: 0 }}>Account created</div>
                <p style={{ fontSize: 13, margin: "4px 0" }}>
                  An email containing a one-time password has been sent to <strong>{lastCreated.email}.</strong>
                </p>
              </div>
            )}

            <form onSubmit={handleSubmit}>

              <div className="form-group">
                <label>Email</label>
                <input type="email" name="email" value={form.email} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select name="role" value={form.role} onChange={handleChange}>
                  <option value="admin">Administrator</option>
                  <option value="doctor">Doctor</option>
                  <option value="receptionist">Receptionist</option>
                </select>
              </div>

              {form.role === "doctor" && (
                <>
                  <div className="form-group">
                    <label>Full name</label>
                    <input name="full_name" value={form.full_name} onChange={handleChange} placeholder="Dr. ..." />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Specialization</label>
                      <input name="specialization" value={form.specialization} onChange={handleChange} placeholder="General Physician" />
                    </div>
                    <div className="form-group">
                      <label>Phone</label>
                      <input name="phone" value={form.phone} onChange={handleChange} />
                    </div>
                  </div>
                </>
              )}

              {error && <div className="error-text">{error}</div>}
              <button className="btn" type="submit" disabled={creating}>
                {creating ? "Creating..." : "Create user"}
              </button>
            </form>
          </div>
        )}

        {activeTab === "manage" && (
          <div className="card">
            <div className="section-title">All staff accounts</div>
            

            {toggleError && <div className="error-text" style={{ marginBottom: 8 }}>{toggleError}</div>}
            <table>
              <thead>
                <tr>

                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Password</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>

                    <td>{u.email}</td>
                    <td>{u.role}</td>
                    <td>{u.is_active ? "Active" : "Disabled"}</td>
                    <td>{u.must_change_password ? "Temporary (unset)" : "Set"}</td>
                    <td>
                      <div style={{ display: "flex", gap: "6px" }}>
                        {u.is_active && u.role === "admin" ? (
                          <button className="btn secondary" disabled title="Admin accounts can't be disabled by another admin.">
                            Disable
                          </button>
                        ) : (
                          <button className="btn secondary" onClick={() => handleToggle(u.id)}>
                            {u.is_active ? "Disable" : "Enable"}
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
    </div>
  );
}
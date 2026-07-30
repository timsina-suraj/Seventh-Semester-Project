import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../api/endpoints";
import { useAuth } from "../auth/AuthContext.jsx";
import { PASSWORD_RULES_HINT, validatePasswordStrength } from "../utils/passwordValidation.js";

export default function ChangePassword() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const isMustChange = user?.mustChangePassword;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    const strengthError = validatePasswordStrength(newPassword);
    if (strengthError) {
      setError(strengthError);
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match.");
      return;
    }
    if (!isMustChange && newPassword === currentPassword) {
      setError("New password must be different from the current one.");
      return;
    }

    setSaving(true);
    try {
      if (isMustChange) {
        // First-time setup after OTP verification — there's no prior
        // password to confirm, the OTP already proved identity.
        await api.setInitialPassword({ new_password: newPassword });
      } else {
        await api.changePassword({ current_password: currentPassword, new_password: newPassword });
      }

      // ── Security: invalidate the current session immediately. ──────────────
      // The token in localStorage was issued with the old credential. After a
      // password change, the user must re-authenticate so the system proves
      // the right person (not a hijacked session) performed the change.
      logout();
      navigate("/login", {
        replace: true,
        state: { successMessage: "Password set successfully. Please sign in with your new password." },
      });
    } catch (err) {
      setError(err.response?.data?.detail || "Could not save password.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", alignItems: "center", justifyContent: "center", background: "var(--color-bg)" }}>
      <div className="card" style={{ maxWidth: 440, width: "100%" }}>
        <div className="section-title" style={{ marginTop: 0 }}>
          {isMustChange ? "🔑 Set your password" : "🔑 Change password"}
        </div>

        <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginTop: -6, marginBottom: 20 }}>
          {isMustChange
            ? "You're signed in with a one-time password. Choose a permanent password to continue."
            : "After changing your password you will be signed out and must sign in again with the new one."}
        </p>

        {/* Notice banner for voluntary change */}
        {!isMustChange && (
          <div style={{
            background: "#fffbeb",
            border: "1px solid #fde68a",
            borderRadius: 8,
            padding: "10px 14px",
            fontSize: 13,
            color: "#92400e",
            marginBottom: 20,
            display: "flex",
            alignItems: "flex-start",
            gap: 8,
          }}>
            <span>⚠️</span>
            <span>
              For your security, you will be <strong>automatically signed out</strong> once
              the password is saved. Sign back in with your new password.
            </span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {!isMustChange && (
            <div className="form-group">
              <label>Current password</label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                autoFocus
                autoComplete="current-password"
              />
            </div>
          )}
          <div className="form-group">
            <label>New password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              minLength={8}
              required
              autoFocus={isMustChange}
              autoComplete="new-password"
            />
            <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>{PASSWORD_RULES_HINT}</span>
          </div>
          <div className="form-group">
            <label>Confirm new password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              minLength={8}
              required
              autoComplete="new-password"
            />
          </div>

          {error && <div className="error-text">{String(error)}</div>}

          <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
            <button className="btn" type="submit" disabled={saving}>
              {saving ? "Saving…" : "Save & sign out"}
            </button>
            <button
              className="btn secondary"
              type="button"
              onClick={() => {
                if (isMustChange) {
                  logout();
                  navigate("/login", { replace: true });
                } else {
                  navigate(-1);
                }
              }}
            >
              {isMustChange ? "Log out" : "Cancel"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
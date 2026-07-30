import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../api/endpoints";
import { PASSWORD_RULES_HINT, validatePasswordStrength } from "../utils/passwordValidation.js";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  
  // Step 1 state
  const [email, setEmail] = useState("");
  const [requesting, setRequesting] = useState(false);
  const [requestError, setRequestError] = useState("");

  // Step 2 state
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [resetting, setResetting] = useState(false);
  const [resetError, setResetError] = useState("");

  const handleRequestOtp = async (e) => {
    e.preventDefault();
    setRequestError("");
    setRequesting(true);
    try {
      await api.forgotPassword({ email });
      setStep(2);
    } catch (err) {
      setRequestError(err.response?.data?.detail || "Could not request password reset.");
    } finally {
      setRequesting(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setResetError("");

    const strengthError = validatePasswordStrength(newPassword);
    if (strengthError) {
      setResetError(strengthError);
      return;
    }
    if (newPassword !== confirmPassword) {
      setResetError("New password and confirmation do not match.");
      return;
    }

    setResetting(true);
    try {
      await api.resetPasswordWithOTP({ email, otp, new_password: newPassword });
      navigate("/login", {
        replace: true,
        state: { successMessage: "Password reset successfully. Please sign in." },
      });
    } catch (err) {
      setResetError(err.response?.data?.detail || "Could not reset password. OTP may be invalid or expired.");
    } finally {
      setResetting(false);
    }
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", alignItems: "center", justifyContent: "center", background: "var(--color-bg)" }}>
      <div className="card" style={{ maxWidth: 440, width: "100%" }}>
        <div className="section-title" style={{ marginTop: 0 }}>
          {step === 1 ? "Forgot password?" : "Reset your password"}
        </div>

        {step === 1 && (
          <>
            <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginTop: -6, marginBottom: 20 }}>
              Enter your email address and we'll send you a one-time password (OTP) to reset your password.
            </p>
            <form onSubmit={handleRequestOtp}>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoFocus
                  autoComplete="email"
                />
              </div>

              {requestError && <div className="error-text">{requestError}</div>}

              <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
                <button className="btn" type="submit" disabled={requesting}>
                  {requesting ? "Sending…" : "Send Reset OTP"}
                </button>
                <button
                  className="btn secondary"
                  type="button"
                  onClick={() => navigate("/login")}
                >
                  Cancel
                </button>
              </div>
            </form>
          </>
        )}

        {step === 2 && (
          <>
            <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginTop: -6, marginBottom: 20 }}>
              An email with a one-time password has been sent to <strong>{email}</strong>. Please enter it below to choose a new password.
            </p>
            <form onSubmit={handleResetPassword}>
              <div className="form-group">
                <label>One-time password (OTP)</label>
                <input
                  type="text"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  required
                  autoFocus
                  autoComplete="off"
                />
              </div>
              <div className="form-group">
                <label>New password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  minLength={8}
                  required
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

              {resetError && <div className="error-text">{resetError}</div>}

              <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
                <button className="btn" type="submit" disabled={resetting}>
                  {resetting ? "Resetting…" : "Reset Password"}
                </button>
                <button
                  className="btn secondary"
                  type="button"
                  onClick={() => setStep(1)}
                >
                  Back
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

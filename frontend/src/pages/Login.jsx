import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";
import * as api from "../api/endpoints";

export default function Login() {
  const { login, loginWithOTP } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const successMessage = location.state?.successMessage || "";
  
  const [step, setStep] = useState(1); // 1 = email, 2 = password, 3 = otp
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handlePreLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await api.preLogin({ email });
      if (data.requires_otp) {
        setStep(3); // Go to OTP step
      } else {
        setStep(2); // Go to Password step
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Could not verify email.");
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Check your password.");
    } finally {
      setLoading(false);
    }
  };

  const handleOtpLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await loginWithOTP(email, otp);
      navigate("/change-password", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Check your OTP.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell">
      <div className="login-card">
        {/* Branding */}
        <div style={{ textAlign: "center", marginBottom: 8 }}>
          <div style={{ fontSize: 40, marginBottom: 6, filter: "drop-shadow(0 0 10px rgba(99,179,237,0.5))" }}>🛡️</div>
          <h1 style={{ margin: 0 }}>MediShield</h1>
          <p style={{ margin: "6px 0 0", color: "var(--color-text-muted)", fontSize: 13 }}>
            Intelligent Hospital Management
          </p>
        </div>

        {successMessage && step === 1 && (
          <div style={{
            background: "#ecfeff",
            border: "1px solid #a5f3fc",
            color: "#0891b2",
            padding: "10px 14px",
            borderRadius: 8,
            marginTop: 16,
            fontSize: 13,
            textAlign: "center"
          }}>
            {successMessage}
          </div>
        )}

        {step === 1 && (
          <form onSubmit={handlePreLogin}>
            <div className="form-group" style={{ marginTop: 20 }}>
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
            {error && <div className="error-text">{error}</div>}
            <button className="btn" type="submit" disabled={loading} style={{ width: "100%", marginTop: 8 }}>
              {loading ? "Checking…" : "Continue"}
            </button>
            <div style={{ marginTop: 18, borderTop: "1px solid var(--color-border)", paddingTop: 14 }}>
              <button
                type="button"
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--color-primary)",
                  fontSize: 13,
                  fontWeight: 500,
                  cursor: "pointer",
                  padding: 0,
                  textDecoration: "underline",
                }}
                onClick={() => navigate("/forgot-password")}
              >
                Forgot password?
              </button>
            </div>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={handlePasswordLogin}>
            <p style={{ fontSize: 14, marginBottom: 16, textAlign: "center" }}>
              Welcome back, <strong>{email}</strong>
            </p>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoFocus
                autoComplete="current-password"
              />
            </div>
            {error && <div className="error-text">{error}</div>}
            <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
              <button className="btn" type="submit" disabled={loading} style={{ flex: 1 }}>
                {loading ? "Signing in…" : "Sign in"}
              </button>
              <button className="btn secondary" type="button" onClick={() => { setStep(1); setPassword(""); setError(""); }}>
                Back
              </button>
            </div>
            <div style={{ marginTop: 18, borderTop: "1px solid var(--color-border)", paddingTop: 14 }}>
              <button
                type="button"
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--color-primary)",
                  fontSize: 13,
                  fontWeight: 500,
                  cursor: "pointer",
                  padding: 0,
                  textDecoration: "underline",
                }}
                onClick={() => navigate("/forgot-password")}
              >
                Forgot password?
              </button>
            </div>
          </form>
        )}

        {step === 3 && (
          <form onSubmit={handleOtpLogin}>
            <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginBottom: 16, textAlign: "center", lineHeight: 1.5 }}>
              This is your first time logging in! We've sent a one-time password to <strong>{email}</strong>.
            </p>
            <div className="form-group">
              <label>One-Time Password (OTP)</label>
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                required
                autoFocus
                autoComplete="off"
              />
            </div>
            {error && <div className="error-text">{error}</div>}
            <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
              <button className="btn" type="submit" disabled={loading} style={{ flex: 1 }}>
                {loading ? "Verifying…" : "Verify OTP"}
              </button>
              <button className="btn secondary" type="button" onClick={() => { setStep(1); setOtp(""); setError(""); }}>
                Back
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

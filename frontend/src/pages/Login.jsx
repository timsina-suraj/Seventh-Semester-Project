import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const successMessage = location.state?.successMessage || "";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell">
      <form className="login-card" onSubmit={handleLoginSubmit}>
        {/* Branding */}
        <div style={{ textAlign: "center", marginBottom: 8 }}>
          <div style={{ fontSize: 40, marginBottom: 6, filter: "drop-shadow(0 0 10px rgba(99,179,237,0.5))" }}>🛡️</div>
          <h1 style={{ margin: 0 }}>MediShield</h1>
          <p style={{ margin: "6px 0 0", color: "var(--color-text-muted)", fontSize: 13 }}>
            Intelligent Hospital Management
          </p>
        </div>

        {successMessage && (
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

        <div className="form-group" style={{ marginTop: 20 }}>
          <label>Email</label>
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
            autoComplete="email"
          />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </div>

        {error && <div className="error-text">{error}</div>}

        <button className="btn" type="submit" disabled={loading} style={{ width: "100%", marginTop: 8 }}>
          {loading ? "Signing in…" : "Sign in"}
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
    </div>
  );
}

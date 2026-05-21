import { useState, type FormEvent } from "react";
import { login } from "../api";
import "./LoginPage.css";

interface Props {
  onLogin: (token: string) => void;
}

export default function LoginPage({ onLogin }: Props) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await login(password);
      if (res.code === 200 && res.data) {
        onLogin(res.data.access_token);
      } else {
        setError(res.error_message ?? "Login failed");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-wrapper">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-logo">
          <span>🛡️</span>
        </div>
        <h1>ML Prediction System</h1>
        <p className="login-subtitle">
          Enter the secret key to access the prediction dashboard
        </p>

        <div className="login-field">
          <label htmlFor="login-password">Secret Key</label>
          <input
            id="login-password"
            type="password"
            placeholder="Enter secret key…"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
            required
          />
        </div>

        <button
          id="login-submit"
          type="submit"
          className="login-btn"
          disabled={loading || !password}
        >
          {loading ? "Authenticating…" : "Unlock Dashboard"}
        </button>

        {error && <div className="login-error">{error}</div>}
      </form>
    </div>
  );
}

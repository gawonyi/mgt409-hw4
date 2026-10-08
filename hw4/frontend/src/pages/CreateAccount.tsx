import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function CreateAccount() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ first: "", last: "", email: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [k]: e.target.value });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      await register({
        first_name: form.first.trim(),
        last_name: form.last.trim(),
        email: form.email.trim(),
        password: form.password,
      });
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create account.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="form-page">
      <h1>Create account</h1>
      <form onSubmit={onSubmit} className="form">
        <label>
          First name
          <input value={form.first} onChange={set("first")} autoComplete="given-name" required />
        </label>
        <label>
          Last name
          <input value={form.last} onChange={set("last")} autoComplete="family-name" required />
        </label>
        <label>
          Email
          <input type="email" value={form.email} onChange={set("email")} autoComplete="email" required />
        </label>
        <label>
          Password <small className="muted">(at least 8 characters)</small>
          <input type="password" value={form.password} onChange={set("password")} autoComplete="new-password" required />
        </label>
        <label>
          Confirm password
          <input type="password" value={form.confirm} onChange={set("confirm")} autoComplete="new-password" required />
        </label>
        <button type="submit" className="button" disabled={busy}>
          {busy ? "Creating account…" : "Create account"}
        </button>
        {error && <p className="error">{error}</p>}
      </form>
      <p className="muted">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </section>
  );
}

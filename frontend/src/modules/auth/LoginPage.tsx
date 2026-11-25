import { createSignal } from "solid-js";
import { login } from "./api";
import { storeLogin } from "./store";

interface Props {
  onSwitchToRegister: () => void;
}

export function LoginPage(props: Props) {
  const [email, setEmail] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [error, setError] = createSignal("");
  const [loading, setLoading] = createSignal(false);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await login(email(), password());
      storeLogin(result.access_token, result.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div class="auth-shell">
      <div class="auth-card">
        <div class="auth-logo">K8</div>
        <h1 class="auth-title">Kaiju8 Studio</h1>
        <p class="auth-subtitle">Sign in to your workspace</p>

        {error() && <div class="toast error">{error()}</div>}

        <form onSubmit={handleSubmit} class="auth-form">
          <label>
            <span>Email</span>
            <input
              id="login-email"
              name="email"
              type="email"
              value={email()}
              onInput={(e) => setEmail(e.currentTarget.value)}
              placeholder="you@example.com"
              required
            />
          </label>
          <label>
            <span>Password</span>
            <input
              id="login-password"
              name="password"
              type="password"
              value={password()}
              onInput={(e) => setPassword(e.currentTarget.value)}
              placeholder="••••••••"
              required
            />
          </label>
          <button type="submit" class="primary-button wide" disabled={loading()}>
            {loading() ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p class="auth-switch">
          No account?{" "}
          <button class="link-button" onClick={props.onSwitchToRegister}>
            Create one
          </button>
        </p>
      </div>
    </div>
  );
}

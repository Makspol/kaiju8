import { createSignal } from "solid-js";
import { register } from "./api";
import { storeLogin } from "./store";

interface Props {
  onSwitchToLogin: () => void;
}

export function RegisterPage(props: Props) {
  const [email, setEmail] = createSignal("");
  const [name, setName] = createSignal("");
  const [password, setPassword] = createSignal("");
  const [error, setError] = createSignal("");
  const [loading, setLoading] = createSignal(false);

  async function handleSubmit(e: Event) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await register(email(), name(), password());
      storeLogin(result.access_token, result.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div class="auth-shell">
      <div class="auth-card">
        <div class="auth-logo">K8</div>
        <h1 class="auth-title">Kaiju8 Studio</h1>
        <p class="auth-subtitle">Create your account</p>

        {error() && <div class="toast error">{error()}</div>}

        <form onSubmit={handleSubmit} class="auth-form">
          <label>
            <span>Name</span>
            <input
              id="register-name"
              name="name"
              type="text"
              value={name()}
              onInput={(e) => setName(e.currentTarget.value)}
              placeholder="Your name"
              required
            />
          </label>
          <label>
            <span>Email</span>
            <input
              id="register-email"
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
              id="register-password"
              name="password"
              type="password"
              value={password()}
              onInput={(e) => setPassword(e.currentTarget.value)}
              placeholder="Min. 8 characters"
              minlength="8"
              required
            />
          </label>
          <button type="submit" class="primary-button wide" disabled={loading()}>
            {loading() ? "Creating account…" : "Create account"}
          </button>
        </form>

        <p class="auth-switch">
          Have an account?{" "}
          <button class="link-button" onClick={props.onSwitchToLogin}>
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}

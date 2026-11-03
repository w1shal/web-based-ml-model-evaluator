
import { useState, type FormEvent } from "react";
import { api, type AuthUser } from "./lib/api";
import "./App.css";

type AuthMode = "login" | "register";
type Notice = { kind: "success" | "error" | "info"; text: string };

const workflow = [
  { number: "01", title: "Upload", description: "Choose your dataset" },
  { number: "02", title: "Configure", description: "Set evaluation options" },
  { number: "03", title: "Evaluate", description: "Run model checks" },
  { number: "04", title: "Results", description: "Review performance" },
];

function validateRegistration(
  username: string,
  email: string,
  password: string,
): string | null {
  if (!/^[A-Za-z0-9_.-]{3,50}$/.test(username)) {
    return "Username must be 3–50 characters using letters, numbers, dots, underscores or hyphens.";
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return "Enter a valid email address.";
  }

  if (password.length < 8) {
    return "Password must contain at least 8 characters.";
  }

  if (new TextEncoder().encode(password).length > 72) {
    return "Password must not exceed 72 UTF-8 bytes.";
  }

  if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
    return "Password must contain at least one letter and one number.";
  }

  return null;
}

export default function App() {
  const [mode, setMode] = useState<AuthMode>("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [inWorkspace, setInWorkspace] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);

  function changeMode(nextMode: AuthMode) {
    setMode(nextMode);
    setPassword("");
    setNotice(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNotice(null);

    if (mode === "register") {
      const validationError = validateRegistration(
        username.trim(),
        email.trim(),
        password,
      );

      if (validationError) {
        setNotice({ kind: "error", text: validationError });
        return;
      }
    } else if (!identifier.trim() || !password) {
      setNotice({
        kind: "error",
        text: "Enter your username or email and password.",
      });
      return;
    }

    setBusy(true);

    try {
      if (mode === "register") {
        await api.register({
          username: username.trim(),
          email: email.trim(),
          password,
        });

        setIdentifier(email.trim());
        setPassword("");
        setMode("login");
        setNotice({
          kind: "success",
          text: "Account created. Sign in with your new credentials.",
        });
      } else {
        const result = await api.login({
          identifier: identifier.trim(),
          password,
        });

        setAccessToken(result.access_token);
        setUser(result.user);
        setPassword("");
        setInWorkspace(true);
        setNotice({
          kind: "success",
          text: "You are signed in. Welcome back!",
        });
      }
    } catch (error) {
      setNotice({
        kind: "error",
        text:
          error instanceof Error
            ? error.message
            : "Something went wrong. Please try again.",
      });
    } finally {
      setBusy(false);
    }
  }

  function continueAsGuest() {
    setAccessToken(null);
    setUser(null);
    setNotice(null);
    setInWorkspace(true);
  }

  async function verifySession() {
    if (!accessToken) return;

    setBusy(true);
    setNotice(null);

    try {
      const currentUser = await api.me(accessToken);
      setUser(currentUser);
      setNotice({ kind: "success", text: "Your session is valid." });
    } catch (error) {
      setNotice({
        kind: "error",
        text:
          error instanceof Error
            ? error.message
            : "Unable to verify your session.",
      });
    } finally {
      setBusy(false);
    }
  }

  async function handleLogout() {
    const token = accessToken;
    setBusy(true);
    setNotice(null);

    let logoutNotice: Notice = {
      kind: "success",
      text: "Signed out successfully.",
    };

    try {
      if (token) await api.logout(token);
    } catch {
      logoutNotice = {
        kind: "info",
        text: "Signed out on this device, but the server could not confirm token revocation.",
      };
    } finally {
      setAccessToken(null);
      setUser(null);
      setPassword("");
      setInWorkspace(false);
      setMode("login");
      setNotice(logoutNotice);
      setBusy(false);
    }
  }

  if (inWorkspace) {
    return (
      <main className="workspace-page">
        <header className="topbar">
          <a className="brand" href="#" onClick={(event) => {
            event.preventDefault();
            setInWorkspace(false);
          }}>
            <span className="brand-mark">M</span>
            <span>Model<span className="brand-accent">Evaluator</span></span>
          </a>
          <div className="topbar-actions">
            <span className={`status-pill ${user ? "signed-in" : ""}`}>
              <span className="status-dot" />
              {user ? "Authenticated" : "Guest mode"}
            </span>
            {user ? (
              <button className="button button-dark" onClick={handleLogout} disabled={busy}>
                {busy ? "Signing out…" : "Sign out"}
              </button>
            ) : (
              <button className="button button-dark" onClick={() => setInWorkspace(false)}>
                Sign in
              </button>
            )}
          </div>
        </header>

        <section className="workspace-content">
          <span className="eyebrow">YOUR WORKSPACE</span>
          <h1>
            {user ? `Welcome, ${user.username}.` : "Your next model insight starts here."}
          </h1>
          <p className="workspace-lead">
            {user
              ? `Signed in as ${user.email}.`
              : "You are exploring as a guest. Sign-in is optional for supported guest features."}
          </p>

          {notice && (
            <div className={`notice notice-${notice.kind}`} role="status">
              {notice.text}
            </div>
          )}

          {user && (
            <section className="session-card">
              <div>
                <strong>Authentication session</strong>
                <p>Verify that the backend still accepts your access token.</p>
              </div>
              <button className="button button-outline" onClick={verifySession} disabled={busy}>
                {busy ? "Checking…" : "Verify session"}
              </button>
            </section>
          )}

          <h2 className="section-heading">Evaluation workflow</h2>
          <div className="workflow-grid">
            {workflow.map((step) => (
              <article className="workflow-card" key={step.number}>
                <span className="workflow-number">{step.number}</span>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </article>
            ))}
          </div>
          <p className="coming-soon">
            Workflow navigation is a scaffold. Dataset processing and evaluation
            will be connected as those features are implemented.
          </p>
          {user && (
            <p className="account-note">
              Account: {user.username} · {user.email}
            </p>
          )}
        </section>
      </main>
    );
  }

  return (
    <main className="auth-page">
      <header className="topbar">
        <a className="brand" href="#" onClick={(event) => event.preventDefault()}>
          <span className="brand-mark">M</span>
          <span>Model<span className="brand-accent">Evaluator</span></span>
        </a>
        <button className="text-button" onClick={continueAsGuest}>
          Explore as guest <span aria-hidden="true">↗</span>
        </button>
      </header>

      <div className="auth-layout">
        <section className="hero-panel">
          <div className="hero-orb orb-one" />
          <div className="hero-orb orb-two" />
          <span className="eyebrow hero-eyebrow">THE ML WORKSPACE</span>
          <h1>From raw data to <span>real insight.</span></h1>
          <p className="hero-copy">
            A focused workspace for exploring datasets, evaluating machine
            learning models, and understanding their performance.
          </p>

          <div className="hero-preview">
            <div className="preview-header">
              <span>Evaluation workflow</span>
              <span className="preview-live"><span /> Ready to explore</span>
            </div>
            <div className="preview-flow">
              {workflow.map((step, index) => (
                <div className="preview-step" key={step.number}>
                  <span className="preview-number">{step.number}</span>
                  <span>{step.title}</span>
                  {index < workflow.length - 1 && (
                    <span className="preview-arrow">→</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="hero-footnote">
            <span className="shield-icon">✓</span>
            Passwords are protected. Tokens are never displayed.
          </div>
        </section>

        <section className="form-panel">
          <div className="auth-card">
            <div className="card-intro">
              <span className="eyebrow">{mode === "login" ? "WELCOME BACK" : "GET STARTED"}</span>
              <h2>{mode === "login" ? "Sign in to your account" : "Create your account"}</h2>
              <p>
                {mode === "login"
                  ? "Enter your details to continue to your workspace."
                  : "A few details and your workspace is ready."}
              </p>
            </div>

            <div className="auth-tabs" role="tablist" aria-label="Authentication">
              <button
                type="button"
                role="tab"
                aria-selected={mode === "login"}
                className={mode === "login" ? "active" : ""}
                onClick={() => changeMode("login")}
              >
                Sign in
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={mode === "register"}
                className={mode === "register" ? "active" : ""}
                onClick={() => changeMode("register")}
              >
                Create account
              </button>
            </div>

            {notice && (
              <div className={`notice notice-${notice.kind}`} role="status">
                {notice.text}
              </div>
            )}

            <form className="auth-form" onSubmit={handleSubmit} noValidate>
              {mode === "register" && (
                <>
                  <label htmlFor="username">Username</label>
                  <input
                    id="username"
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    placeholder="e.g. alex_m"
                    autoComplete="username"
                    minLength={3}
                    maxLength={50}
                    required
                    disabled={busy}
                  />

                  <label htmlFor="email">Email address</label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                    autoComplete="email"
                    required
                    disabled={busy}
                  />
                </>
              )}

              {mode === "login" && (
                <>
                  <label htmlFor="identifier">Username or email</label>
                  <input
                    id="identifier"
                    value={identifier}
                    onChange={(event) => setIdentifier(event.target.value)}
                    placeholder="Enter username or email"
                    autoComplete="username"
                    required
                    disabled={busy}
                  />
                </>
              )}

              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder={mode === "register" ? "At least 8 characters" : "Enter your password"}
                autoComplete={mode === "register" ? "new-password" : "current-password"}
                minLength={mode === "register" ? 8 : 1}
                maxLength={72}
                required
                disabled={busy}
              />

              {mode === "register" && (
                <p className="field-hint">
                  Use at least 8 characters, including a letter and a number.
                </p>
              )}

              <button className="button button-primary submit-button" type="submit" disabled={busy}>
                {busy
                  ? "Please wait…"
                  : mode === "login"
                    ? "Sign in"
                    : "Create account"}
                {!busy && <span aria-hidden="true">→</span>}
              </button>
            </form>

            <div className="separator"><span>OR</span></div>

            <button className="button button-guest" type="button" onClick={continueAsGuest}>
              Continue as guest <span aria-hidden="true">↗</span>
            </button>

            <p className="privacy-note">
              Your password is never shown in messages or application logs.
              Authentication tokens remain in memory and are cleared on sign-out or refresh.
            </p>
          </div>
        </section>
      </div>

      <footer className="page-footer">
        <span>Model Evaluator</span>
        <span>Built for clearer model evaluation.</span>
      </footer>
    </main>
  );
}

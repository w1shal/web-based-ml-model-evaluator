
import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App";
import { api, type AuthUser } from "../lib/api";

vi.mock("../lib/api", () => ({
  api: {
    register: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    me: vi.fn(),
  },
}));

const mockedApi = vi.mocked(api);

const demoUser: AuthUser = {
  user_id: 42,
  username: "vivek_ui_demo",
  email: "vivek.ui.demo@example.com",
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("Authentication UI", () => {
  it("registers an account and returns to sign-in", async () => {
    const user = userEvent.setup();
    mockedApi.register.mockResolvedValue({
      user_id: 42,
      message: "User registered",
    });

    render(<App />);

    await user.click(screen.getByRole("tab", { name: "Create account" }));
    await user.type(screen.getByLabelText("Username"), "vivek_ui_demo");
    await user.type(
      screen.getByLabelText("Email address"),
      "vivek.ui.demo@example.com",
    );
    await user.type(
      screen.getByLabelText("Password"),
      "ModelTest123",
    );
    await user.click(
      screen.getByRole("button", { name: /create account/i }),
    );

    expect(await screen.findByText(/Account created/)).toBeInTheDocument();
    expect(mockedApi.register).toHaveBeenCalledWith({
      username: "vivek_ui_demo",
      email: "vivek.ui.demo@example.com",
      password: "ModelTest123",
    });
    expect(
      screen.getByRole("heading", { name: "Sign in to your account" }),
    ).toBeInTheDocument();
  });

  it("rejects invalid registration fields before calling the API", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("tab", { name: "Create account" }));
    await user.type(screen.getByLabelText("Username"), "x");
    await user.click(
      screen.getByRole("button", { name: /create account/i }),
    );

    expect(
      await screen.findByText(/Username must be 3/),
    ).toBeInTheDocument();
    expect(mockedApi.register).not.toHaveBeenCalled();
  });

  it("logs in and verifies the authenticated session", async () => {
    const user = userEvent.setup();
    mockedApi.login.mockResolvedValue({
      access_token: "test-access-token",
      token_type: "bearer",
      expires_in: 3600,
      user: demoUser,
    });
    mockedApi.me.mockResolvedValue(demoUser);

    render(<App />);

    await user.type(
      screen.getByLabelText("Username or email"),
      demoUser.email,
    );
    await user.type(screen.getByLabelText("Password"), "ModelTest123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(
      await screen.findByRole("heading", {
        name: `Welcome, ${demoUser.username}.`,
      }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Verify session" }));

    expect(await screen.findByText("Your session is valid."))
      .toBeInTheDocument();
    expect(mockedApi.me).toHaveBeenCalledWith("test-access-token");
  });

  it("shows an understandable error for invalid login credentials", async () => {
    const user = userEvent.setup();
    mockedApi.login.mockRejectedValue(new Error("Invalid credentials"));

    render(<App />);

    await user.type(
      screen.getByLabelText("Username or email"),
      demoUser.email,
    );
    await user.type(screen.getByLabelText("Password"), "WrongPassword123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(
      await screen.findByText("Invalid credentials"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Sign in to your account" }),
    ).toBeInTheDocument();
  });

  it("revokes the token and clears frontend authentication on logout", async () => {
    const user = userEvent.setup();

    mockedApi.login.mockResolvedValue({
      access_token: "test-access-token",
      token_type: "bearer",
      expires_in: 3600,
      user: demoUser,
    });
    mockedApi.logout.mockResolvedValue({ message: "Logged out" });

    render(<App />);

    await user.type(
      screen.getByLabelText("Username or email"),
      demoUser.email,
    );
    await user.type(screen.getByLabelText("Password"), "ModelTest123");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await screen.findByRole("heading", {
      name: `Welcome, ${demoUser.username}.`,
    });

    await user.click(screen.getByRole("button", { name: "Sign out" }));

    expect(mockedApi.logout).toHaveBeenCalledWith("test-access-token");
    expect(
      await screen.findByRole("heading", {
        name: "Sign in to your account",
      }),
    ).toBeInTheDocument();
    expect(screen.queryByText("test-access-token")).not.toBeInTheDocument();
  });

  it("allows guest access without calling the authentication API", async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.click(
      screen.getByRole("button", { name: /continue as guest/i }),
    );

    expect(
      screen.getByRole("heading", {
        name: "Your next model insight starts here.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Guest mode")).toBeInTheDocument();
    expect(mockedApi.login).not.toHaveBeenCalled();
    expect(mockedApi.register).not.toHaveBeenCalled();
  });
});

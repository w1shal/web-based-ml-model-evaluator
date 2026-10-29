
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export type AuthUser = {
  user_id: number;
  username: string;
  email: string;
};

type RegisterInput = {
  username: string;
  email: string;
  password: string;
};

type LoginInput = {
  identifier: string;
  password: string;
};

type LoginResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
};

type BackendError = {
  detail?: unknown;
  error?: {
    message?: string;
    fields?: Array<{ field?: string; message?: string }>;
  };
};

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(options.headers);

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new Error(
      "Cannot reach the server. Check that the backend is running.",
    );
  }

  const data = (await response.json().catch(() => null)) as
    | BackendError
    | LoginResponse
    | Record<string, unknown>
    | null;

  if (!response.ok) {
    const error = data as BackendError | null;
    const firstFieldError = error?.error?.fields?.[0];

    const message =
      (typeof error?.detail === "string" && error.detail) ||
      (firstFieldError?.message &&
        `${firstFieldError.field || "Input"}: ${firstFieldError.message}`) ||
      error?.error?.message ||
      "The request could not be completed.";

    throw new Error(message);
  }

  return data as T;
}

export const api = {
  register(input: RegisterInput) {
    return request<{ user_id: number; message: string }>(
      "/auth/register",
      {
        method: "POST",
        body: JSON.stringify(input),
      },
    );
  },

  login(input: LoginInput) {
    return request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  logout(token: string) {
    return request<{ message: string }>(
      "/auth/logout",
      { method: "POST" },
      token,
    );
  },

  me(token: string) {
    return request<AuthUser>("/auth/me", { method: "GET" }, token);
  },
};

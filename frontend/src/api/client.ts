
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions extends RequestInit {
  token?: string | null;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { token, headers, signal, ...requestOptions } = options;

  let storedToken: string | null = null;

  try {
    storedToken = localStorage.getItem("authToken");
  } catch {
    // Storage may be unavailable; guest requests are still allowed.
  }

  const authToken = token ?? storedToken;
  const requestHeaders = new Headers(headers);

  if (
    requestOptions.body &&
    !(requestOptions.body instanceof FormData) &&
    !requestHeaders.has("Content-Type")
  ) {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (authToken) {
    requestHeaders.set("Authorization", `Bearer ${authToken}`);
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/${path.replace(/^\/+/, "")}`,
      {
        ...requestOptions,
        headers: requestHeaders,
        signal,
      },
    );

    if (!response.ok) {
      let message = `Request failed (${response.status})`;

      try {
        const body: unknown = await response.json();

        if (
          typeof body === "object" &&
          body !== null &&
          "detail" in body &&
          typeof body.detail === "string"
        ) {
          message = body.detail;
        }
      } catch {
        // Keep the default HTTP error message.
      }

      throw new ApiError(message, response.status);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }

    throw new ApiError(
      "Unable to reach the backend. Check your connection and confirm the API server is running.",
    );
  }
}

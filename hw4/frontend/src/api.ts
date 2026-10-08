import type { AuthResponse, ChatResponse, PageContext, Product, ProductDetail, StoredMessage } from "./types";

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    // FastAPI errors look like {"detail": "..."}; show that message when present.
    let message = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      /* not JSON */
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

const jsonPost = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export function registerUser(data: {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}): Promise<AuthResponse> {
  return getJson<AuthResponse>("/api/auth/register", jsonPost(data));
}

export function loginUser(email: string, password: string): Promise<AuthResponse> {
  return getJson<AuthResponse>("/api/auth/login", jsonPost({ email, password }));
}

export function fetchMe(token: string): Promise<AuthResponse["user"]> {
  return getJson<{ user: AuthResponse["user"] }>("/api/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  }).then((r) => r.user);
}

export interface ProductFilters {
  q?: string;
  category?: string;
  sort?: "name" | "price_asc" | "price_desc" | "stock";
  inStock?: boolean;
}

export function fetchProducts(q?: string | ProductFilters): Promise<Product[]> {
  const f: ProductFilters = typeof q === "string" ? { q } : q ?? {};
  const params = new URLSearchParams();
  if (f.q) params.set("q", f.q);
  if (f.category) params.set("category", f.category);
  if (f.sort && f.sort !== "name") params.set("sort", f.sort);
  if (f.inStock) params.set("in_stock", "true");
  const qs = params.toString();
  return getJson<Product[]>(`/api/products${qs ? `?${qs}` : ""}`);
}

export function fetchProduct(id: string): Promise<ProductDetail> {
  return getJson<ProductDetail>(`/api/products/${encodeURIComponent(id)}`);
}

// Sends one chat message plus recent history to the PydanticAI agent behind FastAPI.
export function sendChat(
  message: string,
  history: { role: "user" | "assistant"; content: string }[],
  token: string | null,
  page: PageContext
): Promise<ChatResponse> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  return getJson<ChatResponse>("/api/chat", {
    method: "POST",
    headers,
    // Logged-in users' history is loaded from the database by the server; guests send what's on screen.
    body: JSON.stringify({ message, history: token ? [] : history, page }),
  });
}

export function fetchChatHistory(token: string): Promise<StoredMessage[]> {
  return getJson<StoredMessage[]>("/api/chat/history", { headers: { Authorization: `Bearer ${token}` } });
}

export function clearChatHistory(token: string): Promise<{ deleted: number }> {
  return getJson<{ deleted: number }>("/api/chat/history", {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export const formatPrice = (n: number) => `$${n.toFixed(2)}`;

export interface Product {
  product_id: string;
  name: string;
  garment_type: string;
  description: string;
  colors: string[];
  price: number;
  image_url: string;
  total_units?: number; // only on /api/products list results
}

export interface SizeStock {
  size: string;
  quantity: number;
}

export interface ProductDetail extends Product {
  search_tags: string[];
  stock: SizeStock[];
}

export interface ToolEvent {
  tool: string;
  args: Record<string, unknown>;
  duration_ms: number | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  products?: Product[];
  tool_events?: ToolEvent[];
  pageTitle?: string; // set when this reply put search results on the page
  notice?: string; // safety notice shown under the reply
}

// Problem 7 contract: search results the agent wants rendered as cards on the page.
export interface PageResults {
  title: string;
  query: string;
  total_matches: number;
  products: Product[];
}

export interface ChatResponse {
  reply: string;
  products: Product[];
  page_results: PageResults | null;
  safety_notice?: string | null;
  masked_message?: string | null;
  tool_events: ToolEvent[];
  model: string;
}

export interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface PageContext {
  path: string;
  product_id: string | null;
}

export interface StoredMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  products: Product[];
  created_at: string;
}

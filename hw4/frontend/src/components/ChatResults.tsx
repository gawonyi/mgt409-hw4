import { useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { usePageResults } from "../pageResults";
import ProductCard from "./ProductCard";

// Grid of products found by the chat agent. Uses the same ProductCard as the Products page,
// so every card opens the same single-item detail page (/products/:id) when clicked.
export default function ChatResults() {
  const { results, version, clear } = usePageResults();
  const location = useLocation();
  const navigate = useNavigate();
  const ref = useRef<HTMLElement>(null);
  const onDetailPage = /^\/products\/[^/]+$/.test(location.pathname);

  // New results while the shopper is on a detail page: go back to the products page to show them.
  useEffect(() => {
    if (!results) return;
    if (onDetailPage) navigate("/products");
    else ref.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version]);

  if (!results || onDetailPage) return null;

  return (
    <section ref={ref} className="chat-results" aria-live="polite">
      <div className="chat-results-head">
        <div>
          <span className="eyebrow">From your chat</span>
          <h2>{results.title}</h2>
          <p className="muted">
            {results.total_matches} match{results.total_matches === 1 ? "" : "es"}
            {results.total_matches > results.products.length ? ` · showing ${results.products.length}` : ""}
          </p>
        </div>
        <button className="link-button" onClick={clear}>Clear results</button>
      </div>
      <div className="grid">
        {results.products.map((p) => (
          <ProductCard key={p.product_id} product={p} />
        ))}
      </div>
    </section>
  );
}

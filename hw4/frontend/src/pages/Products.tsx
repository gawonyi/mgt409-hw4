import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fetchProducts, ProductFilters } from "../api";
import type { Product } from "../types";
import ProductCard from "../components/ProductCard";

const CATEGORIES = [
  { value: "", label: "All" },
  { value: "hoodie", label: "Hoodies" },
  { value: "crewneck", label: "Crewnecks" },
  { value: "t-shirt", label: "T-shirts" },
  { value: "quarter-zip", label: "Quarter-zips" },
  { value: "fleece", label: "Fleece" },
  { value: "jacket", label: "Jackets" },
];

const SORTS: { value: NonNullable<ProductFilters["sort"]>; label: string }[] = [
  { value: "name", label: "Name (A–Z)" },
  { value: "price_asc", label: "Price: low to high" },
  { value: "price_desc", label: "Price: high to low" },
  { value: "stock", label: "Most in stock" },
];

export default function Products() {
  // Filters live in the URL (?category=hoodie&sort=price_asc&instock=1) so they survive Back and can be shared.
  const [params, setParams] = useSearchParams();
  const category = params.get("category") ?? "";
  const sort = (params.get("sort") as ProductFilters["sort"]) ?? "name";
  const inStock = params.get("instock") === "1";
  const [query, setQuery] = useState(params.get("q") ?? "");
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  function update(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  }

  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => {
      fetchProducts({ q: query || undefined, category: category || undefined, sort, inStock })
        .then((p) => {
          setProducts(p);
          setError("");
        })
        .catch(() => setError("Could not load products. Is the backend running on port 8000?"))
        .finally(() => setLoading(false));
    }, 200);
    return () => clearTimeout(t);
  }, [query, category, sort, inStock]);

  const filtered = Boolean(query || category || inStock);

  return (
    <section>
      <div className="products-head">
        <h1>Products</h1>
        <input
          className="search"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            update("q", e.target.value);
          }}
          placeholder="Search hoodies, crewnecks, sports…"
        />
      </div>

      <div className="filters">
        <div className="chips" role="group" aria-label="Category">
          {CATEGORIES.map((c) => (
            <button
              key={c.value}
              className={`chip ${category === c.value ? "active" : ""}`}
              aria-pressed={category === c.value}
              onClick={() => update("category", c.value)}
            >
              {c.label}
            </button>
          ))}
        </div>
        <div className="filter-right">
          <label className="toggle">
            <input type="checkbox" checked={inStock} onChange={(e) => update("instock", e.target.checked ? "1" : "")} />
            In stock only
          </label>
          <select value={sort} onChange={(e) => update("sort", e.target.value === "name" ? "" : e.target.value)} aria-label="Sort">
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
      </div>

      {error && <p className="error">{error}</p>}
      {!error && !loading && (
        <p className="muted">
          {products.length} item{products.length === 1 ? "" : "s"}
          {filtered && (
            <>
              {" · "}
              <button
                className="link-inline"
                onClick={() => {
                  setQuery("");
                  setParams(sort !== "name" ? { sort } : {}, { replace: true });
                }}
              >
                clear filters
              </button>
            </>
          )}
        </p>
      )}
      {!error && !loading && products.length === 0 && (
        <p className="muted">Nothing matches those filters. Try another category or ask our assistant.</p>
      )}
      <div className="grid">
        {products.map((p) => (
          <ProductCard key={p.product_id} product={p} />
        ))}
      </div>
    </section>
  );
}

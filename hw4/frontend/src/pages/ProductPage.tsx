import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchProduct, formatPrice } from "../api";
import { askInChat } from "../askChat";
import type { ProductDetail } from "../types";

const LOW_STOCK = 5;

export default function ProductPage() {
  const { productId = "" } = useParams();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [error, setError] = useState("");
  const [size, setSize] = useState<string | null>(null);

  useEffect(() => {
    setProduct(null);
    setError("");
    setSize(null);
    fetchProduct(productId)
      .then(setProduct)
      .catch(() => setError("Sorry, we couldn't find that product."));
  }, [productId]);

  if (error) return <p className="error">{error}</p>;
  if (!product) return <p className="muted">Loading…</p>;

  const chosen = product.stock.find((s) => s.size === size) ?? null;
  const inStockSizes = product.stock.filter((s) => s.quantity > 0).map((s) => s.size);

  function status() {
    if (!chosen) return <p className="muted">Select a size to check availability.</p>;
    if (chosen.quantity === 0)
      return (
        <p className="stock-msg out">
          Size {chosen.size} is sold out.
          {inStockSizes.length > 0 && <> In stock: {inStockSizes.join(", ")}.</>}
        </p>
      );
    if (chosen.quantity <= LOW_STOCK)
      return <p className="stock-msg low">Only {chosen.quantity} left in {chosen.size} — order soon!</p>;
    return <p className="stock-msg ok">In stock in {chosen.size} ({chosen.quantity} available).</p>;
  }

  const question = chosen
    ? chosen.quantity === 0
      ? `Size ${chosen.size} of the ${product.name} is sold out. Can you suggest something similar in ${chosen.size}?`
      : `Tell me more about the ${product.name} in size ${chosen.size}.`
    : `Tell me about the ${product.name}. Which sizes are in stock?`;

  return (
    <section>
      <Link to="/products" className="back">← Back to products</Link>
      <div className="detail">
        <img src={product.image_url} alt={product.name} className="detail-image" />
        <div className="detail-info">
          <p className="muted">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price big">{formatPrice(product.price)}</p>
          <p>{product.description}</p>
          <p>
            <strong>Colors:</strong> {product.colors.join(", ")}
          </p>
          <h3>Choose a size</h3>
          <div className="sizes" role="radiogroup" aria-label="Size">
            {product.stock.map((s) => (
              <button
                key={s.size}
                role="radio"
                aria-checked={size === s.size}
                className={`size ${s.quantity === 0 ? "out" : ""} ${size === s.size ? "selected" : ""}`}
                onClick={() => setSize(s.size)}
              >
                <span>{s.size}</span>
                <small>
                  {s.quantity === 0 ? "Sold out" : s.quantity <= LOW_STOCK ? `Only ${s.quantity}` : `${s.quantity} left`}
                </small>
              </button>
            ))}
          </div>
          {status()}
          <button className="button ask-button" onClick={() => askInChat(question)}>
            💬 Ask about this item
          </button>
        </div>
      </div>
    </section>
  );
}

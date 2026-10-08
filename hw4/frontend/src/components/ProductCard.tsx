import { Link } from "react-router-dom";
import type { Product } from "../types";
import { formatPrice } from "../api";

// Card styled like a store hang tag: the price sits on a tag with a punched hole.
export default function ProductCard({ product }: { product: Product }) {
  const soldOut = product.total_units === 0;
  return (
    <Link to={`/products/${product.product_id}`} className={`card ${soldOut ? "is-out" : ""}`}>
      <div className="card-media">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        <span className="hang-tag">{formatPrice(product.price)}</span>
      </div>
      <div className="card-body">
        <p className="card-type">{product.garment_type}</p>
        <h3>{product.name}</h3>
        <p className="short">{product.description}</p>
        {soldOut && <span className="badge out">Sold out</span>}
      </div>
    </Link>
  );
}

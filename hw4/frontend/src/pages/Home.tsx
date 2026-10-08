import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { fetchProducts } from "../api";
import { askInChat } from "../askChat";
import type { Product } from "../types";
import ProductCard from "../components/ProductCard";

const SHOP_BY = [
  { to: "/products?category=hoodie", title: "Hoodies", note: "Pullovers and full-zips for cold walks across campus" },
  { to: "/products?category=crewneck", title: "Crewnecks", note: "One for every residential college" },
  { to: "/products?q=sports", title: "Varsity sports", note: "From soccer to squash" },
  { to: "/products?category=quarter-zip", title: "Quarter-zips", note: "Graduate and professional schools" },
];

export default function Home() {
  const [featured, setFeatured] = useState<Product[]>([]);
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    fetch("/api/stats")
      .then((r) => r.json())
      .then((d) => setCount(d.product_count))
      .catch(() => setCount(null));
    fetchProducts({ category: "hoodie", inStock: true, sort: "stock" })
      .then((p) => setFeatured(p.slice(0, 4)))
      .catch(() => setFeatured([]));
  }, []);

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <p className="hero-kicker">Campus Customs · New Haven, CT</p>
          <h1>Wear New Haven on your sleeve.</h1>
          <p className="hero-lede">
            Officially licensed Yale apparel: cozy hoodies, crewnecks for every residential college,
            team tees, and gifts for the whole Bulldog family.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="button">{count ? `Shop all ${count} products` : "Shop all products"}</Link>
            <button className="button ghost" onClick={() => askInChat("What hoodies do you have?")}>
              Ask what's in stock
            </button>
          </div>
        </div>
        <div className="pennant-wrap" aria-hidden="true">
          <div className="pennant">
            <span>Campus Customs</span>
          </div>
        </div>
      </section>

      <section className="shop-by" aria-label="Shop by">
        {SHOP_BY.map((s) => (
          <Link key={s.title} to={s.to} className="shop-tile">
            <strong>{s.title}</strong>
            <span>{s.note}</span>
          </Link>
        ))}
      </section>

      {featured.length > 0 && (
        <section className="featured">
          <div className="section-head">
            <h2>Hoodie season</h2>
            <Link to="/products?category=hoodie">See all hoodies</Link>
          </div>
          <div className="grid">
            {featured.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
        </section>
      )}
    </>
  );
}

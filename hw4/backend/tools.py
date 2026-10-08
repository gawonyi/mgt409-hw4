"""Tools the Campus Customs agent can call, plus database helpers.

Every fact the agent states about products (names, prices, sizes, stock) must come
from these functions, which read data/campus_customs.db. They are plain Python so
they can be tested without the model.

Problem 5: get_store_overview.
Problem 6: find_product, get_product_info, get_price, get_stock.
Problem 7: search_catalogue (category / keyword / color / price search for the page grid).
Problem 8: customer profile, saved chat history, and current-page context helpers.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import List, Optional

import re

from models import (
    PriceInfo,
    ProductCard,
    ProductInfo,
    ProductLookup,
    ProductMatch,
    SearchHit,
    SearchResults,
    SizeStock,
    StockInfo,
    StoreOverview,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR.parent / "data")).resolve()
DB_PATH = DATA_DIR / "campus_customs.db"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def image_url(image_file_path: str) -> str:
    """catalogue stores 'products/<file>.jpg'; FastAPI serves it at /media/<file>.jpg."""
    return "/media/" + Path(image_file_path).name


def row_to_card(row: sqlite3.Row) -> ProductCard:
    return ProductCard(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        price=row["price"],
        image_url=image_url(row["image_file_path"]),
        description=row["description"],
        colors=json.loads(row["colors"]),
    )


def cards_for_ids(product_ids: List[str], limit: int = 12) -> List[ProductCard]:
    """Turn product_ids chosen by the agent into cards. Unknown ids are dropped, so the
    model can never put an invented product on the page."""
    seen: List[str] = []
    for pid in product_ids:
        if pid not in seen:
            seen.append(pid)
    seen = seen[:limit]
    if not seen:
        return []
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT * FROM catalogue WHERE product_id IN ({','.join('?' * len(seen))})", seen
        ).fetchall()
    by_id = {r["product_id"]: row_to_card(r) for r in rows}
    return [by_id[pid] for pid in seen if pid in by_id]


# ------------------------------------------------------------------ agent tools


def get_store_overview() -> StoreOverview:
    """What the shop sells: product count, garment types with counts, price range (USD), sizes."""
    with get_db() as conn:
        types = conn.execute(
            "SELECT lower(garment_type) AS t, count(*) AS n FROM catalogue GROUP BY t ORDER BY n DESC"
        ).fetchall()
        lo, hi, n = conn.execute("SELECT min(price), max(price), count(*) FROM catalogue").fetchone()
        sizes = [r[0] for r in conn.execute("SELECT DISTINCT size FROM inventory").fetchall()]
    sizes.sort(key=lambda s: SIZE_ORDER.index(s) if s in SIZE_ORDER else 99)
    return StoreOverview(
        product_count=n,
        garment_types={r["t"]: r["n"] for r in types},
        min_price=lo,
        max_price=hi,
        sizes=sizes,
    )


# Words shoppers use for sizes -> the size codes stored in the inventory table.
SIZE_ALIASES = {
    "xs": "XS", "x-small": "XS", "xsmall": "XS", "extra small": "XS", "extra-small": "XS",
    "s": "S", "small": "S", "sm": "S",
    "m": "M", "medium": "M", "med": "M",
    "l": "L", "large": "L", "lg": "L",
    "xl": "XL", "x-large": "XL", "xlarge": "XL", "extra large": "XL", "extra-large": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "xxlarge": "XXL", "2x": "XXL",
    "double xl": "XXL", "extra extra large": "XXL",
}


def normalize_size(size: Optional[str]) -> Optional[str]:
    """'medium' -> 'M', '2XL' -> 'XXL'. Returns the cleaned text if it is not a known size."""
    if size is None or not size.strip():
        return None
    key = size.strip().lower()
    return SIZE_ALIASES.get(key, size.strip().upper())


def _words(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def find_product(query: str, limit: int = 5) -> ProductLookup:
    """Product names/ids that best match the shopper's words (name > id > type > tags)."""
    q_words = [w for w in _words(query) if w not in {"the", "a", "an", "yale", "shirt"} or len(_words(query)) <= 2]
    if not q_words:
        q_words = _words(query)
    with get_db() as conn:
        rows = conn.execute("SELECT product_id, name, garment_type, search_tags, price FROM catalogue").fetchall()
    scored = []
    q_full = query.strip().lower()
    for r in rows:
        name, pid = r["name"].lower(), r["product_id"].lower()
        if q_full in (name, pid):
            score = 100.0
        else:
            name_w, type_w = set(_words(name)), set(_words(r["garment_type"]))
            tag_w = set(_words(r["search_tags"]))
            score = sum(3 if w in name_w else 1 if w in type_w else 0.5 if w in tag_w else 0 for w in q_words)
            score /= max(len(q_words), 1)
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda t: (-t[0], t[1]["name"]))
    return ProductLookup(
        query=query,
        matches=[
            ProductMatch(product_id=r["product_id"], name=r["name"], garment_type=r["garment_type"], price=r["price"])
            for _, r in scored[: max(1, min(limit, 10))]
        ],
    )


def _catalogue_row(product_id: str) -> Optional[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id.strip(),)).fetchone()


NOT_FOUND = "No product with that product_id. Call find_product with the product name first."


def get_product_info(product_id: str) -> ProductInfo:
    """Full description, garment type, colors and tags for one product."""
    row = _catalogue_row(product_id)
    if row is None:
        return ProductInfo(found=False, product_id=product_id, message=NOT_FOUND)
    return ProductInfo(
        found=True,
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        search_tags=json.loads(row["search_tags"]),
    )


def get_price(product_id: str) -> PriceInfo:
    """Current price in USD for one product."""
    row = _catalogue_row(product_id)
    if row is None:
        return PriceInfo(found=False, product_id=product_id, message=NOT_FOUND)
    return PriceInfo(found=True, product_id=row["product_id"], name=row["name"], price=row["price"])


def get_stock(product_id: str, size: Optional[str] = None) -> StockInfo:
    """Units in stock per size for one product; if size is given, also answers for that size."""
    row = _catalogue_row(product_id)
    if row is None:
        return StockInfo(found=False, product_id=product_id, message=NOT_FOUND)
    with get_db() as conn:
        stock_rows = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (row["product_id"],)
        ).fetchall()
    sizes = sorted(
        (SizeStock(size=r["size"], quantity=r["quantity"], in_stock=r["quantity"] > 0) for r in stock_rows),
        key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else 99,
    )
    info = StockInfo(
        found=True,
        product_id=row["product_id"],
        name=row["name"],
        sizes=sizes,
        total_units=sum(s.quantity for s in sizes),
        sizes_in_stock=[s.size for s in sizes if s.in_stock],
        sizes_sold_out=[s.size for s in sizes if not s.in_stock],
    )
    wanted = normalize_size(size)
    if wanted:
        info.requested_size = wanted
        match = next((s for s in sizes if s.size == wanted), None)
        if match is None:
            info.requested_size_quantity = 0
            info.requested_size_in_stock = False
            info.message = f"This item is not made in size {wanted}. Sizes offered: {', '.join(s.size for s in sizes)}."
        else:
            info.requested_size_quantity = match.quantity
            info.requested_size_in_stock = match.in_stock
            if not match.in_stock:
                info.message = f"Size {wanted} is sold out."
    return info


# garment_type values in the DB are not normalized ("pullover hoodie", "hooded sweatshirt", "hoodie"...),
# so each shopper-facing category is matched by keywords in garment_type.
CATEGORIES = {
    "hoodie": ["hoodie", "hooded"],
    "crewneck": ["crewneck"],
    "t-shirt": ["t-shirt"],
    "quarter-zip": ["quarter-zip"],
    "jacket": ["jacket"],
    "fleece": ["fleece"],
    "long-sleeve": ["long-sleeve"],
    "sweatshirt": ["sweatshirt", "crewneck", "hoodie", "hooded", "quarter-zip"],
    "mockneck": ["mockneck"],
}
CATEGORY_ALIASES = {
    "hoodies": "hoodie", "hoody": "hoodie", "hooded sweatshirt": "hoodie", "hoodie": "hoodie",
    "crewnecks": "crewneck", "crew neck": "crewneck", "crew": "crewneck", "crewneck": "crewneck",
    "tshirt": "t-shirt", "t shirt": "t-shirt", "tee": "t-shirt", "tees": "t-shirt", "t-shirts": "t-shirt",
    "shirts": "t-shirt", "shirt": "t-shirt", "t-shirt": "t-shirt",
    "quarter zip": "quarter-zip", "quarter zips": "quarter-zip", "1/4 zip": "quarter-zip", "quarter-zips": "quarter-zip",
    "half zip": "quarter-zip", "quarter-zip": "quarter-zip",
    "jackets": "jacket", "coat": "jacket", "coats": "jacket", "jacket": "jacket",
    "fleeces": "fleece", "fleece": "fleece",
    "long sleeve": "long-sleeve", "long sleeves": "long-sleeve", "long-sleeve": "long-sleeve",
    "sweatshirts": "sweatshirt", "sweaters": "sweatshirt", "sweater": "sweatshirt", "sweatshirt": "sweatshirt",
    "mock neck": "mockneck", "mockneck": "mockneck",
}
STOP_WORDS = {"a", "an", "the", "any", "do", "you", "have", "what", "show", "me", "some", "with", "and", "or",
              "for", "in", "of", "on", "all", "your", "items", "item", "stuff", "merch", "clothes", "apparel",
              "yale", "products", "product", "under", "below", "than", "less"}


def normalize_category(category: Optional[str]) -> Optional[str]:
    if not category or not category.strip():
        return None
    key = category.strip().lower()
    return CATEGORY_ALIASES.get(key, key if key in CATEGORIES else None)


def _first_sentence(text: str) -> str:
    end = text.find(". ")
    return text if end == -1 else text[: end + 1]


def search_catalogue(
    query: str = "",
    category: Optional[str] = None,
    color: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 24,
) -> SearchResults:
    """Products that fit a category (hoodie, crewneck, t-shirt...), keywords (sport, college, 'mom'),
    a color, and/or a max price in USD. Every keyword must appear in the product's name, type, tags,
    description or colors."""
    cat = normalize_category(category)
    words = [w for w in _words(query) if w not in STOP_WORDS]
    # A category word typed into the query ("hoodies") becomes the category filter.
    if cat is None:
        for w in list(words):
            if normalize_category(w):
                cat = normalize_category(w)
                words.remove(w)
                break
    elif normalize_category(" ".join(words)) == cat:
        words = []
    if cat:
        words = [w for w in words if normalize_category(w) != cat]
    color_l = color.strip().lower() if color and color.strip() else None

    with get_db() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    hits: List[SearchHit] = []
    for r in rows:
        gtype = r["garment_type"].lower()
        if cat and not any(k in gtype for k in CATEGORIES[cat]):
            continue
        colors = json.loads(r["colors"])
        if color_l and not any(color_l in c.lower() or c.lower() in color_l for c in colors):
            continue
        if max_price is not None and r["price"] > max_price:
            continue
        haystack = set(_words(" ".join([r["name"], gtype, r["search_tags"], r["description"], " ".join(colors)])))
        if words and not all(w in haystack or w.rstrip("s") in haystack for w in words):
            continue
        hits.append(
            SearchHit(
                product_id=r["product_id"],
                name=r["name"],
                garment_type=r["garment_type"],
                price=r["price"],
                colors=colors,
                short_description=_first_sentence(r["description"]),
            )
        )
    limit = max(1, min(limit, 30))
    message = None
    if not hits:
        message = "No products matched. Try fewer keywords, a broader category, or no color filter."
    elif category and cat is None:
        message = f"Unknown category '{category}'; searched keywords only. Known categories: {', '.join(CATEGORIES)}."
    return SearchResults(
        query=query,
        category=cat,
        color=color_l,
        max_price=max_price,
        total_matches=len(hits),
        products=hits[:limit],
        message=message,
    )




# ------------------------------------------------------------------ Problem 8: customer memory + page context

HISTORY_FOR_MODEL = 12   # saved messages sent back to the model each turn
HISTORY_FOR_UI = 50      # saved messages shown when the chat reloads


def get_customer_profile(user_id: int) -> Optional["CustomerProfile"]:
    from models import CustomerProfile

    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            return None
        n = conn.execute("SELECT count(*) FROM chat_messages WHERE user_id = ?", (user_id,)).fetchone()[0]
    first = row["first_name"] or row["name"].split(" ")[0]
    last = row["last_name"] or " ".join(row["name"].split(" ")[1:])
    return CustomerProfile(
        user_id=row["id"],
        first_name=first,
        last_name=last,
        email=row["email"],
        member_since=(row["created_at"] or "")[:10] or None,
        saved_messages=n,
    )


def save_chat_message(user_id: int, role: str, content: str, products: Optional[List[ProductCard]] = None) -> None:
    """Append one message to chat_messages. products_json keeps the cards shown with a reply."""
    products_json = json.dumps([p.model_dump() for p in products]) if products is not None else None
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (user_id, role, content, products_json),
        )


def load_chat_history(user_id: int, limit: int = HISTORY_FOR_UI) -> list:
    """Most recent `limit` messages for a user, oldest first."""
    from models import StoredMessage

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM (SELECT * FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?) ORDER BY id",
            (user_id, limit),
        ).fetchall()
    out = []
    for r in rows:
        try:
            raw = json.loads(r["products_json"]) if r["products_json"] else []
        except json.JSONDecodeError:
            raw = []
        # Re-validate stored cards against the live catalogue (prices/images may have changed).
        cards = cards_for_ids([p.get("product_id") for p in raw if isinstance(p, dict)], limit=24)
        out.append(
            StoredMessage(id=r["id"], role=r["role"], content=r["content"], products=cards, created_at=r["created_at"])
        )
    return out


def clear_chat_history(user_id: int) -> int:
    with get_db() as conn:
        return conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,)).rowcount


PAGE_NAMES = {"/": "Home", "/products": "Products", "/about": "About Us", "/login": "Log in",
              "/create-account": "Create account"}


def describe_page(path: str, product_id: Optional[str]) -> "CurrentPage":
    """Resolve the page the shopper is on. A product page is looked up in the DB, so 'this' has a real id."""
    from models import CurrentPage

    path = path or "/"
    pid = product_id
    if pid is None and path.startswith("/products/"):
        pid = path.split("/products/", 1)[1].strip("/") or None
    if pid:
        row = _catalogue_row(pid)
        if row is not None:
            return CurrentPage(
                path=path,
                page_name="Product detail",
                product_id=row["product_id"],
                product_name=row["name"],
                garment_type=row["garment_type"],
                price=row["price"],
                colors=json.loads(row["colors"]),
            )
    return CurrentPage(path=path, page_name=PAGE_NAMES.get(path, "Other page"))


# ------------------------------------------------------------------ Problem 9: usability improvements


def _category_of(garment_type: str) -> Optional[str]:
    """Most specific shopper category for a garment_type (hoodie before sweatshirt)."""
    g = garment_type.lower()
    for cat in ["hoodie", "quarter-zip", "crewneck", "mockneck", "t-shirt", "fleece", "jacket", "long-sleeve"]:
        if any(k in g for k in CATEGORIES[cat]):
            return cat
    return None


def find_alternatives(product_id: str, size: Optional[str] = None, limit: int = 4) -> "Alternatives":
    """In-stock alternatives for a product: same category, available in `size` (if given), ranked by
    shared search tags/colors and closeness in price. Used when a size is sold out."""
    from models import Alternative, Alternatives

    base = _catalogue_row(product_id)
    if base is None:
        return Alternatives(found=False, product_id=product_id, message=NOT_FOUND)
    wanted = normalize_size(size)
    cat = _category_of(base["garment_type"])
    base_tags = set(t.lower() for t in json.loads(base["search_tags"])) | set(c.lower() for c in json.loads(base["colors"]))
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM catalogue WHERE product_id != ?", (base["product_id"],)).fetchall()
        stock = {}
        for r in conn.execute("SELECT product_id, size, quantity FROM inventory"):
            stock.setdefault(r["product_id"], {})[r["size"]] = r["quantity"]
    picks = []
    for r in rows:
        if cat and _category_of(r["garment_type"]) != cat:
            continue
        sizes = stock.get(r["product_id"], {})
        qty = sizes.get(wanted, 0) if wanted else sum(sizes.values())
        if qty <= 0:
            continue
        tags = set(t.lower() for t in json.loads(r["search_tags"])) | set(c.lower() for c in json.loads(r["colors"]))
        overlap = len(base_tags & tags)
        price_gap = abs(r["price"] - base["price"])
        picks.append((-overlap, price_gap, r, qty))
    picks.sort(key=lambda t: (t[0], t[1], t[2]["name"]))
    return Alternatives(
        found=True,
        product_id=base["product_id"],
        name=base["name"],
        category=cat,
        size=wanted,
        alternatives=[
            Alternative(
                product_id=r["product_id"],
                name=r["name"],
                garment_type=r["garment_type"],
                price=r["price"],
                units_in_size=qty if wanted else None,
                shared_features=sorted(base_tags & set(t.lower() for t in json.loads(r["search_tags"])))[:4],
            )
            for _, _, r, qty in picks[: max(1, min(limit, 8))]
        ],
        message=None if picks else "No in-stock alternatives in that category and size.",
    )


# ---- input safety filter: sensitive data never reaches the model or the database

CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
SSN_RE = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
SECRET_RE = re.compile(
    r"(?i)\b(password|passcode|pin|cvv|cvc|security code)\b(\s*(is|:|=)\s*)(\S+)"
)


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for d in reversed(digits):
        n = int(d)
        if alt:
            n = n * 2 - 9 if n > 4 else n * 2
        total += n
        alt = not alt
    return total % 10 == 0


def redact_sensitive(text: str) -> tuple:
    """Mask payment card numbers (Luhn-checked), SSNs and 'password is ...' style secrets.
    Returns (clean_text, list of what was redacted)."""
    found = []

    def card(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            found.append("card number")
            tail = " " if m.group(0)[-1] in " -" else ""
            return f"[card number removed •••• {digits[-4:]}]{tail}"
        return m.group(0)

    text = CARD_RE.sub(card, text)
    if SSN_RE.search(text):
        found.append("SSN")
        text = SSN_RE.sub("[SSN removed]", text)
    if SECRET_RE.search(text):
        found.append("password/PIN")
        text = SECRET_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}[removed]", text)
    return text, found

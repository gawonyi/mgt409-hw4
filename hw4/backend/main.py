"""Campus Customs FastAPI backend.

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000

Serves products and images (Problem 3), auth (Problem 4), and the chat route that
calls the PydanticAI agent in agent.py (Problem 5).
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

from collections import defaultdict, deque

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent import MODEL_NAME, run_chat
from models import ChatRequest, ChatResponse, StoredMessage
import tools

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR.parent / "data")).resolve()
DB_PATH = DATA_DIR / "campus_customs.db"
IMAGES_DIR = DATA_DIR / "products"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# Auth settings. Hash format matches the seed users: pbkdf2_sha256$<salt>$<hex digest>
PBKDF2_ITERATIONS = 120_000
SECRET_KEY = os.getenv("SECRET_KEY") or ""
if not SECRET_KEY:
    # Tokens are still signed so local dev works, but warn loudly: anyone who knows this
    # default could forge a login token. Set SECRET_KEY in .env for any real deployment.
    SECRET_KEY = "dev-only-change-me"
    print("[auth] WARNING: SECRET_KEY is not set in .env; using an insecure development key.")
TOKEN_TTL_SECONDS = 7 * 24 * 3600

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Only the product image folder is public (never the database file).
app.mount("/media", StaticFiles(directory=IMAGES_DIR), name="media")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def image_url(image_file_path: str) -> str:
    # catalogue stores "products/<file>.jpg"; images are served from /media/<file>.jpg
    return "/media/" + Path(image_file_path).name


def product_summary(row: sqlite3.Row) -> dict:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "price": row["price"],
        "image_url": image_url(row["image_file_path"]),
    }


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "db_found": DB_PATH.exists(),
        "model": MODEL_NAME,
        "api_key_loaded": bool(os.getenv("PORTKEY_API_KEY")),
        "secret_key_set": bool(os.getenv("SECRET_KEY")),
    }


@app.get("/api/stats")
def stats() -> dict:
    """Live store numbers for the home page (no hard-coded counts)."""
    with get_db() as conn:
        n = conn.execute("SELECT count(*) FROM catalogue").fetchone()[0]
    return {"product_count": n}


@app.get("/api/products")
def list_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    sort: str = "name",
    in_stock: bool = False,
) -> List[dict]:
    """Products with optional text search, category (hoodie, crewneck, t-shirt...), sort
    (name | price_asc | price_desc | stock) and an in-stock-only filter. Each item includes total_units."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        units = dict(conn.execute("SELECT product_id, sum(quantity) FROM inventory GROUP BY product_id").fetchall())
    cat = tools.normalize_category(category) if category else None
    products = []
    for r in rows:
        if q and q.lower().strip() not in (r["name"] + " " + r["garment_type"] + " " + r["search_tags"]).lower():
            continue
        if cat and not any(k in r["garment_type"].lower() for k in tools.CATEGORIES[cat]):
            continue
        p = product_summary(r)
        p["total_units"] = units.get(r["product_id"], 0)
        if in_stock and p["total_units"] <= 0:
            continue
        products.append(p)
    if sort == "price_asc":
        products.sort(key=lambda p: (p["price"], p["name"]))
    elif sort == "price_desc":
        products.sort(key=lambda p: (-p["price"], p["name"]))
    elif sort == "stock":
        products.sort(key=lambda p: (-p["total_units"], p["name"]))
    return products


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    """One product with its size-by-size stock."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        stock_rows = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()

    stock = sorted(
        ({"size": s["size"], "quantity": s["quantity"]} for s in stock_rows),
        key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99,
    )
    product = product_summary(row)
    product["search_tags"] = json.loads(row["search_tags"])
    product["stock"] = stock
    return product


# ---------------------------------------------------------------- auth (Problem 4)


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Salted PBKDF2-SHA256. Only this hash is stored, never the password."""
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt, _ = stored.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


def make_token(user_id: int) -> str:
    """Signed login token: base64(payload).signature (HMAC-SHA256 with SECRET_KEY)."""
    payload = json.dumps({"uid": user_id, "exp": int(time.time()) + TOKEN_TTL_SECONDS})
    body = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = hmac.new(SECRET_KEY.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def read_token(token: str) -> Optional[int]:
    try:
        body, sig = token.split(".")
        expected = hmac.new(SECRET_KEY.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body.encode()))
        if payload["exp"] < time.time():
            return None
        return int(payload["uid"])
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


def public_user(row: sqlite3.Row) -> dict:
    """User fields that are safe to send to the browser (never the password hash)."""
    first = row["first_name"] or row["name"].split(" ")[0]
    last = row["last_name"] or " ".join(row["name"].split(" ")[1:])
    return {"id": row["id"], "first_name": first, "last_name": last, "email": row["email"]}


def current_user(authorization: Optional[str]) -> Optional[dict]:
    """Logged-in user from an 'Authorization: Bearer <token>' header, or None for guests."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    user_id = read_token(authorization[len("Bearer "):].strip())
    if user_id is None:
        return None
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return public_user(row) if row else None


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


def clean_email(email: str) -> str:
    email = email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    return email


@app.post("/api/auth/register")
def register(req: RegisterRequest) -> dict:
    email = clean_email(req.email)
    first, last = req.first_name.strip(), req.last_name.strip()
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            raise HTTPException(status_code=409, detail="An account with that email already exists.")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
            (f"{first} {last}", email, hash_password(req.password), first, last),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return {"token": make_token(row["id"]), "user": public_user(row)}


@app.post("/api/auth/login")
def login(req: LoginRequest) -> dict:
    email = req.email.strip().lower()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    # Same message for unknown email and wrong password, so emails can't be probed.
    if row is None or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return {"token": make_token(row["id"]), "user": public_user(row)}


@app.get("/api/auth/me")
def me(authorization: Optional[str] = Header(default=None)) -> dict:
    user = current_user(authorization)
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in.")
    return {"user": user}


# ---------------------------------------------------------------- chat (Problem 5)


# Improvement: per-shopper rate limit so one user (or a bot) can't run up model costs.
CHAT_LIMIT_PER_MINUTE = 15
_chat_calls: dict = defaultdict(deque)


def check_rate_limit(key: str) -> None:
    now = time.time()
    calls = _chat_calls[key]
    while calls and now - calls[0] > 60:
        calls.popleft()
    if len(calls) >= CHAT_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="You're sending messages very quickly. Please wait a moment and try again.")
    calls.append(now)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest, request: Request, authorization: Optional[str] = Header(default=None)
) -> ChatResponse:
    """Website chat message -> PydanticAI agent -> reply (+ product cards and tool calls)."""
    user = current_user(authorization)
    check_rate_limit(f"user:{user['id']}" if user else f"ip:{request.client.host if request.client else 'unknown'}")
    try:
        return await run_chat(req.message, req.history, user, req.page)
    except Exception as exc:
        # Log the real error for the developer; the shopper gets an honest message, not a made-up answer.
        print(f"[chat] agent error: {exc!r}")
        raise HTTPException(
            status_code=502,
            detail="Sorry, the shop assistant is having trouble right now. Please try again in a moment.",
        )


@app.get("/api/chat/history", response_model=List[StoredMessage])
def chat_history(authorization: Optional[str] = Header(default=None)) -> List[StoredMessage]:
    """Saved chat for the logged-in customer (most recent 50, oldest first). Guests get 401."""
    user = current_user(authorization)
    if user is None:
        raise HTTPException(status_code=401, detail="Log in to see your saved chat.")
    return tools.load_chat_history(user["id"])


@app.delete("/api/chat/history")
def clear_history(authorization: Optional[str] = Header(default=None)) -> dict:
    """Let a customer wipe their own saved chat."""
    user = current_user(authorization)
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in.")
    return {"deleted": tools.clear_chat_history(user["id"])}


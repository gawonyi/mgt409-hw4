"""Pydantic / PydanticAI types for the Campus Customs chatbot.

- ChatRequest / ChatResponse: the JSON contract between the website and FastAPI.
- AgentReply: the structured output the agent must return.
- ProductCard: what the front end needs to draw one product card.
- ToolEvent: one tool call the agent made (shown in the chat so answers can be audited).
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class HistoryMessage(BaseModel):
    """One earlier chat turn sent by the website so the agent keeps context."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class PageContext(BaseModel):
    """Which page the shopper is looking at when they send a chat message (Problem 8)."""

    path: str = Field(default="/", max_length=200, description="Current URL path, e.g. /products/basic-hoodie-big-yale")
    product_id: Optional[str] = Field(default=None, max_length=120, description="Set when the shopper is on a product page")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # Guests send their on-screen history; for logged-in users the server loads it from the database.
    history: List[HistoryMessage] = Field(default_factory=list, max_length=20)
    page: Optional[PageContext] = None


class CustomerProfile(BaseModel):
    """Who is chatting. Given to the agent through deps; never includes the password hash."""

    user_id: int
    first_name: str
    last_name: str
    email: str
    member_since: Optional[str] = Field(default=None, description="Account creation date (YYYY-MM-DD)")
    saved_messages: int = Field(default=0, description="How many chat messages this customer has saved")


class CurrentPage(BaseModel):
    """Result of get_current_page: the page and product (if any) the shopper is viewing."""

    path: str
    page_name: str
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    garment_type: Optional[str] = None
    price: Optional[float] = Field(default=None, description="USD")
    colors: List[str] = Field(default_factory=list)


class StoredMessage(BaseModel):
    """One saved chat message, as returned by GET /api/chat/history."""

    id: int
    role: Literal["user", "assistant"]
    content: str
    products: List["ProductCard"] = Field(default_factory=list)
    created_at: str


class ProductCard(BaseModel):
    """Everything a product card on the page needs. Built from the database, never by the model."""

    product_id: str
    name: str
    garment_type: str
    price: float = Field(description="Price in US dollars, from the catalogue table")
    image_url: str
    description: str
    colors: List[str] = Field(default_factory=list)


class StoreOverview(BaseModel):
    """Result of the get_store_overview tool: a quick map of what the shop sells."""

    product_count: int
    garment_types: dict[str, int] = Field(description="garment_type -> number of products")
    min_price: float = Field(description="Cheapest item, USD")
    max_price: float = Field(description="Most expensive item, USD")
    sizes: List[str]


class AgentReply(BaseModel):
    """The agent's final answer for one chat turn."""

    reply: str = Field(description="Friendly answer to show the shopper, in Campus Customs voice. Plain text or light markdown.")
    product_ids: List[str] = Field(
        default_factory=list,
        description="product_id values (exactly as returned by a tool) of items to show as cards. Empty if none.",
    )
    show_on_page: bool = Field(
        default=False,
        description="True when the shopper asked to browse a category/search (e.g. 'what hoodies do you have?'): "
        "the product_ids are then shown as a results grid on the web page, not just in the chat.",
    )
    results_title: Optional[str] = Field(
        default=None, description="Short heading for the page results, e.g. 'Hoodies' or 'Navy crewnecks under $60'"
    )


class ToolEvent(BaseModel):
    """One tool call made during the turn."""

    tool: str
    args: dict = Field(default_factory=dict)
    duration_ms: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    products: List[ProductCard] = Field(default_factory=list, description="Cards shown inside the chat (1-3 items)")
    page_results: Optional["PageResults"] = Field(
        default=None, description="Search results to render as cards on the page; None if this turn was not a search"
    )
    tool_events: List[ToolEvent] = Field(default_factory=list)
    model: str
    safety_notice: Optional[str] = Field(default=None, description="Shown when sensitive data was removed from the message")
    masked_message: Optional[str] = Field(default=None, description="The shopper's message after masking, so the UI can hide the original")


# ------------------------------------------------------------------ Problem 6: lookup tool results


class ProductMatch(BaseModel):
    """One candidate from find_product, enough for the agent to pick the right product_id."""

    product_id: str
    name: str
    garment_type: str
    price: float = Field(description="USD")


class ProductLookup(BaseModel):
    """Result of find_product(query)."""

    query: str
    matches: List[ProductMatch] = Field(default_factory=list, description="Best matches first; empty if nothing matched")


class ProductInfo(BaseModel):
    """Result of get_product_info(product_id): the full catalogue row the shopper cares about."""

    found: bool
    product_id: str
    name: Optional[str] = None
    garment_type: Optional[str] = None
    description: Optional[str] = None
    colors: List[str] = Field(default_factory=list)
    search_tags: List[str] = Field(default_factory=list)
    message: Optional[str] = Field(default=None, description="Why the lookup failed, if found is false")


class PriceInfo(BaseModel):
    """Result of get_price(product_id)."""

    found: bool
    product_id: str
    name: Optional[str] = None
    price: Optional[float] = Field(default=None, description="Price in US dollars from the catalogue table")
    currency: str = "USD"
    message: Optional[str] = None


class SizeStock(BaseModel):
    size: str = Field(description="XS, S, M, L, XL or XXL")
    quantity: int = Field(description="Units in stock right now (0 = sold out)")
    in_stock: bool


class StockInfo(BaseModel):
    """Result of get_stock(product_id, size=None)."""

    found: bool
    product_id: str
    name: Optional[str] = None
    requested_size: Optional[str] = Field(default=None, description="Normalized size the shopper asked about, if any")
    requested_size_quantity: Optional[int] = None
    requested_size_in_stock: Optional[bool] = None
    sizes: List[SizeStock] = Field(default_factory=list, description="Every size, in XS..XXL order")
    total_units: int = 0
    sizes_in_stock: List[str] = Field(default_factory=list)
    sizes_sold_out: List[str] = Field(default_factory=list)
    message: Optional[str] = None


# ------------------------------------------------------------------ Problem 7: catalogue search


class SearchHit(BaseModel):
    """One product found by search_catalogue (short, so a long list stays small for the model)."""

    product_id: str
    name: str
    garment_type: str
    price: float = Field(description="USD")
    colors: List[str] = Field(default_factory=list)
    short_description: str = Field(description="First sentence of the catalogue description")


class SearchResults(BaseModel):
    """Result of search_catalogue: products matching a category and/or keywords."""

    query: str
    category: Optional[str] = Field(default=None, description="Normalized category used, e.g. 'hoodie'")
    color: Optional[str] = None
    max_price: Optional[float] = None
    total_matches: int = Field(description="How many products matched before the limit")
    products: List[SearchHit] = Field(default_factory=list)
    message: Optional[str] = None


class PageResults(BaseModel):
    """Search results the website renders as product cards on the page (the Problem 7 contract)."""

    title: str = Field(description="Heading shown above the cards, e.g. 'Hoodies'")
    query: str
    total_matches: int
    products: List[ProductCard] = Field(default_factory=list)





# ------------------------------------------------------------------ Problem 9: alternatives + safety


class Alternative(BaseModel):
    product_id: str
    name: str
    garment_type: str
    price: float = Field(description="USD")
    units_in_size: Optional[int] = Field(default=None, description="Units in stock in the requested size")
    shared_features: List[str] = Field(default_factory=list, description="Tags/colors it shares with the original item")


class Alternatives(BaseModel):
    """Result of find_alternatives(product_id, size): similar items that ARE in stock."""

    found: bool
    product_id: str
    name: Optional[str] = None
    category: Optional[str] = None
    size: Optional[str] = None
    alternatives: List[Alternative] = Field(default_factory=list, description="Best first: most shared features, then closest price")
    message: Optional[str] = None


ChatResponse.model_rebuild()
StoredMessage.model_rebuild()

"""Campus Customs chatbot agent: PydanticAI wiring.

- System prompt: prompts/prompt.md (read at startup).
- Model: PORTKEY_MODEL from Documents/codex/.env (default gpt-5.6-luna), called through
  the Portkey gateway with the OpenAI-compatible client. No sampling params are sent.
- Tools: functions in tools.py, registered below.
- Output: models.AgentReply (reply text + product_ids), turned into a ChatResponse
  whose product cards are built from the database, not from the model.

FastAPI (main.py) calls run_chat() for every website chat message.

Quick check from the backend/ folder:
    python3 agent.py "What kinds of things do you sell?"
    python3 agent.py --list-models
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI, OpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.usage import UsageLimits

import tools
from models import (
    AgentReply,
    Alternatives,
    CurrentPage,
    CustomerProfile,
    PageContext,
    ChatResponse,
    HistoryMessage,
    PriceInfo,
    ProductInfo,
    PageResults,
    ProductLookup,
    SearchResults,
    StockInfo,
    StoreOverview,
    ToolEvent,
)

# Finds Documents/codex/.env (walking up from the current folder), per AGENTS.md.
load_dotenv(find_dotenv(usecwd=True))

HERE = Path(__file__).resolve().parent
PROMPT_PATH = HERE / "prompts" / "prompt.md"
BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")
MODEL_NAME = os.getenv("PORTKEY_MODEL", "gpt-5.6-luna")
MAX_AGENT_REQUESTS = 6   # bounded agent loop: model calls per chat turn
MAX_HISTORY = 12         # earlier messages sent back to the model


AUDIT_PATH = Path(os.getenv("AUDIT_PATH", HERE.parent / "output" / "audit_trail.json"))
RESULT_SUMMARY_CHARS = 240   # tool results are summarized, never stored whole
_audit_lock = threading.Lock()


def summarize_result(result: object) -> Optional[str]:
    """Short, human-readable summary of a tool result for the audit trail."""
    if result is None:
        return None
    if hasattr(result, "model_dump"):
        data = result.model_dump()
        # Lists of products are summarized as a count plus the first few ids.
        for key in ("products", "matches", "alternatives", "sizes"):
            if isinstance(data.get(key), list):
                items = data[key]
                ids = [i.get("product_id") or i.get("size") for i in items[:3] if isinstance(i, dict)]
                data[key] = f"{len(items)} items, e.g. {ids}"
        text = json.dumps(data, default=str)
    else:
        text = str(result)
    return text if len(text) <= RESULT_SUMMARY_CHARS else text[: RESULT_SUMMARY_CHARS - 1] + "…"


def append_audit(entry: dict) -> None:
    """Append one entry to output/audit_trail.json without rewriting earlier entries.

    The file is a JSON array. New entries are written by seeking to the closing ']' and writing
    ',<entry>\n]', so old runs are never erased and the file stays valid JSON."""
    line = json.dumps(entry, ensure_ascii=False, default=str)
    with _audit_lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not AUDIT_PATH.exists() or AUDIT_PATH.stat().st_size == 0:
            AUDIT_PATH.write_text("[\n" + line + "\n]\n", encoding="utf-8")
            return
        with open(AUDIT_PATH, "rb+") as f:
            f.seek(0, os.SEEK_END)
            pos = f.tell()
            while pos > 0:                      # find the final ']'
                pos -= 1
                f.seek(pos)
                if f.read(1) == b"]":
                    break
            f.seek(pos)
            f.truncate()
            f.write((",\n" + line + "\n]\n").encode("utf-8"))


def stop_reason_of(messages: List[ModelMessage]) -> str:
    """Why the agent loop ended: the model's final structured answer, or its finish reason."""
    for m in reversed(messages):
        if isinstance(m, ModelResponse):
            if any(isinstance(p, ToolCallPart) and p.tool_name.startswith("final_result") for p in m.parts):
                return "final_output"
            return str(getattr(m, "finish_reason", None) or "end_turn")
    return "unknown"


@dataclass
class Deps:
    """Per-turn state shared with the tools. tool_events records every call for the UI."""

    customer: Optional[CustomerProfile] = None    # logged-in shopper, None for guests
    page: Optional[CurrentPage] = None            # what the shopper is looking at
    tool_events: List[ToolEvent] = field(default_factory=list)
    last_search: Optional[SearchResults] = None   # most recent search_catalogue result this turn
    audit_tools: List[dict] = field(default_factory=list)   # tool calls with result summaries (audit trail)

    def record(self, tool: str, args: dict, started: float, result: object = None) -> None:
        event = ToolEvent(tool=tool, args=args, duration_ms=int((time.perf_counter() - started) * 1000))
        self.tool_events.append(event)
        self.audit_tools.append({"tool": tool, "args": args, "duration_ms": event.duration_ms,
                                 "result": summarize_result(result)})


def make_client() -> AsyncOpenAI:
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY not found. Add it to Documents/codex/.env")
    return AsyncOpenAI(api_key=key, base_url=BASE_URL, max_retries=3, timeout=60)


def build_agent() -> Agent[Deps, AgentReply]:
    model = OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=make_client()))
    agent: Agent[Deps, AgentReply] = Agent(
        model,
        deps_type=Deps,
        output_type=AgentReply,
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        retries=2,
    )

    @agent.instructions
    def customer_and_page_context(ctx: RunContext[Deps]) -> str:
        """Added to the system prompt on every turn: who is chatting and which page they are on."""
        c, pg = ctx.deps.customer, ctx.deps.page
        lines = ["## Current session (from the website, trusted)"]
        if c:
            lines.append(
                f"- Customer: logged in as {c.first_name} {c.last_name} <{c.email}> "
                f"(customer since {c.member_since}). Their chat history is saved."
            )
        else:
            lines.append("- Customer: guest (not logged in). You don't know their name or email; chat is not saved.")
        if pg and pg.product_id:
            lines.append(
                f"- Page: product detail page for **{pg.product_name}** (product_id `{pg.product_id}`, "
                f"{pg.garment_type}, ${pg.price:.2f}, design colors: {', '.join(pg.colors)}). "
                "Words like 'this', 'it', 'this one' or 'this shirt' mean this product unless the shopper names another."
            )
        elif pg:
            lines.append(f"- Page: {pg.page_name} ({pg.path}). No single product is open.")
        return "\n".join(lines)

    @agent.tool
    def get_customer_profile(ctx: RunContext[Deps]) -> Optional[CustomerProfile]:
        """The logged-in customer's profile: user_id, first_name, last_name, email, member_since date and
        number of saved chat messages. Returns null for a guest."""
        started = time.perf_counter()
        ctx.deps.record("get_customer_profile", {}, started, ctx.deps.customer)
        return ctx.deps.customer

    @agent.tool
    def get_current_page(ctx: RunContext[Deps]) -> Optional[CurrentPage]:
        """The page the shopper is viewing right now. On a product page this includes product_id, name,
        garment_type, price (USD) and design colors, which is what 'this' or 'it' refers to."""
        started = time.perf_counter()
        ctx.deps.record("get_current_page", {}, started, ctx.deps.page)
        return ctx.deps.page

    @agent.tool
    def get_store_overview(ctx: RunContext[Deps]) -> StoreOverview:
        """Overview of the whole shop from the database: number of products, each garment type
        with its product count, the lowest and highest price in USD, and the sizes sold."""
        started = time.perf_counter()
        result = tools.get_store_overview()
        ctx.deps.record("get_store_overview", {}, started, result)
        return result

    @agent.tool
    def find_product(ctx: RunContext[Deps], query: str, limit: int = 5) -> ProductLookup:
        """Find products by name or description words (e.g. "basic hoodie big yale", "morse quarter zip").
        Returns up to `limit` (max 10) matches, best first, each with product_id, name, garment_type and
        price in USD. Use it to get the product_id before calling get_product_info, get_price or get_stock.
        Matches can be loose: check the name really fits what the shopper asked for."""
        started = time.perf_counter()
        result = tools.find_product(query, limit)
        ctx.deps.record("find_product", {"query": query, "limit": limit}, started, result)
        return result

    @agent.tool
    def get_product_info(ctx: RunContext[Deps], product_id: str) -> ProductInfo:
        """Full product details from the catalogue table: name, garment_type, description, colors in the
        design, and search tags. found=false means the product_id does not exist."""
        started = time.perf_counter()
        result = tools.get_product_info(product_id)
        ctx.deps.record("get_product_info", {"product_id": product_id}, started, result)
        return result

    @agent.tool
    def get_price(ctx: RunContext[Deps], product_id: str) -> PriceInfo:
        """Current price of one product in US dollars, from the catalogue table.
        found=false means the product_id does not exist."""
        started = time.perf_counter()
        result = tools.get_price(product_id)
        ctx.deps.record("get_price", {"product_id": product_id}, started, result)
        return result

    @agent.tool
    def get_stock(ctx: RunContext[Deps], product_id: str, size: Optional[str] = None) -> StockInfo:
        """Live inventory for one product from the inventory table: units in stock for every size
        (XS, S, M, L, XL, XXL), total units, sizes in stock and sizes sold out. Pass `size` (e.g. "M",
        "medium", "2XL") when the shopper asks about a specific size; then requested_size_quantity and
        requested_size_in_stock answer it directly, and `message` explains a sold-out or unavailable size."""
        started = time.perf_counter()
        result = tools.get_stock(product_id, size)
        args = {"product_id": product_id} | ({"size": size} if size else {})
        ctx.deps.record("get_stock", args, started, result)
        return result

    @agent.tool
    def search_catalogue(
        ctx: RunContext[Deps],
        query: str = "",
        category: Optional[str] = None,
        color: Optional[str] = None,
        max_price: Optional[float] = None,
        limit: int = 24,
    ) -> SearchResults:
        """Search the catalogue for a category and/or keywords, to answer browse questions like
        "what hoodies do you have?", "soccer gear", "Morse college items", "navy crewnecks under $60".
        - category: hoodie, crewneck, t-shirt, quarter-zip, jacket, fleece, long-sleeve, sweatshirt, mockneck
        - query: other keywords (sport, college, school, 'mom', 'vintage'...); every keyword must match
        - color: one color word, matched against the design's colors
        - max_price: highest price in USD
        Returns total_matches and up to `limit` (max 30) products with product_id, name, garment_type,
        price (USD), colors and a one-sentence description. Empty products + message means nothing matched."""
        started = time.perf_counter()
        result = tools.search_catalogue(query, category, color, max_price, limit)
        ctx.deps.last_search = result
        args = {k: v for k, v in {"query": query, "category": category, "color": color, "max_price": max_price}.items() if v}
        ctx.deps.record("search_catalogue", args, started, result)
        return result

    @agent.tool
    def find_alternatives(
        ctx: RunContext[Deps], product_id: str, size: Optional[str] = None, limit: int = 4
    ) -> Alternatives:
        """Similar products that ARE in stock: same category as product_id (hoodie, crewneck, t-shirt...),
        available in `size` if given (e.g. "XS", "medium"), ranked by shared tags/colors and closest price
        in USD. Returns up to `limit` (max 8) alternatives with units_in_size. Use it when the shopper's
        size is sold out or the item doesn't fit their need."""
        started = time.perf_counter()
        result = tools.find_alternatives(product_id, size, limit)
        ctx.deps.record("find_alternatives", {"product_id": product_id} | ({"size": size} if size else {}), started, result)
        return result

    return agent


_agent: Optional[Agent[Deps, AgentReply]] = None


def get_agent() -> Agent[Deps, AgentReply]:
    """Build the agent once, on first use, so the API can start even before a key is set."""
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


def to_model_history(history: List[HistoryMessage]) -> List[ModelMessage]:
    """Website chat history -> PydanticAI messages (text only)."""
    messages: List[ModelMessage] = []
    for m in history[-MAX_HISTORY:]:
        if m.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=m.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=m.content)]))
    return messages


async def run_chat(
    message: str,
    history: Optional[List[HistoryMessage]] = None,
    user: Optional[dict] = None,
    page: Optional[PageContext] = None,
) -> ChatResponse:
    """Run one chat turn through the agent and return the website's ChatResponse.

    Logged-in users: history comes from the chat_messages table (not from the browser), and both the
    question and the answer are saved after a successful turn. Guests: the browser's on-screen
    history is used and nothing is saved."""
    # Improvement: sensitive data (card numbers, SSNs, passwords) is masked before it reaches the
    # model, the logs or the database.
    message, redacted = tools.redact_sensitive(message)
    customer = tools.get_customer_profile(user["id"]) if user else None
    current_page = tools.describe_page(page.path, page.product_id) if page else None
    deps = Deps(customer=customer, page=current_page)

    if customer:
        saved = tools.load_chat_history(customer.user_id, limit=tools.HISTORY_FOR_MODEL)
        history = [HistoryMessage(role=m.role, content=m.content[:4000]) for m in saved]

    run_id = uuid.uuid4().hex[:12]
    started = time.perf_counter()
    audit = {
        "run_id": run_id,
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": MODEL_NAME,
        "customer": f"user:{customer.user_id}" if customer else "guest",
        "page": current_page.path if current_page else None,
        "message": message[:200],
        "redacted": redacted,
    }
    try:
        result = await get_agent().run(
            message,
            deps=deps,
            message_history=to_model_history(history or []),
            usage_limits=UsageLimits(request_limit=MAX_AGENT_REQUESTS),
        )
    except UsageLimitExceeded as exc:
        audit.update(stop_reason="request_limit", error=str(exc), tool_calls=deps.audit_tools,
                     duration_ms=int((time.perf_counter() - started) * 1000))
        append_audit(audit)
        raise
    except Exception as exc:
        audit.update(stop_reason="error", error=repr(exc)[:300], tool_calls=deps.audit_tools,
                     duration_ms=int((time.perf_counter() - started) * 1000))
        append_audit(audit)
        raise
    response = build_response(result.output, deps)
    usage = result.usage() if callable(result.usage) else result.usage
    audit.update(
        stop_reason=stop_reason_of(result.all_messages()),
        model_requests=usage.requests,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        tool_calls=deps.audit_tools,
        reply=response.reply[:200],
        product_ids=[p.product_id for p in (response.page_results.products if response.page_results else response.products)][:12],
        show_on_page=response.page_results is not None,
        duration_ms=int((time.perf_counter() - started) * 1000),
    )
    append_audit(audit)
    if redacted:
        response.safety_notice = (
            f"For your safety we removed the {' and '.join(sorted(set(redacted)))} from your message. "
            "Never share payment or password details in chat."
        )
        response.masked_message = message

    if customer:
        shown = response.page_results.products if response.page_results else response.products
        tools.save_chat_message(customer.user_id, "user", message)
        tools.save_chat_message(customer.user_id, "assistant", response.reply, shown)
    return response


PAGE_LIMIT = 24   # max cards in the page results grid
CHAT_LIMIT = 3    # max mini cards inside the chat bubble


def build_response(reply: AgentReply, deps: Deps) -> ChatResponse:
    """Turn the agent's structured output into the website contract.

    - show_on_page=True (a browse/search question): the product_ids become PageResults, which the
      website renders as a grid of normal product cards. If the model forgot the ids, the ids from
      this turn's search_catalogue call are used, so the grid always matches what the tool found.
    - otherwise: up to 3 small cards inside the chat.
    Cards are always rebuilt from the database (tools.cards_for_ids), and unknown ids are dropped."""
    page_results: Optional[PageResults] = None
    chat_cards = []
    if reply.show_on_page:
        ids = reply.product_ids or [p.product_id for p in (deps.last_search.products if deps.last_search else [])]
        cards = tools.cards_for_ids(ids, limit=PAGE_LIMIT)
        if cards:
            search = deps.last_search
            page_results = PageResults(
                title=reply.results_title or (search.category.title() + "s" if search and search.category else "Search results"),
                query=search.query if search else "",
                total_matches=max(len(cards), search.total_matches if search else 0),
                products=cards,
            )
    else:
        chat_cards = tools.cards_for_ids(reply.product_ids, limit=CHAT_LIMIT)
    return ChatResponse(
        reply=reply.reply,
        products=chat_cards,
        page_results=page_results,
        tool_events=deps.tool_events,
        model=MODEL_NAME,
    )


def tool_calls_in(messages: List[ModelMessage]) -> List[str]:
    return [p.tool_name for m in messages for p in getattr(m, "parts", []) if isinstance(p, ToolCallPart)]


def list_models() -> None:
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        sys.exit("PORTKEY_API_KEY not found. Add it to Documents/codex/.env")
    for m in OpenAI(api_key=key, base_url=BASE_URL).models.list():
        print(m.id)


def main() -> None:
    import asyncio

    if "--list-models" in sys.argv:
        list_models()
        return
    question = " ".join(a for a in sys.argv[1:]) or "What kinds of things do you sell?"
    try:
        res = asyncio.run(run_chat(question))
    except Exception as exc:  # show the real error body, never a fake answer
        sys.exit(f"Agent call failed: {exc!r}")
    print(f"[model] {res.model}")
    for ev in res.tool_events:
        print(f"[tool] {ev.tool}({ev.args}) {ev.duration_ms} ms")
    print(res.reply)
    print("Next: start the API with  uvicorn main:app --reload --port 8000")


if __name__ == "__main__":
    main()

# Usability Improvements — Campus Customs

Four improvements were added after the core shop worked: two on the front end and two in the agent/backend. Each one is live in the running app; the "Where to see it" line says how to find it.

---

## Front end

### 1. Product filters and sorting on the Products page

**What I added**
- Category chips (**All · Hoodies · Crewnecks · T-shirts · Quarter-zips · Fleece · Jackets**), an **In stock only** checkbox, and a **sort** menu (Name A–Z, Price low→high, Price high→low, Most in stock), alongside the existing search box.
- Filters are stored in the URL (e.g. `/products?category=hoodie&sort=price_asc&instock=1`), so they survive Back, a refresh, or a shared link. A "clear filters" link resets them.
- The backend's `GET /api/products` gained `category`, `sort`, and `in_stock` parameters and now returns `total_units` for each product. A product with no stock at all gets a red **Sold out** badge on its card.

**Why it helps**
- **Shopper:** 102 products in one long grid is hard to scan. A parent looking for a hoodie under budget can get "Hoodies, cheapest first, in stock" in two clicks instead of scrolling past T-shirts and sold-out items.
- **Business:** shoppers who find something quickly are more likely to buy. Hiding sold-out items cuts frustration and avoids dead-end clicks.

**Where to see it:** Products page → click **Hoodies** → choose **Price: low to high** → tick **In stock only** (27 hoodies, starting with the $45 UA Gameday Double Knit Hood).

### 2. Size picker with live availability + "Ask about this item"

**What I added**
- On every product detail page the size boxes are now buttons. Selecting one shows a clear status line: **"In stock in M (20 available)"** in green, **"Only 2 left in L — order soon!"** in amber (5 or fewer), or **"Size XS is sold out. In stock: S, M, L, XXL."** in red. Low-stock sizes say "Only N" right on the button.
- A **💬 Ask about this item** button opens the chat with a ready-made question that matches what the shopper picked. For a sold-out size it asks, "Size XS of the Baseball Left Chest Crewneck is sold out. Can you suggest something similar in XS?" They just press Send.

**Why it helps**
- **Shopper:** answers the most common question ("do you have my size?") without reading a table, and turns a sold-out dead end into a one-click path to help. Typing a question on a phone is slow; a prefilled one isn't.
- **Business:** "only N left" creates gentle urgency. Linking the product page to the assistant (together with backend improvement 3 below) recovers sales that would otherwise be lost to a sold-out size.

**Where to see it:** open the **Baseball Left Chest Crewneck** → click **XS** (red sold-out message) → click **Ask about this item** → Send.

---

## Agent / backend

### 3. `find_alternatives` tool — in-stock suggestions when a size is sold out

**What I added**
- A new agent tool, `find_alternatives(product_id, size, limit)` in `backend/tools.py`, with return type `Alternatives` / `Alternative` in `models.py`. It finds products in the **same category** (hoodie, crewneck, t-shirt…) that **have stock in the requested size**, ranked by how many tags and colors they share with the original (e.g. "college merch", "left chest logo", "navy") and then by closest price. Each result includes `units_in_size` from the inventory table.
- `prompts/prompt.md` now says: when `get_stock` reports a sold-out size, call `find_alternatives` and suggest 1–3 in-stock items with exact prices, shown as product cards.

**Why it helps**
- **Shopper:** instead of "sorry, sold out", they get real, available options in their size, with prices and stock counts from the database (never invented).
- **Business:** 145 of the 612 size/product combinations are sold out, so this happens often. Redirecting to a similar in-stock item keeps the sale.

**Where to see it:** in the chat, "Do you have the Baseball Left Chest Crewneck in XS?" → the reply says XS is sold out and suggests the **Davenport College Crewneck ($58.00, 20 in XS)**, **Pierson College Crewneck ($58.00, 12 in XS)**, and **District Vit Crewneck Vintage Standing Bulldog ($58.00, 20 in XS)** as cards. The tool chips show `get_stock` → `find_alternatives`.

### 4. Input safety filter + chat rate limit

**What I added**
- **Sensitive-data masking before the model sees anything** (`tools.redact_sensitive`, called first in `agent.run_chat`):
  - Payment card numbers (13–19 digits that pass the Luhn checksum, so order numbers aren't caught) → `[card number removed •••• 4242]`
  - US SSNs (`123-45-6789`) → `[SSN removed]`
  - "password / PIN / CVV is …" → `password is [removed]`

  The masked text is what goes to the AI model, the server logs, and the `chat_messages` table. The response carries a `safety_notice` (shown in an amber 🔒 box in the chat) and `masked_message`, which replaces the shopper's on-screen bubble with the masked version.
- **Rate limit:** at most 15 chat messages per minute per logged-in user (or per IP for guests). Beyond that `/api/chat` returns HTTP 429 with a friendly "please wait a moment" message instead of calling the model.
- The prompt now also states that the site has no checkout and the chat can't take payments or orders, so the agent never invents a payment flow.

**Why it helps**
- **Shopper:** if someone pastes their card or password by mistake, it never leaves our server, isn't stored in their saved chat history, and isn't sent to a third-party AI provider. They're also told why.
- **Business:** avoids storing payment data the shop isn't allowed or equipped to hold (a PCI and privacy risk), and the rate limit caps runaway AI costs from a bot or a stuck client. Each chat call can make up to 6 model requests.

**Where to see it:** in the chat, type "Can I just pay here? My card is 4242 4242 4242 4242" → your bubble changes to "My card is [card number removed •••• 4242]", and the reply comes with the 🔒 safety notice. Sending more than 15 messages within a minute returns the "sending messages very quickly" message.

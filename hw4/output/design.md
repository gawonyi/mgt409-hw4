# Design — Campus Customs storefront

**Idea:** make the site feel like walking into a real campus shop: felt pennants, stitched patches, and price tags hanging off the merch. One bold element (the pennant hero and hang-tag prices) carries the personality. Everything else stays quiet so the product photos do the selling.

## What changed and why it helps sales

| Change | What it looks like | Why it keeps people shopping |
|---|---|---|
| **Collegiate type** | Headlines, prices and the chat header use **Graduate** (a varsity block-letter face). Body text uses **Libre Franklin** for easy reading. Both load from Google Fonts. | Instantly reads "college shop", not "generic template", which builds trust that this is the real campus store. The readable body face keeps long product descriptions comfortable. |
| **Color system** | Old Campus navy `#12284B` for the brand, a cool chalk background `#F3F5F8`, and a single pennant-gold accent `#E2B33C` used only for attention (primary hero button, price tags, the current nav item, selected size, focus rings, low stock). Red is kept for sold out, green for in stock and tool activity. | Shoppers learn quickly that gold means "look here". Because the accent is reserved for the price and the next action, the eye goes from photo to price to button. |
| **Stitched-patch hero with a swinging pennant** | The navy hero has a felt-dot texture and a dashed gold "stitch" border. A white felt pennant with a gold trim swings in once on page load. Two clear actions: **Shop all 102 products** and **Ask what's in stock**, which opens the chat with that question. | A memorable first screen gives visitors a reason to stay. The second button routes hesitant shoppers straight to the assistant instead of letting them bounce. |
| **Shop-by tiles** | Four tiles under the hero (Hoodies, Crewnecks, Varsity sports, Quarter-zips) with one-line descriptions. They link to the filtered Products page. | One click from the home page to a focused, relevant grid, so there are fewer steps to a product someone actually wants. |
| **Hang-tag product cards** | Price sits on a gold store tag with a punched hole in the image corner. The card shows type, name and two description lines. Hovering tilts the tag and darkens the border. Products that are fully sold out show a dimmed photo and a red badge. | Price is visible at a glance, like browsing a real rack. Dimming sold-out stock pushes attention to items that can actually be bought. |
| **Product page hierarchy** | Large image on the left (stays in view while you scroll on desktop), big display-font price, then size buttons. Sold-out sizes are crossed out on a hatched background, the selected size turns navy with a gold underline, and a colored status bar shows in stock / only N left / sold out. | The buying decision (size + availability) is the most prominent thing after the photo. "Only N left" adds honest urgency. |
| **"Ask the shop counter" chat** | Navy header in the varsity font with a gold stitch line. Rounded speech bubbles (navy for the shopper, white for the shop). Product mini-cards, mint tool chips, an amber safety notice, and a gold "shown on the page" pill. The chat button has a gold ring, and the panel scales open from the button. | The assistant feels like part of the store, not a bolted-on widget, so people are more willing to ask. Every answer that leads to a product card is one click from the product page. |
| **Chat results on the page** | When the chat finds products, a "From your chat" panel with a gold edge slides in at the top of the page. | Makes the chat's answer impossible to miss and turns a question into a browsable grid. |
| **Motion, used sparingly** | Only three moments: the pennant swing on load, the chat panel opening, and the results panel appearing. All motion is turned off for visitors who choose "reduce motion" in their system settings. | Motion marks what changed without distracting from shopping, and it respects accessibility settings. |
| **Quality floor** | Visible gold focus rings for keyboard users, layouts that stack on phones (hero, product page and chat panel all adapt), and a sticky nav. | Works for everyone on any device, so nobody is lost to a broken layout. |

## Files

- `frontend/index.html` — font links.
- `frontend/src/styles.css` — full rewrite around the tokens above.
- `frontend/src/pages/Home.tsx` — pennant hero, Shop-by tiles, "Hoodie season" picks (in-stock hoodies sorted by stock).
- `frontend/src/components/ProductCard.tsx` — hang-tag card.
- `frontend/src/components/ChatWidget.tsx` — "Ask the shop counter" header.

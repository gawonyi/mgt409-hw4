# Campus Customs Shop + Chatbot (MGT409 Homework 4)

A Campus Customs storefront with an AI shopping assistant. Shoppers can browse Yale apparel, create an account, and chat about merch. The chat answers price and stock questions honestly from a local SQLite database, and matching products appear as cards on the page.

- **Front end:** React + Vite + TypeScript (`frontend/`)
- **Backend:** FastAPI (`backend/main.py`) with a PydanticAI agent: `backend/prompts/prompt.md`, `backend/agent.py`, `backend/tools.py`, and `backend/models.py`
- **Model:** `gpt-5.6-luna` through the Portkey gateway (configurable)
- **Docs:** `output/harness.md` (how the system works), `output/usability.md`, `output/design.md`, `output/app_check.html` (tested screenshots), `output/audit_trail.json` (agent run log), and `AI_prompts.md` (my prompts)

## 1. Requirements

- Python 3.10+ (`python3`)
- Node.js 18+ and npm
- A Portkey API key (or another OpenAI-compatible key and base URL)

## 2. Place the data pack (not in git)

The database and product images are **not** committed. Unzip the course `data.zip` **inside this `hw4/` folder** so you have:

```text
hw4/
└── data/
    ├── campus_customs.db
    └── products/          # images referenced by the catalogue table
```

The backend looks for `../data` relative to `backend/`. To keep the data elsewhere, set `DATA_DIR=/path/to/data`.

## 3. Add your API key

Copy the template and fill in real values. `.env` is git-ignored.

```bash
cp .env.example .env
# edit .env: PORTKEY_API_KEY=..., optionally PORTKEY_MODEL=gpt-5.6-luna and SECRET_KEY=<long random string>
```

The backend loads the nearest `.env` above the folder you run it from, so a `.env` in `hw4/` or in a parent folder (e.g. `Documents/codex/.env`) works.

## 4. Run the backend (terminal 1)

```bash
cd hw4
python3 -m pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

- Health check: <http://localhost:8000/api/health> should show `"db_found": true` and `"api_key_loaded": true`.
- Optional: test the agent without the website by running `python3 agent.py "What hoodies do you have?"` from `backend/`.

## 5. Run the front end (terminal 2)

```bash
cd hw4/frontend
npm install
npm run dev
```

Open <http://localhost:5173>. The Vite dev server proxies `/api` and `/media` to the backend on port 8000, so both terminals must be running.

## 6. Try it

- **Test account:** `test@campuscustoms.yale.edu` / `password` (or create your own on **Create account**).
- In the chat (bottom right), try:
  - "How much is the Yale Mom Hoodie, and how many are left in size M?" → price and stock from the DB
  - "What hoodies do you have?" → matching product cards appear on the page
  - On a product page: "Do you have this in pink?" → the agent knows which product "this" is
- Log in, chat, then reload: your conversation is saved and reloaded.
- **Products page:** category chips, "In stock only", and sorting. On a product page, pick a size and use **Ask about this item**.

Each chat run is appended to `output/audit_trail.json`. See `output/harness.md` for the architecture, models, tools, safety rules, and limits.

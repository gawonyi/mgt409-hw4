# AI Prompts Log — MGT409 Homework 4: Campus Customs Shop + Chatbot

Gawon Yi

This file records the prompts I gave my vibe coder, one section per problem.

---

## Problem 1: Vibe coder prompts

**Prompt:**

> Create an `AI_prompts.md` file when you begin the assignment and update it throughout the project. This file should serve as a record of the prompts you actually gave to your vibe coding tool.
> For each problem, explain the task to the vibe coder using your own wording. Do not simply copy the entire assignment page or send the assignment link and ask the AI to complete everything.
> Include a separate section for every problem. Each section should contain:
>
> - The problem number and title
> - At least one prompt you personally wrote, preferably in your own words
> - If you used a follow-up prompt, include it as well, along with one sentence explaining what was missing or insufficient in the first response
>
> You do not need to write a separate essay proving your work. Your functioning website, database activity, screenshots, and prompt log will serve as evidence that you completed the assignment.

**Follow-up prompt:** None needed.

---

## Problem 2: Analyze the database

**Prompt:**

> Review the database file `data/campus_customs.db` and become familiar with the fields contained in each table.
> At a minimum, you should understand the `catalogue`, `inventory`, and `users` tables.
> Create the file `output/harness.md`. In this file, list each table and its fields, and add a brief explanation of why each field is relevant to either the shop or the chatbot.
> You will continue expanding this harness file in later problems to document items such as models, tools, safety, and technical specifications.

**Follow-up prompt:** None needed.

---

## Problem 3: Build the Campus Customs website

**Prompt:**

> Set up a Campus Customs front end using React, Vite, and TypeScript. Add a navigation bar at the top with links to the main pages:
>
> - Home
> - Products
> - About Us
> - Log in
> - Create account
>
> Use yalebulldogblue.com as inspiration for the Campus Customs tone and wording on the Home and About Us pages, but write the content in your own words rather than copying text from the original site.
> On the Products page, display product images from the catalogue using the image paths stored in the database, along with basic product details such as the product name, price, and a short description.
> Each product should link to its own detail page. This page should show a large product image on one side and the complete product information on the other, including the description, price, and size or stock information when available. Clicking a product card on the Products page should take the shopper to this detail page.
> Add a chat interface in the bottom-right corner of the website. A floating chat panel is acceptable. For now, it does not need to connect to an agent; a placeholder that can later call the backend is sufficient for this problem.
> You will soon need a small API to retrieve data from the database. You may begin by creating a basic FastAPI application in `backend/main.py` that serves products and images, and then expand it into the full agent backend in Problem 5.

**Follow-up prompt:** None needed.

---

## Problem 4: Create account and login

**Prompt:**

> Create a standard account registration and login process.
>
> - Create account: collect the user's first name, last name, email, and password. Adding a password confirmation field is optional but recommended.
> - Log in: require the user's email and password.
>
> Store all newly created accounts in the `users` table. Passwords must be stored securely so they cannot be accessed directly by unauthorized users, whether human or AI.
> The starter database already includes a test account that you can use during development:
>
> - Email: `test@campuscustoms.yale.edu`
> - Password: `password`
>
> Verify that the provided test account can successfully log in, and also confirm that a newly created account can log in properly.
> Update `output/harness.md` to explain how authentication is implemented, including what user information is stored and how passwords are secured.

**Follow-up prompt:** None needed.

---

## Problem 5: PydanticAI agent backend

**Prompt:**

> Use the Portkey API key from the .env file in my codex folder.
>
> Build the shop chatbot using a PydanticAI agent that runs behind a FastAPI backend and connects to the chat widget on your front end. Place the FastAPI application in `backend/main.py`, which should be the file launched with Uvicorn. Keep the agent organized into the following four files alongside it, following a structure similar to Homework 3:
>
> - `backend/prompts/prompt.md` — the system prompt, which you will continue expanding in later problems
> - `backend/agent.py` — the agent setup and wiring
> - `backend/tools.py` — the tools available to the agent
> - `backend/models.py` — the Pydantic and PydanticAI structured data types
>
> In `main.py`, create a chat endpoint so that messages sent from the website are passed to the agent and the agent's response is returned to the front end. You may also add any additional endpoints needed for products or authentication. The agent will require an API key for the AI model you use.
> Add the Campus Customs tone and basic safety guidelines to `prompts/prompt.md`. You will expand both the tools and safety instructions in later problems. Add or update the necessary types in `models.py` for items such as chat responses and product cards.
> Update `output/harness.md` to explain how the front end communicates with FastAPI and how the agent is initialized, including the prompt file and model being used.
> Make sure the backend can be started from inside the `backend/` directory with the following command:
>
> ```
> uvicorn main:app --reload --port 8000
> ```

**Follow-up prompt:** None needed.

---

## Problem 6: Tools: product info and stock

**Prompt:**

> Provide the agent with tools that retrieve accurate information from `campus_customs.db`, including:
>
> - Product descriptions
> - Prices
> - Current inventory levels, including stock by size when a customer asks about a specific size
>
> The agent must rely on the database rather than making up prices or inventory counts. If a requested size is unavailable, the agent should state that clearly.
> Update `prompts/prompt.md` so the agent knows to use these tools whenever a user asks about pricing or stock. Add or revise the corresponding return types in `models.py`.
> In `output/harness.md`, document each tool and explain which model fields you used for the lookup results and why you selected them.

**Follow-up prompt:** None needed.

---

## Problem 7: Chat search that updates the page

**Prompt:**

> Add a feature that allows the website to respond dynamically when a customer asks about a category of products. For example, if a shopper asks, "What hoodies do you have?", the agent should search the catalogue and the website should display the matching products as cards that include an image, product name, price, and brief information.
> This should work through a structured API contract: the agent returns structured product matches, and the front end uses those results to render the product cards on the page.
> After these dynamically generated product cards appear, make sure they continue to use the same product-detail behavior created in Problem 3. Every product card, including those added through chat search, should open the detailed single-item page with a large image and complete product information when clicked.
> Update both `prompts/prompt.md` and `output/harness.md` to explain how search results are passed from the agent to the website.

**Follow-up prompt:** None needed.

---

## Problem 8: Customer memory

**Prompt:**

> For logged-in shoppers, store their chat history in an appropriate database table and reload that history when they come back.
> The agent should also know which customer is currently chatting, including the customer's name and email. Pass this information through agent dependencies or another clearly defined approach, and/or provide tools that allow the agent to access it.
> Also provide enough page context for the agent to understand references to the product currently being viewed. For example, if a shopper is on a product page and asks, "Do you have this in pink?", the agent should know which product "this" refers to. One possible approach is to include relevant code or page information in the agent context.
> Guests should still be allowed to use the chat feature, but persistent chat history is only required for logged-in users.
> In `output/harness.md`, explain how chat history is stored, which customer fields are available to the agent, and how page context is passed to it.

**Follow-up prompt:** None needed.

---

## Problem 9: Usability improvements

**Prompt:**

> Here is the Problem 9 prompt. Explain what I need to do and ask me if you need anything.
>
> Once the main shopping experience is working, improve the application by implementing:
>
> - 2 front-end usability improvements
> - 2 agent or backend usability improvements
>
> Front-end improvements should make the site easier to use or improve its visual experience.
> Agent or backend improvements should improve the quality, accuracy, safety, speed, cost efficiency, or usefulness of the agent. These improvements may include new agent tools or backend changes that make the system perform better.
> Create `output/usability.md` before or while implementing these features. For each improvement, explain:
>
> - What you added
> - Why it benefits either a Campus Customs shopper or the business
>
> Make sure every improvement described in the document is actually implemented in the working application, since graders will compare the write-up with the running site.

**Follow-up prompt:**

> Front end: product filters & sorting, and size selection + "ask about this item". Agent/backend: a tool that recommends in-stock alternatives when a size is sold out, and an input safety filter.

What was lacking after the first prompt: it didn't say *which* four improvements to build, so the vibe coder asked me to choose from a list of options.

---

## Problem 10: Style the website

**Prompt:**

> Apply creative styling so the website feels like a polished and realistic Campus Customs storefront. Consider elements such as typography, color, visual hierarchy, motion, product presentation, and the overall chat experience.
> More creative and original design choices may earn additional credit.
> Create `output/design.md` and briefly explain what you changed and why those changes could encourage customers to stay on the site longer and make purchases. Keep the explanation specific and concise.

**Follow-up prompt:** None needed.

---

## Problem 11: Site testing (app check)

**Prompt:**

> Test the working website and document the results in `output/app_check.html`, which should be a standalone page that can be opened directly.
> Include clear screenshots and short captions showing:
>
> - The chat retrieving a product's actual inventory level and price from the database
> - Dynamic product-search cards appearing after a category-based question, such as a request for hoodies
> - One usability improvement implemented in Problem 9
>
> Organize the HTML so it is easy to grade. Each test should have a heading, a screenshot, and one or two sentences explaining what the screenshot demonstrates.
> Store all screenshot files in `output/app_check_images/` and reference them from `app_check.html` using relative paths, such as `app_check_images/inventory.png`.

**Follow-up prompt:** None needed.

---

## Problem 12: Audit trail, safety, finish harness

**Prompt:**

> Maintain an append-only file called `output/audit_trail.json` that records activity from the agent loop. Each entry should include items such as the time, tool name, brief arguments and result, and the reason the loop stopped.
> Do not erase or reset this audit trail between runs.
> Also create appropriate safety rules for the agent and add them to `prompts/prompt.md`.
> Complete `output/harness.md` so that it clearly explains how the entire system works. It should cover:
>
> - The fields defined in `models.py` and the reasoning behind them
> - The available tools and what they can do
> - Safety rules
> - Technical specifications, including loop limits, result limits, model choices, and instructions for running both the front end and backend

**Follow-up prompt:** None needed.

---

## Problem 13: Push to GitHub and submit the URL

**Prompt:**

> Place your project code inside a folder named `hw4` and push it to a public GitHub repository.
> Submit the repository URL on Canvas so graders can open and clone the project. Do not submit a zip file for this assignment.
> Do not commit your actual `.env` file, `campus_customs.db`, or product image files to GitHub. Use `.gitignore` to exclude them. Include a `.env.example` file that contains placeholder values only.
> Use the expected project structure (AI_prompts.md, requirements.txt, .env.example, .gitignore, README.md, frontend/, backend/ with main.py, agent.py, models.py, tools.py, prompts/prompt.md, and output/ with harness.md, design.md, usability.md, app_check.html, app_check_images/, audit_trail.json). Keep the local data package (data/campus_customs.db, data/products/) outside of Git.
> Finally, `README.md` should explain how to run both the front end and backend after the local data package has been placed in the project.

**Follow-up prompt:** None needed.

---

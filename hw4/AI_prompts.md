# AI Prompts Log — MGT409 Homework 4: Campus Customs Shop + Chatbot

Gawon Yi

This file records the prompts I gave my vibe coder, one section per problem.

---

## Problem 1: Vibe coder prompts

**Prompt:**

> Create a file that records the prompts I write, with a separate section for each problem.

**Follow-up prompt:** None needed.

---

## Problem 2: Analyze the database

**Prompt:**

> Open the database, organize the tables and their fields, and analyze why each field is needed. Create a harness.md file.

**Follow-up prompt:** None needed.

---

## Problem 3: Build the Campus Customs website

**Prompt:**

> I'm going to build the website. Use React, Vite, and TypeScript, with five items in the top menu. Write the Home and About pages using yalebulldogblue.com as a reference, but paraphrase it. Build a product image list and product detail pages, and also add a chat window in the bottom-right corner.

**Follow-up prompt:**

> (sent a screenshot of the home page) Is this right? … It's not showing — fix it.

What was lacking after the first prompt: the "Hoodie season" products never loaded because the backend wasn't running/reachable. The fix made `main.py` work on older Python versions and pointed the Vite proxy at `127.0.0.1:8000`, and then I started the backend in its own terminal.

---

## Problem 4: Create account and login

**Prompt:**

> Also implement sign-up and login. Sign-up should have first name, last name, email, and password (plus a password confirmation step), and login should use email and password. Save accounts in a users table. Make sure passwords are stored securely, check that both the test account and a new account work, and add an explanation of authentication to harness.md.

**Follow-up prompt:** None needed.

---

## Problem 5: PydanticAI agent backend

**Prompt:**

> I'm going to implement the agent backend: a PydanticAI agent behind FastAPI, split into four files (prompt.md, agent.py, tools.py, models.py). Connect a chat route, use the Portkey key from the .env file in my codex folder, add the shop's tone and basic safety rules, and describe how everything connects in harness.md.

**Follow-up prompt:** None needed.

---

## Problem 6: Tools: product info and stock

**Prompt:**

> I'm going to build price and stock tools. Look up the description, price, and stock by size from the DB, never make anything up, and say clearly when something is sold out. Update prompt.md, and explain in harness.md why you chose each field.

**Follow-up prompt:** None needed.

---

## Problem 7: Chat search that updates the page

**Prompt:**

> I want chat searches to show products as cards. When someone asks "What hoodies do you have?", the products should appear as cards on the page. Pass them as structured data, make each card open its detail page when clicked, and update the docs.

**Follow-up prompt:** None needed.

---

## Problem 8: Customer memory

**Prompt:**

> Customer memory: save logged-in users' chat history in the DB and load it again when they come back. Let the agent know who is chatting (name and email) and what "this" means on a product page. Guests should still be able to chat. Explain it in harness.md.

**Follow-up prompt:** None needed.

---

## Problem 9: Usability improvements

**Prompt:**

> Usability improvements: two front-end and two backend improvements. Write in usability.md what each one is and why.

**Follow-up prompt:**

> Front end: product filters & sorting, and size selection + "ask about this item". Agent/backend: a tool that recommends in-stock alternatives when a size is sold out, and an input safety filter.

What was lacking after the first prompt: it didn't say *which* four improvements to build, so the vibe coder asked me to choose from a list of options.

---

## Problem 10: Style the website

**Prompt:**

> Design: make it feel like a real campus store (fonts, colors, animation, cards, and the feel of the chat) and make it original. Write design.md.

**Follow-up prompt:** None needed.

---

## Problem 11: Site testing (app check)

**Prompt:**

> App testing: take screenshots of an inventory lookup, the hoodie search cards, and one usability feature, and put them in app_check.html with the images in their own folder linked by relative paths.

**Follow-up prompt:**

> (sent three full-width screenshots of the inventory chat, the hoodie search results, and the filtered Products page) You do it.

What was lacking after the first prompt: the first screenshots were captured at a narrow, phone-sized width, so they were small and hard to read; they were replaced with these full-width desktop screenshots.

---

## Problem 12: Audit trail, safety, finish harness

**Prompt:**

> Audit, safety, and harness: keep adding to a log of agent runs without erasing it (time, tool, result, and why it stopped), add safety rules, and finish harness.md (fields, tools, safety, specs, and how to run it).

**Follow-up prompt:** None needed.

---

## Problem 13: Push to GitHub and submit the URL

**Prompt:**

> GitHub: put the project in an hw4 folder in a public repo, leave out .env, the DB, and the images, include .env.example, and explain how to run it in the README.

**Follow-up prompt:** None needed.

---

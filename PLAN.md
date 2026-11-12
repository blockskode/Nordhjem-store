# Plan: Nordhjem store, an AI store assistant on GCP

Nordhjem is a fictional Scandinavian home and furniture store. This
project builds its website and an AI assistant behind it, on Google
Cloud, in four phases. It doubles as preparation for a JYSK AI
Engineer interview (around 2026-11-17), so every phase is also
learning material.

Confirmed with the owner:
- Goal: build **all four phases**. That is the best way to learn. If
  time runs out before the interview, the later phases continue after
  it; the goal stays.
- One realistic use case, on GCP, with the owner's own Google account
  and billing. Gemini on Vertex AI, not a Claude key.
- Fictional brand "Nordhjem": no JYSK name, logo or look.
- The project runs on **Firebase** (Firebase project `nordhjemstore`;
  web config in `firebase_config.js`).
- **Start from scratch** in this repo: only the generated data was
  brought over (products, test questions, photos). All code is written
  new here.
- Split of work: Claude does setup and plumbing (GCP, data generation,
  images, the web shell). The owner writes the core code (search, RAG,
  agent, GNN) as exercises, with a learn document, a check script and
  a reference solution from Claude.
- Learn material as LaTeX PDFs, precise, every math step shown. A
  running reference PDF (`notes.pdf`) collects concept answers and
  tables.

Marked **hypothesis to confirm** where Claude chose something alone.

## The four phases

| Phase | What the customer gets | Steps |
|---|---|---|
| 1 | The Nordhjem website: type what you want, see products with name, price and photo | 1 |
| 2 | Questions answered with sources, over products and store policies (RAG on Vertex AI) | 2, 3 |
| 3 | A chat assistant (agent) that searches, checks stock and orders, safely; deployed on Cloud Run | 4, 5, 6 |
| 4 | A graph neural network (GNN) model, for example a demand forecast per product, used by the agent as a tool (to be discussed later) | 8 |

Step 7 (interview rehearsal) happens before the interview, wherever
the phases are by then.

## The use case

Customers or store staff ask in plain language:

- "Which mattress is good for back pain, under 3000 kroner?" (product
  search: semantic search plus a price filter)
- "Can I return a bed after 30 days?" (policy question: RAG over
  documents)
- "Is the Viborg 3-seat sofa in stock in the Aarhus store?" (exact
  lookup: a tool that queries a table, not RAG)
- "Where is my order 10234?" (exact lookup plus a privacy check)
- "Is this sofa popular, will it sell out?" (the GNN forecast tool)
- "I want to complain about a broken delivery" (hand-off to a human)

The mix is deliberate: part of the skill is knowing when RAG is the
right tool and when a plain database query or a model is.

## The data (generated, fake)

Fake but realistic data with deliberate traps. The product data and
photos were generated earlier (in another repo) and are kept here in
`data/` as a fixed dataset; the scripts that made them were not
brought over. New data (policies, stock, orders, sales) gets new
generator scripts here.

- **Products** (500, done): name, category, colour, price in DKK,
  language (343 English, 107 Danish, 50 German), description,
  attributes. 8 categories: mattress, sofa, rug, garden, pillow, duvet,
  dining table, office chair. Traps: colour variants, very short
  descriptions, several languages, distractors.
- **Product photos** (125 looks covering the 500 products, done): one
  realistic catalogue photo per look (same category, material and
  colour share a photo).
- **Search test questions** (23, done): each with the relevant product
  IDs and a kind: meaning, language or needs_filter.
- **Policies** (about 20 documents, to do): returns, delivery, warranty,
  "100 night mattress trial", country differences. Traps: a policy
  that changed (old and new version), rules that differ by country.
- **Stores and stock** (about 30 stores, to do).
- **Orders** (a few thousand, with customer email for the privacy
  check, to do).
- **Weekly sales history** (to do, phase 4): see Step 8.
- **Evaluation set** for RAG and the agent: about 50 questions with
  the right answer and the documents that should be found.

## GCP and Firebase facts

Firebase project: `nordhjemstore` (a Firebase project is also a GCP
project). **Confirmed 2026-11-12:** run everything (hosting, Vertex
AI, BigQuery, Firestore, Cloud Run) in `nordhjemstore`, so the app and
its AI live in one project. That needs the Blaze (pay as you go) plan
linked to billing, the APIs below turned on there, and a budget alert.
The earlier project below then stays only as a reference.

**`nordhjemstore`, set up 2026-11-12:**

- Project number 757427498119. Billed to "My Billing Account"
  (01052B-B86D92-F7FC72, DKK); the 5th project on that account.
- Budget alert "Nordhjem store": 200 DKK, emails at 50, 90 and 100
  percent.
- APIs on: Vertex AI, Firestore, Cloud Storage, Cloud Run, Cloud
  Build, Artifact Registry, BigQuery, Discovery Engine (ranking),
  Trace, Logging, Monitoring, Billing Budgets, Firebase Storage,
  Firebase Hosting, Firebase Rules.
- Login: ADC with quota project `nordhjemstore`. The owner's account
  has `roles/owner`, which includes the Vertex AI permissions (adding
  `roles/aiplatform.user` separately was not needed).
- Models checked on this project: `gemini-embedding-001` in
  `europe-west1` works (3072 numbers, length 1.0);
  `gemini-3-flash-preview` in `global` works; `gemini-2.5-flash`
  gives 404. The image model is not checked yet.
- Firestore: database `(default)`, Native mode, `europe-west1`.
- Storage: bucket `nordhjemstore.firebasestorage.app`, `EUROPE-WEST1`.
- Hosting: site `nordhjemstore` (https://nordhjemstore.web.app),
  nothing deployed.
- Security rules: none published yet, so all browser access to
  Firestore and Storage is refused. Rules come before any deploy.

Earlier GCP project (set up 2026-11-10, used for the data):

- Project `jysk-store-assistant-1110`, billed to "My Billing Account"
  (01052B-B86D92-F7FC72, currency DKK).
- Budget alert "JYSK store assistant practice": 200 DKK, emails at 50,
  90 and 100 percent.
- APIs on: Vertex AI, BigQuery, Firestore, Cloud Run, Cloud Build,
  Artifact Registry, Discovery Engine (ranking), Trace, Logging,
  Monitoring, Billing Budgets.
- Login: Application Default Credentials (ADC), no API key.
  `genai.Client(vertexai=True, project=..., location=...)`.
- Models that answer:
  - Embeddings: `gemini-embedding-001` in `europe-west1`. 3072 numbers
    per text by default, already length 1; 768 with
    `output_dimensionality`. Up to 250 texts per call.
  - Text: `gemini-3-flash-preview`, only in location `global`.
  - Images: `gemini-3-pro-image` in `global` (the Imagen models are not
    offered to this project). 4 parallel requests hit the rate limit
    (429); 1 or 2 with retries works.
- Regions: data and embeddings in `europe-west1` (Belgium); Gemini
  through `global`. Interview point: EU data rules may require a
  regional endpoint, and then only the models offered there.

## The steps

Each step has: a learn PDF (the concept from the start, one worked
example, every step shown), code the owner writes, a reference
solution, and a check script.

### Step 1: embeddings and semantic search (phase 1)

Status: done once in the old repo (learn PDF, exercises, check);
redone from scratch here. The search test questions are in
`data/eval/product_queries.json`.

- What an embedding is; cosine similarity, dot product, L2 norm,
  normalising, worked by hand.
- Task types (`RETRIEVAL_QUERY` vs `RETRIEVAL_DOCUMENT`), dimensionality,
  batching, what text to embed.
- Search 500 products with plain NumPy: one matrix product, top 5.
- Measure: hit@5 and precision@5. Reference: meaning questions 1.00 /
  0.99, language 1.00 / 0.96; needs_filter questions fail on purpose
  (Step 3 fixes them).

### Step 2: RAG over policies (phase 2)

- Chunking: by size, by heading, with overlap; see how each choice
  changes what is found.
- The prompt: question, retrieved chunks, instruction to answer only
  from them and cite them.
- Gemini on Vertex AI with structured output (JSON with answer and
  sources).
- Failure cases from the data: the old policy version, the country
  difference, a question with no answer ("I don't know" is right).

### Step 3: a real vector store and better retrieval (phase 2)

- Vectors in **BigQuery** with `VECTOR_SEARCH`; then **Firestore**
  vector search. Pay per query, close to zero cost.
- Vertex AI Vector Search: how approximate nearest neighbour indexes
  work (ScaNN, HNSW), when it is worth it, why it is not left running
  here (it costs money every hour).
- Metadata filters: category, price, colour, "not leather" (fixes the
  needs_filter questions).
- Hybrid search: keyword search (BM25) plus vector search, merged.
- Re-ranking with the Vertex AI ranking API.
- Evaluation before and after each change.

### Step 4: the first agent (phase 3)

- An agent is a model in a loop: choose a tool, read the result,
  decide again. Write the loop by hand first with Gemini function
  calling, so nothing is magic.
- Tools: `search_products`, `search_policies`, `check_stock`
  (BigQuery), `order_status` (needs the customer's email),
  `hand_off_to_human`; later `forecast_demand` (Step 8).
- Good tool descriptions and input checks; what happens when the model
  calls a tool wrongly.
- Then the same agent with Google's **Agent Development Kit (ADK)**,
  and what the framework adds (sessions, memory, events).

### Step 5: making the agent safe and measurable (phase 3)

- Guardrails: no order details without the matching email; no made-up
  prices; refuse off-topic requests.
- Multi-agent: a router to a product, policy or order agent; when this
  is better than one agent and when worse.
- Evaluation: task success, tool-call correctness, model-as-judge,
  ADK's evaluation tools.
- Tracing: every step, tokens and time (Cloud Trace).

### Step 6: production on GCP (phase 3)

- The website and agent as a container on **Cloud Run** (scales to
  zero when unused).
- Alternative: Vertex AI Agent Engine; compare.
- A service account with only the roles it needs.
- Monitoring: latency, errors, cost per question; logs without
  personal data.
- Keeping the index fresh when products change.
- Model Context Protocol (MCP): the stock tool as an MCP server.

### Step 7: interview rehearsal (before the interview)

- Design questions out loud: "Design a customer service assistant for
  JYSK", "Your RAG answers are wrong 20 percent of the time: what do you
  do?", "How do you control the cost of an LLM feature?"
- Walk through this system: diagram, choices, trade-offs, numbers from
  the evaluations.
- Check that nothing on GCP costs money while idle.

### Step 8: GNN demand forecast (phase 4)

**Status: to be discussed later (owner, 2026-11-12).** Everything in
this step is a first idea, not a decision.

The question: **how many units of each product will sell next week?**
For a furniture retailer this decides how much stock to order; too
much ties up money, too little loses sales.

- **Graph.** Nodes are products. Edges join products that change each
  other's sales: complements (a sofa sale lifts rugs and cushions) and
  substitutes (a discounted grey sofa takes sales from the blue one;
  this is called cannibalisation).
- **Node features.** Price, category, colour, on sale or not, sale
  price, week of the year, season, last weeks' sales.
- **Target.** Units sold next week (node regression).
- **Model.** Reuse the architecture from `~/semcon/gnn`
  (`src/models/gnn_base.py`: `MessagePassingLayer(h, edge_index)` in
  plain PyTorch). It already learns "graph state at time t to state at
  t+1" for the heat equation; weekly demand has the same shape.
- **Data.** Generated sales history with known rules: garden furniture
  in summer, duvets in winter, uplift when on sale, complement and
  substitute effects. Because the rules are known, the test is honest:
  does the GNN beat the same model without edges (a per-product
  baseline), and does it learn the cross-product effects?
- **Link to the app.** The agent tool `forecast_demand(product_id)`
  answers "is this sofa popular, will it be in stock?".
- **Hypothesis to confirm:** demand forecasting as the question. The
  alternative is "frequently bought together" (link prediction), which
  fits the shop page but needs a different architecture and uses the
  time features less.

## The website (grows with the phases)

- Phase 1: search box; the results are product cards (photo, name,
  category, colour, price, score). It calls the owner's `search()`;
  until that works it uses the reference solution and says so.
- Phase 2: policy questions get an answer with sources.
- Phase 3: a chat panel runs the owner's agent; deployed on Cloud Run.
- Phase 4: a "popular / may sell out" badge from the forecast.
- Stack, **confirmed 2026-11-12:** the page on **Firebase Hosting**;
  product data in **Firestore** (with its vector search for Step 3);
  photos in **Cloud Storage for Firebase**; the AI parts (search, RAG,
  agent, forecast) as a Python service on **Cloud Run**, reached from
  the page through a Firebase Hosting rewrite (so `/api/...` on the
  same site goes to Cloud Run). **Confirmed 2026-11-12:** the front
  end is written in **React**. **Hypothesis to confirm:** built with
  Vite into static files that Firebase Hosting serves; JavaScript or
  TypeScript still open. **Hypothesis to confirm:** colours
  and look, chosen from rendered options.
- Later option: multimodal embeddings (image and text in one space)
  for "find products like this photo".

## Cost

- Product photos: 125 images with `gemini-3-pro-image` (check the real
  amount in billing).
- Embeddings and Gemini Flash at this size: a few euros in total.
- BigQuery and Firestore: within free tiers at this size.
- Cloud Run: scales to zero; near zero.
- Never leave running: Vertex AI Vector Search endpoints, GPU
  machines, Agent Engine deployments.

## Folder layout (hypothesis to confirm)

```
Nordhjem-store/
  README.md          what the project is
  PLAN.md            this plan
  HANDOFF.md         where work stands
  firebase_config.js Firebase web config
  data/              products, test questions, photos (fixed dataset)
  datagen/           new generators: policies, stock, orders, sales
  web/               the page served by Firebase Hosting
  api/               the Python service on Cloud Run
  steps/
    01_embeddings/   learn.pdf, search.py (owner), solution.py, check.py
    02_rag_policies/
    ...
    08_gnn_demand/
  notes.tex, notes.pdf   running reference notes
```

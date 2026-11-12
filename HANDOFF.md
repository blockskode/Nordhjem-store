# Handoff

Last updated 2026-11-12. A new session starts here: read this file,
then `PLAN.md`, then do **"Start here"** below.

## The project in three lines

Nordhjem is a fictional Scandinavian furniture store. We build its
website and an AI assistant on Firebase and Google Cloud in four
phases (search, RAG, agent, later a GNN). It is also the owner's
preparation for a **JYSK AI Engineer interview around 2026-11-17**;
the owner's weak spots are AI agents and RAG / embeddings / semantic
search, so those come first and as deep as possible.

## Start here (the exact next action)

**Set up the Firebase project `nordhjemstore`.** Claude may do this
(it is plumbing, see "How the owner works"). Steps:

1. Check the gcloud and Firebase CLIs are installed and logged in as
   the owner's Google account (`gcloud auth list`, `firebase login:list`).
   If a login is needed, the owner runs it (suggest `! <command>`).
2. Link billing (Blaze plan): billing account "My Billing Account",
   `01052B-B86D92-F7FC72`, currency DKK. It already holds the earlier
   project `jysk-store-assistant-1110`; a billing account allows about 5
   projects. Ask before linking.
3. Turn on the APIs in `nordhjemstore`: Vertex AI (`aiplatform`),
   Firestore, Cloud Storage, Cloud Run, Cloud Build, Artifact Registry,
   BigQuery, Discovery Engine (ranking), Cloud Trace, Logging,
   Monitoring, Billing Budgets.
4. Budget alert on `nordhjemstore` in DKK (the earlier project used
   200 DKK; ask the owner for the amount), emails at 50, 90, 100 percent.
5. Application Default Credentials: quota project set to
   `nordhjemstore` (`gcloud auth application-default set-quota-project
   nordhjemstore`), and the owner's account has `roles/aiplatform.user`.
6. Prove it works with one embedding call and one Gemini call from
   Python against `nordhjemstore` (models below). Note any model that
   is not available to the new project.
7. Firebase: create Firestore (Native mode, region `europe-west1`),
   Storage, Hosting. Do not deploy anything public yet: security rules
   come first.
8. Update the "GCP and Firebase facts" section of `PLAN.md` with what
   was found, update this file, commit and push.

Then **Phase 1** (`PLAN.md`, Step 1): the store page and product
search. The owner writes the search; Claude writes the learn PDF, the
exercise skeleton, the check script and a reference solution, and
builds the web shell around the owner's code.

## How the owner works (important)

- **The owner writes the core code** (search, RAG, agent, model).
  Claude prepares: a learn PDF, an exercise skeleton with TODOs, a
  check script that tests it, and a reference solution kept separate.
  Setup and plumbing (GCP, Firebase, data generation, the web shell)
  Claude may do, and says that it did. The owner once said "i need to
  practice" when Claude did everything, then "it ok to setup up the
  project. this is the easies part. now let do the real exerice".
- **Teach in depth, never jump.** Build each concept: the problem, the
  idea, one worked example with real numbers, every math step shown
  (definition, substitution, each product, each sum, result), the
  traps, then the exercise. The owner said "be precise", "don't jump"
  when a squaring step was skipped. Verify every number in code before
  it goes into a document.
- **Learn material as LaTeX PDFs**, not markdown (easier to read).
  Built with `tectonic`; earlier style: TeX Gyre Pagella and Heros,
  loaded by file name (`texgyrepagella` with `Extension=.otf`), one teal
  accent `#2A7D78`. Render pages with
  `uv run --with pymupdf` to check them before showing.
- **Tables do not go in the terminal**; wide tables are hard to read
  there. Concept answers with tables go into a running reference PDF
  (`notes.tex` -> `notes.pdf`, to start in this repo), with a short
  chat reply.
- Simple words, short sentences, explain each term where it appears.
  **No em dashes** in anything written for the owner.
- Show visual work (page, colours) before committing; offer at least
  five rendered options for look and colour choices.
- Python: PEP 8, type hints and a docstring on every function, simple
  over clever.
- Commit and push after an approved change; plain
  `git commit -m "message"`, stage specific files.

## What the owner already knows (from Step 1 in the old repo)

The owner did part of Step 1 before the move, in
`/Users/yapi.donatien.achou/practice/jysk-ai-engineer/` (kept only as
a reference; its code is **not** reused, this repo starts from
scratch).

- Understood: embeddings as vectors, dot product, L2 norm (with the
  squaring step), cosine similarity (1 same direction, 0 unrelated,
  -1 opposite), normalising to length 1, the search idea (embed the
  question, compare with every product vector, sort, return the
  closest), ADC vs API key, what Vertex AI is, its mapping to MLflow
  on Databricks.
- Did: Exercise A questions 1 and 2 (one embedding call; the vector
  has 3072 numbers and length about 1). Was at question 3 (batching
  2, 50 and 250 texts per call) and question 4 (timing).
- Not done: Exercise B (writing `search()` and measuring hit@5 and
  precision@5).
- Useful reference files there: `steps/01_embeddings/learn.pdf` (the
  Step 1 learn PDF), `notes.pdf` (GCP basics, ADC, Vertex vs MLflow,
  norms), `steps/01_embeddings/solution.py` (reference search; scored
  meaning 1.00 / 0.99, language 1.00 / 0.96 on hit@5 / precision@5).
  Reuse the PDFs' content where it fits instead of rewriting it.

## What is in this repo

| Path | What |
|---|---|
| `PLAN.md` | the four-phase plan |
| `firebase_config.js` | Firebase web config for project `nordhjemstore` |
| `data/products.jsonl` | 500 products, one JSON object per line |
| `data/eval/product_queries.json` | 23 search test questions with the relevant product IDs |
| `data/images/` | 125 product photos (JPEG, 4:3, max 1200 px), about 34 MB |
| `data/product_images.json` | product ID to photo file name, 500 entries |

Product fields: `product_id` (P1001 to P1500), `name`, `category`
(mattress, sofa, rug, garden, pillow, duvet, dining_table,
office_chair), `colour`, `price_dkk`, `language` (en 343, da 107,
de 50), `description`, `attributes` (depend on the category).
Test question kinds: `meaning`, `language`, `needs_filter` (the last
cannot be answered by embeddings alone, on purpose; Step 3 fixes it
with filters).

## Decisions so far

- Goal: all four phases; if time runs out before the interview,
  continue after it.
- Everything runs in the Firebase project `nordhjemstore`: page on
  Firebase Hosting, products in Firestore, photos in Cloud Storage
  for Firebase, the AI service (Python) on Cloud Run behind a Hosting
  rewrite on `/api/...`.
- Fictional brand Nordhjem; no JYSK name, logo or look.
- Phase 4 (GNN) is to be discussed later. First idea: weekly demand
  forecast reusing `~/semcon/gnn` (`src/models/gnn_base.py`).
- Open: colours and look of the site.

## Things to know

- The data has no generator script here: it is a fixed dataset. Do
  not delete it.
- Vertex AI from Python (package `google-genai`):
  `genai.Client(vertexai=True, project=..., location=...)`. Without
  `vertexai=True` it asks for an API key.
  - Embeddings: `gemini-embedding-001` in `europe-west1`. 3072 numbers
    by default, already length 1; `output_dimensionality=768` for
    shorter vectors. Up to 250 texts per call.
  - Gemini: `gemini-3-flash-preview`, only in location `global`. Older
    names like `gemini-2.5-flash` were not available to a new project.
  - Images: `gemini-3-pro-image` in `global` via `generate_content`
    with `response_modalities=["IMAGE"]`. Imagen models returned 404.
    More than 2 parallel requests gave 429 (rate limit).
  These were found on the old project; recheck on `nordhjemstore`.
- Python environments: make the venv with `uv venv` in this repo. A uv
  venv has no pip; add it with `.venv/bin/python -m ensurepip` if the
  owner wants `pip install`. The owner once had another venv
  (`practice`) active, which gave `cannot import name 'genai'`; check
  with `which python3`.
- Firebase web `apiKey` values identify the project; they are not
  secrets. Protection comes from Firestore and Storage security rules
  (and optionally App Check), written before anything goes public.
- Cost: never leave running Vertex AI Vector Search endpoints, GPU
  machines or Agent Engine deployments.

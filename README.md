# Document Intelligence — On-Prem Demo

Demo implementation of the **On-Premise AI-Powered Document Intelligence & Search System** (Local RAG-Based Knowledge Retrieval Platform) 

## What This Demo Does

- **Document ingestion**: Scans a folder (e.g. `sample_docs/`) for PDF, DOCX, XLSX, PPTX, TXT and extracts text.
- **Local indexing**: Chunks documents and builds semantic embeddings using **sentence-transformers** (runs 100% on your machine).
- **Vector store**: Uses **ChromaDB** on disk — no cloud, no external APIs.
- **RAG API**: Natural-language questions return answers with **source citations** (file path, page/sheet, folder).
- **Optional local LLM**: If [Ollama](https://ollama.ai) is running with a model (e.g. `llama2`), answers are summarized by the model; otherwise the demo returns the retrieved excerpts with citations.
- **Intranet-style portal**: Chat UI with filters (folder, doc type) and “Re-index” for demo use.

## Quick Start

### 1. Create virtual environment and install dependencies

```bash
cd /path/to/Naqi-Demo-project
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the application

From the **project root** (so `backend` is on the path):

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Open the portal (frontend)

**The frontend is served by the same backend.** There is no separate frontend server.

- In your browser open: **http://localhost:8000**
- You get the chat UI (HTML, CSS, JS are served from `/` and `/static/`).
- On first run, the app will index `sample_docs/` automatically. You can also click **Re-index** in the UI.

### 4. Try example queries

- “Show the latest mine safety inspection report for Site A”
- “Find blasting SOPs updated after 2022”
- “What were the key findings in the environmental impact report for Project X?”

## Optional: Local LLM (Ollama)

For AI-summarized answers instead of raw excerpts:

1. Install [Ollama](https://ollama.ai) and run: `ollama run qwen2.5:latest` (or another model).
2. Ensure the app can reach `http://localhost:11434`.  
3. Default model is `qwen2.5:latest`; override via env: `OLLAMA_MODEL=llama2` (or in `backend/config.py`).

If Ollama is not running, the demo still works and returns the retrieved document chunks with sources.

## How to test

### 1. Start the backend

From the project root, with the venv activated:

```bash
cd /home/mehdi/startup/Naqi-Demo-project
source .venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Wait until you see `Application startup complete`. On first run it will index `sample_docs/` (you may see "Loading weights" for the embedding model).

### 2. (Optional) Start Ollama for AI summaries

In another terminal:

```bash
ollama run qwen2.5:latest
```

Leave it running. If you skip this, the app still works and returns retrieved text with sources (no LLM summary).

### 3. Test in the browser

1. Open **http://localhost:8000** in your browser.
2. **Suggestion chips**: Click any of the three example questions (e.g. “Latest mine safety report — Site A”). You should get an answer and a “Cited sources” section.
3. **Type a query**: Use the text box and press Enter (e.g. “What are the blasting procedures?”). Check that the answer and sources appear.
4. **Filters**: Change “Folder” to e.g. **Safety** or **SOPs** and run the same query again; results should be limited to that folder.
5. **Re-index**: Click **Re-index**. After a few seconds it should show “Indexed (N)”. Then ask a question again to confirm search still works.

### 4. Quick API check (optional)

In a terminal:

```bash
# Health
curl -s http://localhost:8000/api/health

# Ask a question (JSON response with answer + sources)
curl -s -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "mine safety inspection Site A"}'
```

You should see `{"status":"ok",...}` for health and a JSON object with `answer`, `sources`, and `used_llm` for the query.

## Project Layout

```
Naqi-Demo-project/
├── backend/
│   ├── main.py       # FastAPI app + API + static serve
│   ├── config.py     # Paths, chunk size, Ollama settings
│   ├── ingest.py     # Document loaders + chunking
│   ├── embed.py      # Embeddings + ChromaDB index
│   └── rag.py        # Retrieve + optional Ollama answer
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── sample_docs/      # Demo documents (Safety, SOPs, Environmental, Operations)
├── data/             # Created at runtime: ChromaDB + uploads
├── requirements.txt
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Intranet portal (chat UI) |
| `/api/query` | POST | Natural language query → answer + sources |
| `/api/search` | GET | Semantic search only (no LLM) |
| `/api/index` | POST | Re-run document ingestion and indexing |
| `/api/filters` | GET | Folder and doc-type options for filters |
| `/api/health` | GET | Health check |

## Security & Compliance (Proposal Alignment)

- **100% on-prem**: No external API calls for embeddings or search; optional Ollama is also local.
- **Data location**: Documents and index stay under `sample_docs/` and `data/` on your machine.
- For production: add RBAC, AD/LDAP, audit logging, and document-level permissions as in the full proposal.

## Prepared For

MOL Group — Enterprise Data, Mining Operations & Knowledge Management Teams  

**Prepared By**: Muhammad Mehdi / Decentrasec

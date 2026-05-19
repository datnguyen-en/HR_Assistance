# UMass HR Assistance MVP

A RAG (Retrieval-Augmented Generation) chatbot that answers questions about UMass HR policies and benefits using scraped web content and PDFs as its knowledge base.

## Architecture Overview

```
Ingestion Pipeline                  Query Pipeline
─────────────────                   ──────────────
Web URLs + PDFs                     User question
     │                                    │
  Scraper / PDFProcessor             Embedder (embed query)
     │                                    │
  Chunker (700 token chunks)         VectorStore (ChromaDB similarity search)
     │                                    │
  Embedder (all-MiniLM-L6-v2)       Retriever (top-k chunks)
     │                                    │
  VectorStore (ChromaDB upsert)      LLMClient (Groq API)
                                          │
                                     Streamlit UI
```

## Key Files

| File | Purpose |
|---|---|
| `config.py` | Loads all config from `.env`; raises `ConfigError` if required vars are missing |
| `models.py` | Shared dataclasses: `Chunk`, `RetrievedChunk`, `Citation`, `LLMResponse`, `IngestionSummary` |
| `ingestion/ingest.py` | Entry point for ingestion pipeline — run with `python ingestion/ingest.py` |
| `ingestion/scraper.py` | Fetches URLs, converts to Markdown, discovers and downloads linked PDFs |
| `ingestion/pdf_processor.py` | Converts PDFs to Markdown via `pymupdf4llm` |
| `ingestion/chunker.py` | Splits Markdown into token-bounded chunks with overlap |
| `ingestion/embedder.py` | Wraps `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dim vectors) |
| `ingestion/vector_store.py` | ChromaDB wrapper — cosine similarity, collection name `hr_docs` |
| `retrieval/retriever.py` | Embeds query, returns top-k `RetrievedChunk` objects |
| `retrieval/llm_client.py` | Calls Groq API (streaming), assembles answer + citations |
| `ui/app.py` | Streamlit chat UI — run with `streamlit run ui/app.py` |

## Configuration (`.env`)

```
GROQ_API_KEY=        # Required — get from console.groq.com
LLM_MODEL=           # Groq model ID (e.g. llama-3.3-70b-versatile)
CHUNK_SIZE=700        # Token size per chunk
OVERLAP_PCT=0.12      # Overlap between chunks
TOP_K=5               # Chunks retrieved per query
RAW_DATA_DIR=data/raw
CHROMA_DIR=data/chroma
SOURCE_URLS=          # Comma-separated UMass HR URLs to scrape
```

**Never commit `.env` to git** — it contains the live API key.

## Running the App

```bash
# 1. Ingest data (scrapes URLs + processes PDFs in data/raw/)
python ingestion/ingest.py

# 2. Start the UI
streamlit run ui/app.py
```

## LLM Provider

- **Provider:** Groq (`groq` Python SDK)
- **Embeddings:** Local `sentence-transformers` — no API call needed
- **Vector store:** ChromaDB (local, persisted to `data/chroma/`)
- The model ID must match Groq's naming exactly (no `provider/model` slash format). Check available models at `console.groq.com` or via:
  ```bash
  curl https://api.groq.com/openai/v1/models -H "Authorization: Bearer $GROQ_API_KEY" | python3 -m json.tool | grep '"id"'
  ```

## Data Flow Details

1. **Ingestion:** `Scraper` fetches each `SOURCE_URL`, extracts clean Markdown, and discovers linked PDFs. All PDFs (discovered + any manually placed in `data/raw/`) are converted by `PDFProcessor`. `Chunker` splits text into ~700-token chunks with 12% overlap. `Embedder` produces 384-dim vectors. `VectorStore` upserts by composite ID `{source_hash}_{chunk_index}`.

2. **Query:** `Retriever` embeds the user question and runs a cosine similarity search. Top-k chunks are passed to `LLMClient`, which builds a grounded prompt and calls Groq. Only HTTP/HTTPS sources are shown as citations (PDF hash filenames are filtered out).

## Dependencies

See `requirements.txt`. Key packages: `groq`, `chromadb`, `sentence-transformers`, `streamlit`, `trafilatura`, `pymupdf4llm`, `tiktoken`.
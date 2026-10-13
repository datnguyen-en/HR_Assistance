# HR RAG 

A Retrieval-Augmented Generation (RAG) chatbot that answers HR-related questions using official UMass HR documentation. Built as a summer intern project.

## How It Works

1. **Ingestion** — Scrapes public UMass HR web pages and processes PDF documents, converts them to Markdown, chunks the text, generates embeddings, and stores everything in a local ChromaDB vector database.
2. **Query** — When you ask a question, it finds the most relevant document chunks using semantic search, then sends them to Google Gemini to generate a grounded answer with source citations.

## Tech Stack

| Component | Technology |
|---|---|
| Web scraping | `requests` + `trafilatura` + `markdownify` |
| PDF processing | `pymupdf4llm` |
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) |
| Vector store | ChromaDB (local persistent) |
| LLM | Google Gemini API |
| UI | Streamlit |

## Project Structure

```
umass-hr-chatbot/
├── ingestion/
│   ├── ingest.py          # Pipeline entry point
│   ├── scraper.py         # Web scraper
│   ├── pdf_processor.py   # PDF → Markdown
│   ├── chunker.py         # Text chunking
│   ├── embedder.py        # Embedding generation
│   └── vector_store.py    # ChromaDB wrapper
├── retrieval/
│   ├── retriever.py       # Semantic search
│   └── llm_client.py      # Gemini API client
├── ui/
│   └── app.py             # Streamlit chatbot UI
├── data/
│   ├── raw/               # Scraped Markdown files
│   └── chroma/            # Vector database
├── config.py              # Config loader
├── models.py              # Shared data models
├── .env.example           # Environment variable template
└── requirements.txt
```

## Installation and Usage

### Prerequisites

Before getting started, make sure you have Python 3, Git, and a Google Gemini API key. You can get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/umass-hr-chatbot.git
cd umass-hr-chatbot
```

### 2. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure API Key

Create a `.env` file:

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
GEMINI_API_KEY=your-gemini-api-key-here
SOURCE_URLS=https://www.umass.edu/hr/
```

### 4. Run the Project

First, process the HR documents:

```bash
python ingestion/ingest.py
```

Then launch the chatbot:

```bash
streamlit run ui/app.py
```

The chatbot will open at `http://localhost:8501`. You can now ask HR-related questions and receive answers with source citations.

## API

The HR RAG chatbot uses the **Google Gemini API** to generate answers based on official UMass HR documentation.

### How It Works

1. The user submits a question through the Streamlit interface.
2. The system retrieves relevant HR documents from ChromaDB.
3. The question and retrieved documents are sent to Gemini.
4. Gemini generates an answer with source citations.

The API is handled in `retrieval/llm_client.py`, while `retrieval/retriever.py` is responsible for document retrieval.

### Example Usage

**Input:** "What benefits are available for UMass employees?"

**Output:** The chatbot generates an answer based on the retrieved HR documents, along with citations to the original sources.

**Note:** The chatbot can only answer based on processed documents, and AI-generated responses may not always be accurate.

## Adding PDF Documents

Drop any HR PDF files into `data/raw/` before running the ingestion pipeline. They will be automatically processed alongside the scraped web pages.

## Configuration Options

All settings are controlled via `.env`:

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(required)* | Google Gemini API key |
| `LLM_MODEL` | `gemini-1.5-flash` | Gemini model name |
| `SOURCE_URLS` | *(required)* | Comma-separated URLs to scrape |
| `CHUNK_SIZE` | `700` | Tokens per chunk |
| `OVERLAP_PCT` | `0.12` | Overlap between chunks (12%) |
| `TOP_K` | `5` | Number of chunks retrieved per query |
| `RAW_DATA_DIR` | `data/raw` | Directory for raw Markdown files |
| `CHROMA_DIR` | `data/chroma` | Directory for vector database |

## Future Migration to AWS

The local stack maps cleanly to AWS services when ready to scale:

| Local | AWS |
|---|---|
| Local folder | S3 |
| ChromaDB | pgvector on Aurora |
| Python script | Lambda |
| Gemini API | Amazon Bedrock |
| Local machine | EC2 / ECS |

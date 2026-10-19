# HR Assistance

An AI Assistance for people who want to find answers to HR questions using official UMass documentation.

## Table of Contents

- [Install](#install)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Adding PDF Documents](#adding-pdf-documents)
- [Configuration](#configuration)
- [Known Limitations](#known-limitations)
- [API](#api)
- [Maintainers](#maintainers)
- [Credits](#credits)

## Install

### Dependencies

You will need:

- Python 3 and `pip` (`python3 --version` and `python3 -m pip --version` to check)
- Git (`git --version` to check)
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Get the project

```bash
git clone https://github.com/YOUR-USERNAME/umass-hr-chatbot.git
cd umass-hr-chatbot
```

> Replace `YOUR-USERNAME` with the repository owner's actual GitHub username.

### 2. Install the Python dependencies

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

On Windows, activate the environment with `venv\Scripts\activate` instead.

### 3. Configure the project

Copy the example environment file:

```bash
cp .env.example .env
```

Then add your own key and source URL to `.env`:

```dotenv
GEMINI_API_KEY=your-gemini-api-key-here
SOURCE_URLS=https://www.umass.edu/hr/
```

Do not commit your `.env` file or API key to GitHub.

### 4. Verify the installation

Check that the required packages can be imported:

```bash
python3 -c "import chromadb, streamlit, sentence_transformers; print('Dependencies installed')"
```

Expected output if those imports succeed:

```text
Dependencies installed
```

This checks the Python environment; it does **not** confirm that Gemini credentials or HR document ingestion are working.

## Usage

### CLI

**1. Process the HR documents**

Run the ingestion script to collect and process source documents:

```bash
python3 ingestion/ingest.py
```

The pipeline processes configured HR sources and stores searchable document embeddings in the local vector database. Check `data/chroma/` for database files after the script finishes. The exact terminal messages depend on the implementation.

**2. Start the chatbot**

```bash
streamlit run ui/app.py
```

Streamlit normally displays a local URL similar to:

```text
Local URL: http://localhost:8501
```

Open the URL in your browser to use the chatbot.

**3. Ask a question**

For example, enter:

```text
What benefits are available for UMass employees?
```

The chatbot searches the ingested documents and generates an answer using the relevant information. When available, it also includes source citations so you can review the original HR documentation. The exact response depends on the documents in the database.

**4. If something goes wrong**

If the app cannot answer questions because the vector database is empty, run the ingestion script before starting the chatbot:

```bash
python3 ingestion/ingest.py
streamlit run ui/app.py
```

If Gemini authentication fails, check that `GEMINI_API_KEY` in `.env` is set to your real key, then restart the app. **Before submitting:** replace these general troubleshooting descriptions with one actual error message produced by your program and the command that causes it, as the assignment requires.

## How It Works

1. **Ingestion:** The system collects HR web pages and PDF documents, converts their content to Markdown, divides the text into chunks, and creates embeddings.
2. **Retrieval:** When someone asks a question, ChromaDB searches for relevant document chunks using semantic similarity.
3. **Response:** The retrieved content is sent to Google Gemini to generate an answer grounded in the source documents, with citations where available.

## Tech Stack

| Component | Technology |
| --- | --- |
| Web scraping | `requests`, `trafilatura`, `markdownify` |
| PDF processing | `pymupdf4llm` |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) |
| Vector database | ChromaDB (local) |
| Language model | Google Gemini API |
| User interface | Streamlit |

## Project Structure

```text
umass-hr-chatbot/
├── ingestion/
│   ├── ingest.py          # Runs the ingestion pipeline
│   ├── scraper.py         # Collects HR web pages
│   ├── pdf_processor.py   # Converts PDFs to Markdown
│   ├── chunker.py         # Splits text into chunks
│   ├── embedder.py        # Creates embeddings
│   └── vector_store.py    # Stores data in ChromaDB
├── retrieval/
│   ├── retriever.py       # Finds relevant documents
│   └── llm_client.py      # Communicates with Gemini
├── ui/
│   └── app.py             # Streamlit chatbot interface
├── data/
│   ├── raw/               # Source documents
│   └── chroma/            # Local vector database
├── config.py              # Reads configuration
├── models.py              # Shared data models
├── .env.example           # Environment variable template
├── requirements.txt       # Python dependencies
└── README.md
```

## Adding PDF Documents

Place HR PDF files in `data/raw/` before running the ingestion pipeline:

```bash
python3 ingestion/ingest.py
```

## Configuration

Settings are stored in `.env`.

| Variable | Default | Description |
| --- | --- | --- |
| `GEMINI_API_KEY` | Required | Google Gemini API key |
| `LLM_MODEL` | `gemini-1.5-flash` | Gemini model name |
| `SOURCE_URLS` | Required | Comma-separated HR URLs |
| `CHUNK_SIZE` | `700` | Tokens per text chunk |
| `OVERLAP_PCT` | `0.12` | Overlap between chunks |
| `TOP_K` | `5` | Number of retrieved chunks |
| `RAW_DATA_DIR` | `data/raw` | Folder for source files |
| `CHROMA_DIR` | `data/chroma` | Local vector database folder |


## Known Limitations

- The chatbot can only search documents that have already been processed by the ingestion pipeline.
- If a source page changes, the locally stored content may be outdated until ingestion runs again.
- AI-generated responses may be inaccurate. Check the original HR documents before making important decisions.

## API

The project uses Python modules to process HR documents, find relevant information, and generate answers to user questions. Developers can use these modules to understand how the chatbot works and add new features to the project.

### Python Module Reference

| Module | Purpose | Public API to document |
| --- | --- | --- |
| `ingestion/scraper.py` | Collect HR website content | Function that accepts source URLs and returns collected content |
| `ingestion/pdf_processor.py` | Read HR PDF content | Function that accepts a PDF path and returns processed text |
| `ingestion/chunker.py` | Divide documents into text chunks | Function that accepts text and chunk settings and returns chunks |
| `ingestion/embedder.py` | Convert text to embeddings | Function that accepts text chunks and returns embeddings |
| `ingestion/vector_store.py` | Store and query embeddings | Public storage and search methods |
| `retrieval/retriever.py` | Retrieve relevant document chunks | Function or class used to search the database |
| `retrieval/llm_client.py` | Generate an answer with Gemini | Public function or class used to generate responses |

### Public Functions and Examples — Complete from Source

Use a reference entry in this format, replacing the placeholders with the real implementation:

```text
### `actual_function_name(parameter_name)`

What the function does.

- `parameter_name` (type): What the caller provides.
- Returns: Return type and meaning.
- Raises: Actual exceptions and when they occur.
```

### `LLMClient(model, api_key).generate(query, context_chunks)`

Returns an `LLMResponse` (`answer`, `citations`). Raises `LLMError` if the LLM call fails.

## Maintainers

- **[Eric Nguyen](https://github.com/datnguyen-en)** — Vibe Coder 

## Credits

- [UMass Human Resources](https://www.umass.edu/hr/) — HR documentation used as a source of information.
- [Google AI Studio](https://aistudio.google.com/) — Gemini API documentation and key setup.
- Adi and Adhya — Peer review feedback for my README :D.

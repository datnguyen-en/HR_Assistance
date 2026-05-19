"""
Streamlit UI for the UMass HR RAG Chatbot.
Run with: streamlit run ui/app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from config import load_config, ConfigError
from ingestion.embedder import Embedder
from ingestion.vector_store import VectorStore
from retrieval.retriever import Retriever
from retrieval.llm_client import LLMClient, LLMError


def _render_passages(passages: list) -> None:
    if not passages:
        return
    with st.expander(f"Relevant passages retrieved ({len(passages)})"):
        for i, passage in enumerate(passages, 1):
            source = passage.metadata.source_url or passage.metadata.source_filename or "Unknown source"
            score_pct = int(passage.similarity_score * 100)
            if passage.metadata.source_url:
                st.markdown(f"**Passage {i}** &nbsp;·&nbsp; {score_pct}% match &nbsp;·&nbsp; [{source}]({source})")
            else:
                st.markdown(f"**Passage {i}** &nbsp;·&nbsp; {score_pct}% match &nbsp;·&nbsp; {source}")
            st.text(passage.text)
            if i < len(passages):
                st.divider()


@st.cache_resource(show_spinner=False)
def load_components(_cache_key: str = "groq-v1"):
    cfg = load_config()
    embedder = Embedder()
    vector_store = VectorStore(persist_directory=cfg.chroma_dir)
    retriever = Retriever(embedder=embedder, vector_store=vector_store, k=cfg.top_k)
    llm_client = LLMClient(model=cfg.llm_model, api_key=cfg.groq_api_key)
    return retriever, llm_client, vector_store


def main():
    st.title("UMass HR Assistant")
    st.caption("Ask any question about UMass HR policies and benefits.")

    try:
        retriever, llm_client, vector_store = load_components("groq-v1")
    except ConfigError as e:
        st.error(f"Configuration error: {e}")
        st.stop()

    # Session state for conversation history and most recent passages
    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_passages" not in st.session_state:
        st.session_state.last_passages = []

    # Display conversation history
    for i, entry in enumerate(st.session_state.history):
        with st.chat_message("user"):
            st.write(entry["question"])
        with st.chat_message("assistant"):
            st.write(entry["answer"])
            if entry.get("citations"):
                st.markdown("**Sources:**")
                for c in entry["citations"]:
                    st.markdown(f"- [{c.title}]({c.source})")
            if i == len(st.session_state.history) - 1:
                _render_passages(st.session_state.last_passages)

    # Input
    question = st.chat_input("Ask an HR question...")

    if question:
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching HR documents..."):
                try:
                    chunks = retriever.retrieve(question)

                    if not chunks:
                        st.info("No documents have been ingested yet. Run `python ingestion/ingest.py` first.")
                        st.stop()

                    response = llm_client.generate(question, chunks)
                    st.write(response.answer)

                    # Show only web URL sources (skip hashed PDF filenames)
                    web_citations = [c for c in response.citations if c.source.startswith("http")]
                    if web_citations:
                        st.markdown("**Sources:**")
                        for c in web_citations:
                            st.markdown(f"- [{c.title}]({c.source})")

                    st.session_state.last_passages = chunks
                    _render_passages(chunks)

                    st.session_state.history.append({
                        "question": question,
                        "answer": response.answer,
                        "citations": web_citations,
                    })

                except LLMError as e:
                    st.error(f"Could not generate an answer: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()

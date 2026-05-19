"""
Ingestion Pipeline entry point.
Usage: python ingestion/ingest.py
"""
import logging
import sys
import time
from pathlib import Path

MAX_CHILDREN_PER_SEED = 100
CHILD_REQUEST_DELAY_SECONDS = 0.3

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from models import IngestionSummary

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(self):
        self.config = load_config()

    def run(self) -> IngestionSummary:
        """
        Execute: scrape URLs → process PDFs → chunk → embed → upsert.
        Logs per-document failures and continues.
        Returns IngestionSummary.
        """
        from ingestion.scraper import Scraper, ScraperError
        from ingestion.pdf_processor import PDFProcessor
        from ingestion.chunker import Chunker
        from ingestion.embedder import Embedder
        from ingestion.vector_store import VectorStore

        cfg = self.config
        scraper = Scraper(raw_data_dir=cfg.raw_data_dir)
        pdf_processor = PDFProcessor(raw_data_dir=cfg.raw_data_dir)
        chunker = Chunker(chunk_size=cfg.chunk_size, overlap_pct=cfg.overlap_pct)
        embedder = Embedder()
        vector_store = VectorStore(persist_directory=cfg.chroma_dir)

        all_chunks = []
        docs_processed = 0
        failures = []
        discovered_pdfs: dict[str, Path] = {}  # pdf_url → local path, to avoid duplicates
        visited: set[str] = {u.rstrip("/") for u in cfg.source_urls}

        # Scrape web URLs and discover PDFs linked from each page
        for url in cfg.source_urls:
            try:
                result = scraper.fetch_and_convert(url)
                if result is None:
                    failures.append(url)
                    continue
                markdown, metadata, html = result
                scraper.save(markdown, metadata)
                chunks = chunker.chunk(markdown, metadata)
                all_chunks.extend(chunks)
                docs_processed += 1
                logger.info("Scraped and chunked: %s (%d chunks)", url, len(chunks))

                # Discover and download PDFs linked from this page
                pdf_links = scraper.find_pdf_links(url, html)
                if pdf_links:
                    logger.info("Found %d PDF link(s) on %s", len(pdf_links), url)
                for pdf_url in pdf_links:
                    if pdf_url not in discovered_pdfs:
                        pdf_path = scraper.download_pdf(pdf_url)
                        if pdf_path:
                            discovered_pdfs[pdf_url] = pdf_path

                # 1-hop: process child pages under the same path prefix
                child_urls = scraper.find_internal_links(url, html)[:MAX_CHILDREN_PER_SEED]
                if child_urls:
                    logger.info("Found %d child page(s) under %s", len(child_urls), url)
                for child_url in child_urls:
                    if child_url in visited:
                        continue
                    visited.add(child_url)
                    time.sleep(CHILD_REQUEST_DELAY_SECONDS)
                    try:
                        child_result = scraper.fetch_and_convert(child_url)
                        if child_result is None:
                            failures.append(child_url)
                            continue
                        c_md, c_meta, c_html = child_result
                        scraper.save(c_md, c_meta)
                        c_chunks = chunker.chunk(c_md, c_meta)
                        all_chunks.extend(c_chunks)
                        docs_processed += 1
                        logger.info("Scraped child: %s (%d chunks)", child_url, len(c_chunks))
                        for pdf_url in scraper.find_pdf_links(child_url, c_html):
                            if pdf_url not in discovered_pdfs:
                                pdf_path = scraper.download_pdf(pdf_url)
                                if pdf_path:
                                    discovered_pdfs[pdf_url] = pdf_path
                    except ScraperError as e:
                        logger.error("Scraper error for child %s: %s", child_url, e)
                        failures.append(child_url)
                    except Exception as e:
                        logger.error("Unexpected error for child %s: %s", child_url, e)
                        failures.append(child_url)

            except ScraperError as e:
                logger.error("Scraper error for %s: %s", url, e)
                failures.append(url)
            except Exception as e:
                logger.error("Unexpected error for %s: %s", url, e)
                failures.append(url)

        # Process PDFs: both discovered from web pages and any manually placed in data/raw/
        pdf_paths_to_process = set(discovered_pdfs.values())
        for pdf_path in Path(cfg.raw_data_dir).glob("*.pdf"):
            pdf_paths_to_process.add(pdf_path)

        for pdf_path in pdf_paths_to_process:
            try:
                result = pdf_processor.process(pdf_path)
                if result is None:
                    failures.append(str(pdf_path))
                    continue
                markdown, metadata = result
                pdf_processor.save(markdown, metadata)
                chunks = chunker.chunk(markdown, metadata)
                all_chunks.extend(chunks)
                docs_processed += 1
                logger.info("Processed PDF: %s (%d chunks)", pdf_path.name, len(chunks))
            except Exception as e:
                logger.error("Error processing PDF %s: %s", pdf_path, e)
                failures.append(str(pdf_path))

        # Embed and upsert
        chunks_stored = 0
        if all_chunks:
            logger.info("Embedding %d chunks...", len(all_chunks))
            texts = [c.text for c in all_chunks]
            embeddings = embedder.embed_batch(texts)
            vector_store.upsert(all_chunks, embeddings)
            chunks_stored = len(all_chunks)

        return IngestionSummary(
            documents_processed=docs_processed,
            chunks_stored=chunks_stored,
            failures=failures,
        )


if __name__ == "__main__":
    pipeline = IngestionPipeline()
    summary = pipeline.run()
    logger.info(
        "Ingestion complete: %d documents processed, %d chunks stored, %d failures.",
        summary.documents_processed,
        summary.chunks_stored,
        len(summary.failures),
    )
    if summary.failures:
        logger.warning("Failed sources: %s", summary.failures)

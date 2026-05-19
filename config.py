"""
Reads all runtime configuration from environment variables / .env file.
Call load_config() at startup; raises ConfigError if required params are missing.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path


class ConfigError(Exception):
    pass


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ConfigError(f"Required configuration parameter '{key}' is missing. "
                          f"Set it in your .env file or environment.")
    return value


def _optional(key: str, default: str) -> str:
    return os.getenv(key, default)


def _load_source_urls(path: str) -> list[str]:
    """Read URLs from a file, one per line. Blank lines and lines starting with # are ignored.
    Also accepts a comma-separated SOURCE_URLS env var, appended after file contents."""
    urls: list[str] = []
    p = Path(path)
    if p.is_file():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    env_urls = os.getenv("SOURCE_URLS", "")
    urls.extend(u.strip() for u in env_urls.split(",") if u.strip())
    # De-duplicate while preserving order
    seen: set[str] = set()
    return [u for u in urls if not (u in seen or seen.add(u))]


@dataclass
class Config:
    # LLM
    llm_model: str
    groq_api_key: str

    # Chunking
    chunk_size: int
    overlap_pct: float

    # Retrieval
    top_k: int

    # Paths
    raw_data_dir: str
    chroma_dir: str

    # Sources
    source_urls: list[str] = field(default_factory=list)


def load_config() -> Config:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    llm_model = _optional("LLM_MODEL", "qwen/qwen3-32b")
    groq_api_key = os.getenv("GROQ_API_KEY", "")

    if not groq_api_key:
        raise ConfigError(
            "Required configuration parameter 'GROQ_API_KEY' is missing. "
            "Set it in your .env file or environment."
        )

    source_urls = _load_source_urls(_optional("SOURCES_FILE", "sources.txt"))

    return Config(
        llm_model=llm_model,
        groq_api_key=groq_api_key,
        chunk_size=int(_optional("CHUNK_SIZE", "700")),
        overlap_pct=float(_optional("OVERLAP_PCT", "0.12")),
        top_k=int(_optional("TOP_K", "5")),
        raw_data_dir=_optional("RAW_DATA_DIR", "data/raw"),
        chroma_dir=_optional("CHROMA_DIR", "data/chroma"),
        source_urls=source_urls,
    )

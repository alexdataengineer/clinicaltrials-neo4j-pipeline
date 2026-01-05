"""Configuration management for the pipeline"""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Pipeline configuration loaded from environment variables."""

    # Neo4j Configuration
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")

    # AACT Data Source
    AACT_DOWNLOAD_URL: str = os.getenv(
        "AACT_DOWNLOAD_URL",
        "https://aact.ctti-clinicaltrials.org/pipe_delimited_files",
    )
    AACT_DATA_DIR: Path = Path(os.getenv("AACT_DATA_DIR", "data/raw"))

    # Pipeline Configuration
    MIN_STUDIES: int = int(os.getenv("MIN_STUDIES", "500"))
    PHASES: List[str] = [
        p.strip()
        for p in os.getenv(
            "PHASES", "Phase 1,Phase 2,Phase 3,Phase 4,Not Applicable"
        ).split(",")
    ]
    STATUS_LIST: List[str] = [
        s.strip()
        for s in os.getenv(
            "STATUS_LIST",
            "RECRUITING,ACTIVE_NOT_RECRUITING,COMPLETED,ENROLLING_BY_INVITATION",
        ).split(",")
    ]
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "1000"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Path = Path(os.getenv("LOG_FILE", "logs/pipeline.log"))

    @classmethod
    def validate(cls) -> None:
        """Validate configuration values."""
        if cls.MIN_STUDIES < 1:
            raise ValueError("MIN_STUDIES must be >= 1")
        if cls.BATCH_SIZE < 1:
            raise ValueError("BATCH_SIZE must be >= 1")
        if not cls.NEO4J_URI:
            raise ValueError("NEO4J_URI must be set")


"""Standalone script to set up Neo4j schema (constraints and indexes)"""

import sys
from pathlib import Path

from neo4j import GraphDatabase

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.config import Config
from src.pipeline.cypher import CREATE_CONSTRAINTS, CREATE_INDEXES
from src.utils.logging import setup_logging

logger = setup_logging()


def main():
    """Set up Neo4j schema."""
    config = Config()
    config.validate()

    logger.info("Setting up Neo4j schema")

    try:
        driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD),
        )

        with driver.session() as session:
            # Create constraints
            logger.info("Creating constraints...")
            for constraint_query in CREATE_CONSTRAINTS.strip().split(";"):
                if constraint_query.strip():
                    try:
                        session.run(constraint_query)
                        logger.info(f"Created constraint: {constraint_query[:50]}...")
                    except Exception as e:
                        logger.warning(f"Constraint may already exist: {e}")

            # Create indexes
            logger.info("Creating indexes...")
            for index_query in CREATE_INDEXES.strip().split(";"):
                if index_query.strip():
                    try:
                        session.run(index_query)
                        logger.info(f"Created index: {index_query[:50]}...")
                    except Exception as e:
                        logger.warning(f"Index may already exist: {e}")

        driver.close()
        logger.info("Schema setup complete")

    except Exception as e:
        logger.error(f"Failed to set up schema: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


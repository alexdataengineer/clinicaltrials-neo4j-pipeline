"""Neo4j data loading"""

from typing import Dict, List

import pandas as pd
from neo4j import GraphDatabase

from src.pipeline.config import Config
from src.pipeline.cypher import (
    CREATE_CONSTRAINTS,
    CREATE_INDEXES,
    LOAD_COLLABORATES_WITH_BATCH,
    LOAD_DRUGS_BATCH,
    LOAD_ORGANIZATIONS_BATCH,
    LOAD_SPONSORED_BY_BATCH,
    LOAD_TESTS_DRUG_BATCH,
    LOAD_TRIALS_BATCH,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class Neo4jLoader:
    """Handles loading data into Neo4j."""

    def __init__(self, config: Config):
        self.config = config
        self.driver = None

    def connect(self):
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                self.config.NEO4J_URI,
                auth=(self.config.NEO4J_USER, self.config.NEO4J_PASSWORD),
            )
            # Verify connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"Connected to Neo4j at {self.config.NEO4J_URI}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")

    def setup_schema(self):
        """Create constraints and indexes."""
        logger.info("Setting up Neo4j schema (constraints and indexes)")

        with self.driver.session() as session:
            # Create constraints
            for constraint_query in CREATE_CONSTRAINTS.strip().split(";"):
                if constraint_query.strip():
                    try:
                        session.run(constraint_query)
                    except Exception as e:
                        # Constraint might already exist
                        logger.debug(f"Constraint creation (may already exist): {e}")

            # Create indexes
            for index_query in CREATE_INDEXES.strip().split(";"):
                if index_query.strip():
                    try:
                        session.run(index_query)
                    except Exception as e:
                        # Index might already exist
                        logger.debug(f"Index creation (may already exist): {e}")

        logger.info("Schema setup complete")

    def load_trials(self, trials_df: pd.DataFrame):
        """Load trials into Neo4j in batches."""
        logger.info(f"Loading {len(trials_df)} trials")

        # Convert DataFrame to list of dicts, handling NaN
        trials = trials_df.replace({pd.NA: None, pd.NaT: None}).to_dict("records")

        batch_size = self.config.BATCH_SIZE
        total_batches = (len(trials) + batch_size - 1) // batch_size

        with self.driver.session() as session:
            for i in range(0, len(trials), batch_size):
                batch = trials[i : i + batch_size]
                batch_num = (i // batch_size) + 1

                try:
                    session.run(LOAD_TRIALS_BATCH, trials=batch)
                    logger.info(
                        f"Loaded trial batch {batch_num}/{total_batches} ({len(batch)} trials)"
                    )
                except Exception as e:
                    logger.error(f"Failed to load trial batch {batch_num}: {e}")
                    raise

        logger.info("Trials loading complete")

    def load_organizations(self, organizations_df: pd.DataFrame):
        """Load organizations into Neo4j in batches."""
        logger.info(f"Loading {len(organizations_df)} organizations")

        organizations = (
            organizations_df.replace({pd.NA: None, pd.NaT: None})
            .to_dict("records")
        )

        batch_size = self.config.BATCH_SIZE
        total_batches = (len(organizations) + batch_size - 1) // batch_size

        with self.driver.session() as session:
            for i in range(0, len(organizations), batch_size):
                batch = organizations[i : i + batch_size]
                batch_num = (i // batch_size) + 1

                try:
                    session.run(LOAD_ORGANIZATIONS_BATCH, organizations=batch)
                    logger.info(
                        f"Loaded organization batch {batch_num}/{total_batches} ({len(batch)} orgs)"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to load organization batch {batch_num}: {e}"
                    )
                    raise

        logger.info("Organizations loading complete")

    def load_drugs(self, drugs_df: pd.DataFrame):
        """Load drugs into Neo4j in batches."""
        logger.info(f"Loading {len(drugs_df)} drugs")

        drugs = drugs_df.replace({pd.NA: None, pd.NaT: None}).to_dict("records")

        batch_size = self.config.BATCH_SIZE
        total_batches = (len(drugs) + batch_size - 1) // batch_size

        with self.driver.session() as session:
            for i in range(0, len(drugs), batch_size):
                batch = drugs[i : i + batch_size]
                batch_num = (i // batch_size) + 1

                try:
                    session.run(LOAD_DRUGS_BATCH, drugs=batch)
                    logger.info(
                        f"Loaded drug batch {batch_num}/{total_batches} ({len(batch)} drugs)"
                    )
                except Exception as e:
                    logger.error(f"Failed to load drug batch {batch_num}: {e}")
                    raise

        logger.info("Drugs loading complete")

    def load_trial_org_edges(self, edges_df: pd.DataFrame):
        """Load trial-organization relationships in batches."""
        logger.info(f"Loading {len(edges_df)} trial-organization edges")

        # Split by relationship type
        sponsored_by = edges_df[edges_df["rel_type"] == "SPONSORED_BY"]
        collaborates_with = edges_df[edges_df["rel_type"] == "COLLABORATES_WITH"]

        batch_size = self.config.BATCH_SIZE

        with self.driver.session() as session:
            # Load SPONSORED_BY edges
            if len(sponsored_by) > 0:
                edges = sponsored_by[["nct_id", "org_id"]].to_dict("records")
                total_batches = (len(edges) + batch_size - 1) // batch_size

                for i in range(0, len(edges), batch_size):
                    batch = edges[i : i + batch_size]
                    batch_num = (i // batch_size) + 1

                    try:
                        session.run(LOAD_SPONSORED_BY_BATCH, edges=batch)
                        logger.info(
                            f"Loaded SPONSORED_BY batch {batch_num}/{total_batches}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to load SPONSORED_BY batch {batch_num}: {e}"
                        )
                        raise

            # Load COLLABORATES_WITH edges
            if len(collaborates_with) > 0:
                edges = collaborates_with[["nct_id", "org_id"]].to_dict("records")
                total_batches = (len(edges) + batch_size - 1) // batch_size

                for i in range(0, len(edges), batch_size):
                    batch = edges[i : i + batch_size]
                    batch_num = (i // batch_size) + 1

                    try:
                        session.run(LOAD_COLLABORATES_WITH_BATCH, edges=batch)
                        logger.info(
                            f"Loaded COLLABORATES_WITH batch {batch_num}/{total_batches}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to load COLLABORATES_WITH batch {batch_num}: {e}"
                        )
                        raise

        logger.info("Trial-organization edges loading complete")

    def load_trial_drug_edges(self, edges_df: pd.DataFrame):
        """Load trial-drug relationships in batches."""
        logger.info(f"Loading {len(edges_df)} trial-drug edges")

        edges = edges_df[["nct_id", "drug_id"]].to_dict("records")

        batch_size = self.config.BATCH_SIZE
        total_batches = (len(edges) + batch_size - 1) // batch_size

        with self.driver.session() as session:
            for i in range(0, len(edges), batch_size):
                batch = edges[i : i + batch_size]
                batch_num = (i // batch_size) + 1

                try:
                    session.run(LOAD_TESTS_DRUG_BATCH, edges=batch)
                    logger.info(
                        f"Loaded trial-drug batch {batch_num}/{total_batches}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to load trial-drug batch {batch_num}: {e}"
                    )
                    raise

        logger.info("Trial-drug edges loading complete")

    def load(self, transformed_data: Dict[str, pd.DataFrame]):
        """Complete loading pipeline."""
        logger.info("Starting Neo4j data loading")

        try:
            self.connect()
            self.setup_schema()

            # Load nodes first
            self.load_trials(transformed_data["trials"])
            self.load_organizations(transformed_data["organizations"])
            self.load_drugs(transformed_data["drugs"])

            # Then load relationships
            self.load_trial_org_edges(transformed_data["trial_org_edges"])
            self.load_trial_drug_edges(transformed_data["trial_drug_edges"])

            logger.info("Neo4j loading complete")

        finally:
            self.close()


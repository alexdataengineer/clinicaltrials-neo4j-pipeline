"""Main pipeline entrypoint"""

import sys
from pathlib import Path

from src.pipeline.config import Config
from src.pipeline.ingest import AACTIngester
from src.pipeline.load import Neo4jLoader
from src.pipeline.transform import Transformer
from src.utils.logging import setup_logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def main():
    """Run the complete pipeline: ingest -> transform -> load."""
    # Load configuration
    config = Config()
    config.validate()

    # Setup logging
    logger = setup_logging(
        level=config.LOG_LEVEL,
        log_file=config.LOG_FILE,
    )

    logger.info("=" * 80)
    logger.info("ClinicalTrials.gov → Neo4j Knowledge Graph Pipeline")
    logger.info("=" * 80)

    try:
        # Step 1: Ingest
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: DATA INGESTION")
        logger.info("=" * 80)
        ingester = AACTIngester(config)
        raw_data = ingester.ingest()

        # Step 2: Transform
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: DATA TRANSFORMATION")
        logger.info("=" * 80)
        transformer = Transformer()
        transformed_data = transformer.transform(raw_data)

        # Step 3: Load
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: NEO4J LOADING")
        logger.info("=" * 80)
        loader = Neo4jLoader(config)
        loader.load(transformed_data)

        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Trials loaded: {transformed_data['metrics']['trials']}")
        logger.info(
            f"Organizations loaded: {transformed_data['metrics']['organizations']}"
        )
        logger.info(f"Drugs loaded: {transformed_data['metrics']['drugs']}")
        logger.info(
            f"Trial-Org edges: {transformed_data['metrics']['trial_org_edges']}"
        )
        logger.info(
            f"Trial-Drug edges: {transformed_data['metrics']['trial_drug_edges']}"
        )
        logger.info(
            f"Trials with route: {transformed_data['metrics']['trials_with_route']} "
            f"({transformed_data['metrics']['pct_trials_with_route']:.1f}%)"
        )
        logger.info(
            f"Trials with dosage form: {transformed_data['metrics']['trials_with_dosage_form']} "
            f"({transformed_data['metrics']['pct_trials_with_dosage_form']:.1f}%)"
        )

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()


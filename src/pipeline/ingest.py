"""Data ingestion from AACT ClinicalTrials.gov database"""

import zipfile
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests
from tqdm import tqdm

from src.pipeline.config import Config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AACTIngester:
    """Handles downloading and extracting AACT data."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.data_dir = Path(self.config.AACT_DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_aact_data(self, force: bool = False) -> Path:
        """
        Download the latest AACT pipe-delimited dataset.

        Note: AACT provides pipe-delimited files via direct download.
        The URL should point to the zip file directly.

        Args:
            force: If True, re-download even if file exists

        Returns:
            Path to downloaded zip file
        """
        zip_path = self.data_dir / "aact_pipe_delimited.zip"

        if zip_path.exists() and not force:
            logger.info(f"Using existing AACT data: {zip_path}")
            return zip_path

        # AACT typically provides a direct download link
        # If the URL doesn't work, users can manually download from:
        # https://aact.ctti-clinicaltrials.org/downloads
        download_url = self.config.AACT_DOWNLOAD_URL
        if not download_url.endswith(".zip"):
            # Try common AACT download URL pattern
            download_url = "https://aact.ctti-clinicaltrials.org/static/exported_files/monthly/pipe_delimited_files.zip"

        logger.info(f"Downloading AACT data from {download_url}")
        logger.info(
            "Note: If download fails, manually download from "
            "https://aact.ctti-clinicaltrials.org/downloads and place in data/raw/"
        )

        try:
            response = requests.get(
                download_url,
                stream=True,
                timeout=600,  # Longer timeout for large file
                allow_redirects=True,
            )
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            zip_path.parent.mkdir(parents=True, exist_ok=True)

            with open(zip_path, "wb") as f, tqdm(
                desc="Downloading AACT data",
                total=total_size if total_size > 0 else None,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        if total_size > 0:
                            pbar.update(len(chunk))
                        else:
                            pbar.update(len(chunk))

            logger.info(f"Downloaded AACT data to {zip_path}")
            return zip_path

        except requests.RequestException as e:
            logger.error(f"Failed to download AACT data: {e}")
            logger.error(
                "Please manually download the pipe-delimited files from "
                "https://aact.ctti-clinicaltrials.org/downloads "
                f"and place the zip file at {zip_path}"
            )
            raise

    def extract_aact_data(self, zip_path: Path) -> Path:
        """
        Extract AACT zip file to data directory.

        Args:
            zip_path: Path to zip file

        Returns:
            Path to extracted directory
        """
        extract_dir = self.data_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Extracting {zip_path} to {extract_dir}")

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            logger.info(f"Extracted AACT data to {extract_dir}")
            return extract_dir

        except zipfile.BadZipFile as e:
            logger.error(f"Invalid zip file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract AACT data: {e}")
            raise

    def discover_tables(self, extract_dir: Path) -> Dict[str, Path]:
        """
        Discover available table files in extracted directory.

        Args:
            extract_dir: Path to extracted AACT data

        Returns:
            Dictionary mapping table names to file paths
        """
        tables = {}
        for file_path in extract_dir.glob("*.txt"):
            table_name = file_path.stem
            tables[table_name] = file_path

        logger.info(f"Discovered {len(tables)} tables: {list(tables.keys())}")
        return tables

    def load_table(
        self, file_path: Path, required_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Load a pipe-delimited table from AACT.

        Args:
            file_path: Path to table file
            required_columns: Optional list of required columns

        Returns:
            DataFrame with loaded data
        """
        logger.info(f"Loading table: {file_path.name}")

        try:
            df = pd.read_csv(
                file_path,
                sep="|",
                low_memory=False,
                dtype=str,  # Read all as strings initially to avoid type issues
            )

            if required_columns:
                missing = set(required_columns) - set(df.columns)
                if missing:
                    raise ValueError(
                        f"Missing required columns in {file_path.name}: {missing}"
                    )

            logger.info(f"Loaded {len(df)} rows from {file_path.name}")
            return df

        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {e}")
            raise

    def filter_studies(
        self, studies_df: pd.DataFrame, interventions_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Filter studies based on configuration criteria.

        Query rationale:
        - Must have interventions (drugs) to extract meaningful drug data
        - Must have valid phase (not null/empty)
        - Must be in specified status list (active/completed trials)
        - Must be in specified phase list
        - Target >= 500 studies for non-trivial dataset

        Args:
            studies_df: Studies dataframe
            interventions_df: Interventions dataframe

        Returns:
            Filtered studies dataframe
        """
        logger.info(f"Filtering studies from {len(studies_df)} total studies")

        # Get studies with interventions
        studies_with_interventions = set(interventions_df["nct_id"].unique())
        logger.info(
            f"Found {len(studies_with_interventions)} studies with interventions"
        )

        # Apply filters
        filtered = studies_df[
            (studies_df["nct_id"].isin(studies_with_interventions))
            & (studies_df["phase"].notna())
            & (studies_df["phase"] != "")
            & (studies_df["phase"].isin(self.config.PHASES))
            & (studies_df["overall_status"].notna())
            & (studies_df["overall_status"].isin(self.config.STATUS_LIST))
        ].copy()

        logger.info(f"Filtered to {len(filtered)} studies after applying criteria")

        if len(filtered) < self.config.MIN_STUDIES:
            logger.warning(
                f"Only {len(filtered)} studies match criteria (target: {self.config.MIN_STUDIES})"
            )
        else:
            logger.info(
                f"✓ Filtered dataset has {len(filtered)} studies (target: {self.config.MIN_STUDIES})"
            )

        return filtered

    def ingest(self, force_download: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Complete ingestion pipeline: download, extract, load, filter.

        Args:
            force_download: If True, force re-download

        Returns:
            Dictionary of loaded and filtered dataframes
        """
        logger.info("Starting AACT data ingestion")

        extract_dir = self.data_dir / "extracted"
        
        # Check if extracted data already exists
        if extract_dir.exists() and any(extract_dir.glob("*.txt")):
            logger.info(f"Using existing extracted data in {extract_dir}")
        else:
            # Download
            try:
                zip_path = self.download_aact_data(force=force_download)
                # Extract
                extract_dir = self.extract_aact_data(zip_path)
            except Exception as e:
                logger.warning(f"Download/extract failed: {e}")
                if not extract_dir.exists() or not any(extract_dir.glob("*.txt")):
                    raise FileNotFoundError(
                        f"No extracted data found in {extract_dir}. "
                        "Please manually download AACT data from "
                        "https://aact.ctti-clinicaltrials.org/downloads "
                        f"and extract to {extract_dir}"
                    )
                logger.info(f"Using existing extracted data despite download failure")

        # Discover tables
        tables = self.discover_tables(extract_dir)

        # Load required tables
        # Note: AACT file names may vary; we'll try common patterns
        required_tables = {
            "studies": ["nct_id", "brief_title", "phase", "overall_status"],
            "sponsors": ["nct_id", "name", "agency_class", "lead_or_collaborator"],
            "interventions": ["nct_id", "intervention_name", "intervention_type"],
        }
        
        # AACT may use different file naming conventions
        # Common patterns: studies.txt, studies_table.txt, etc.

        data = {}
        for table_name, required_cols in required_tables.items():
            if table_name not in tables:
                # Try alternative names and patterns
                alternatives = [
                    f"{table_name}.txt",
                    f"{table_name}_table.txt",
                    f"{table_name}_data.txt",
                ]
                # Also try case variations
                alternatives.extend([
                    f"{table_name.capitalize()}.txt",
                    f"{table_name.upper()}.txt",
                ])
                
                found = False
                for alt in alternatives:
                    alt_path = extract_dir / alt
                    if alt_path.exists():
                        data[table_name] = self.load_table(alt_path, required_cols)
                        found = True
                        logger.info(f"Found {table_name} as {alt}")
                        break

                if not found:
                    # List available files to help debug
                    available = list(tables.keys())
                    logger.error(
                        f"Required table '{table_name}' not found. "
                        f"Available tables: {available[:10]}..."
                    )
                    raise FileNotFoundError(
                        f"Required table '{table_name}' not found in {extract_dir}. "
                        f"Available files: {list(extract_dir.glob('*.txt'))[:10]}"
                    )
            else:
                data[table_name] = self.load_table(tables[table_name], required_cols)

        # Filter studies
        data["studies"] = self.filter_studies(
            data["studies"], data["interventions"]
        )

        # Filter other tables to only include filtered studies
        study_ids = set(data["studies"]["nct_id"].unique())
        data["sponsors"] = data["sponsors"][
            data["sponsors"]["nct_id"].isin(study_ids)
        ]
        data["interventions"] = data["interventions"][
            data["interventions"]["nct_id"].isin(study_ids)
        ]

        logger.info("Ingestion complete")
        logger.info(f"  Studies: {len(data['studies'])}")
        logger.info(f"  Sponsors: {len(data['sponsors'])}")
        logger.info(f"  Interventions: {len(data['interventions'])}")

        return data


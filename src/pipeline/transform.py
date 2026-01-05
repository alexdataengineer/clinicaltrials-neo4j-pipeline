"""Data transformation and normalization"""

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from src.pipeline.extract import aggregate_trial_route_dosage
from src.utils.hashing import generate_stable_id, normalize_string
from src.utils.logging import get_logger

logger = get_logger(__name__)


class Transformer:
    """Transforms raw AACT data into normalized tables for Neo4j loading."""

    def __init__(self, staged_dir: Path = Path("data/staged")):
        self.staged_dir = Path(staged_dir)
        self.staged_dir.mkdir(parents=True, exist_ok=True)

    def normalize_organization_name(self, name: str) -> str:
        """Normalize organization name for consistent matching."""
        return normalize_string(name)

    def normalize_drug_name(self, name: str) -> str:
        """Normalize drug name for consistent matching."""
        return normalize_string(name)

    def transform_trials(
        self, studies_df: pd.DataFrame, interventions_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Transform studies into normalized trials table.

        Args:
            studies_df: Raw studies dataframe
            interventions_df: Interventions dataframe for route/dosage extraction

        Returns:
            Normalized trials dataframe
        """
        logger.info("Transforming trials")

        trials = []
        for _, row in studies_df.iterrows():
            nct_id = row["nct_id"]

            # Extract route and dosage form
            route, dosage_form = aggregate_trial_route_dosage(
                interventions_df, nct_id
            )

            trial = {
                "nct_id": nct_id,
                "title": row.get("brief_title", ""),
                "phase": row.get("phase", ""),
                "status": row.get("overall_status", ""),
                "start_date": row.get("start_date", ""),
                "completion_date": row.get("completion_date", ""),
                "study_type": row.get("study_type", ""),
                "route": route,
                "dosage_form": dosage_form,
            }
            trials.append(trial)

        trials_df = pd.DataFrame(trials)
        logger.info(f"Transformed {len(trials_df)} trials")
        return trials_df

    def transform_organizations(
        self, sponsors_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Transform sponsors into normalized organizations and relationships.

        Args:
            sponsors_df: Raw sponsors dataframe

        Returns:
            Tuple of (organizations_df, trial_org_edges_df)
        """
        logger.info("Transforming organizations")

        org_map = {}
        edges = []

        for _, row in sponsors_df.iterrows():
            nct_id = row["nct_id"]
            org_name_raw = row.get("name", "")
            agency_class = row.get("agency_class", "")
            rel_type = row.get("lead_or_collaborator", "").upper()

            if not org_name_raw or pd.isna(org_name_raw):
                continue

            # Normalize organization name
            org_name_norm = self.normalize_organization_name(org_name_raw)

            # Generate stable ID
            org_id = generate_stable_id(org_name_norm, namespace="org")

            # Store organization
            if org_id not in org_map:
                org_map[org_id] = {
                    "org_id": org_id,
                    "name_norm": org_name_norm,
                    "name_raw": org_name_raw,
                    "agency_class": agency_class,
                }

            # Create edge
            edge_type = "SPONSORED_BY" if rel_type == "LEAD" else "COLLABORATES_WITH"
            edges.append(
                {
                    "nct_id": nct_id,
                    "org_id": org_id,
                    "rel_type": edge_type,
                }
            )

        organizations_df = pd.DataFrame(list(org_map.values()))
        trial_org_edges_df = pd.DataFrame(edges)

        logger.info(f"Transformed {len(organizations_df)} unique organizations")
        logger.info(f"Created {len(trial_org_edges_df)} trial-organization edges")

        return organizations_df, trial_org_edges_df

    def transform_drugs(
        self, interventions_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Transform interventions into normalized drugs and relationships.

        Args:
            interventions_df: Raw interventions dataframe

        Returns:
            Tuple of (drugs_df, trial_drug_edges_df)
        """
        logger.info("Transforming drugs")

        drug_map = {}
        edges = []

        for _, row in interventions_df.iterrows():
            nct_id = row["nct_id"]
            drug_name_raw = row.get("intervention_name", "")
            intervention_type = row.get("intervention_type", "")

            # Only process drug-type interventions
            if (
                not drug_name_raw
                or pd.isna(drug_name_raw)
                or intervention_type not in ["Drug", "Biological", "Biological/Vaccine"]
            ):
                continue

            # Normalize drug name
            drug_name_norm = self.normalize_drug_name(drug_name_raw)

            # Generate stable ID
            drug_id = generate_stable_id(drug_name_norm, namespace="drug")

            # Store drug
            if drug_id not in drug_map:
                drug_map[drug_id] = {
                    "drug_id": drug_id,
                    "name_norm": drug_name_norm,
                    "name_raw": drug_name_raw,
                }

            # Create edge
            edges.append(
                {
                    "nct_id": nct_id,
                    "drug_id": drug_id,
                }
            )

        drugs_df = pd.DataFrame(list(drug_map.values()))
        trial_drug_edges_df = pd.DataFrame(edges)

        logger.info(f"Transformed {len(drugs_df)} unique drugs")
        logger.info(f"Created {len(trial_drug_edges_df)} trial-drug edges")

        return drugs_df, trial_drug_edges_df

    def transform(
        self, raw_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """
        Complete transformation pipeline.

        Args:
            raw_data: Dictionary of raw dataframes

        Returns:
            Dictionary of transformed dataframes
        """
        logger.info("Starting transformation")

        # Transform each entity type
        trials_df = self.transform_trials(
            raw_data["studies"], raw_data["interventions"]
        )
        organizations_df, trial_org_edges_df = self.transform_organizations(
            raw_data["sponsors"]
        )
        drugs_df, trial_drug_edges_df = self.transform_drugs(
            raw_data["interventions"]
        )

        # Save to staged directory
        trials_df.to_parquet(self.staged_dir / "trials.parquet", index=False)
        organizations_df.to_parquet(
            self.staged_dir / "organizations.parquet", index=False
        )
        trial_org_edges_df.to_parquet(
            self.staged_dir / "trial_org_edges.parquet", index=False
        )
        drugs_df.to_parquet(self.staged_dir / "drugs.parquet", index=False)
        trial_drug_edges_df.to_parquet(
            self.staged_dir / "trial_drug_edges.parquet", index=False
        )

        logger.info("Transformation complete")

        # Calculate metrics
        metrics = {
            "trials": len(trials_df),
            "organizations": len(organizations_df),
            "drugs": len(drugs_df),
            "trial_org_edges": len(trial_org_edges_df),
            "trial_drug_edges": len(trial_drug_edges_df),
            "trials_with_route": len(trials_df[trials_df["route"].notna()]),
            "trials_with_dosage_form": len(
                trials_df[trials_df["dosage_form"].notna()]
            ),
        }

        metrics["pct_trials_with_route"] = (
            metrics["trials_with_route"] / metrics["trials"] * 100
            if metrics["trials"] > 0
            else 0
        )
        metrics["pct_trials_with_dosage_form"] = (
            metrics["trials_with_dosage_form"] / metrics["trials"] * 100
            if metrics["trials"] > 0
            else 0
        )

        logger.info("Transformation metrics:")
        for key, value in metrics.items():
            if isinstance(value, float):
                logger.info(f"  {key}: {value:.2f}")
            else:
                logger.info(f"  {key}: {value}")

        return {
            "trials": trials_df,
            "organizations": organizations_df,
            "trial_org_edges": trial_org_edges_df,
            "drugs": drugs_df,
            "trial_drug_edges": trial_drug_edges_df,
            "metrics": metrics,
        }


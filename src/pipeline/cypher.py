"""Cypher query strings for Neo4j operations"""

# Schema setup queries
CREATE_CONSTRAINTS = """
// Create uniqueness constraints
CREATE CONSTRAINT trial_nct_id_unique IF NOT EXISTS
FOR (t:Trial) REQUIRE t.nct_id IS UNIQUE;

CREATE CONSTRAINT org_org_id_unique IF NOT EXISTS
FOR (o:Organization) REQUIRE o.org_id IS UNIQUE;

CREATE CONSTRAINT drug_drug_id_unique IF NOT EXISTS
FOR (d:Drug) REQUIRE d.drug_id IS UNIQUE;
"""

CREATE_INDEXES = """
// Create indexes for better query performance
CREATE INDEX trial_status_index IF NOT EXISTS
FOR (t:Trial) ON (t.status);

CREATE INDEX trial_phase_index IF NOT EXISTS
FOR (t:Trial) ON (t.phase);

CREATE INDEX org_name_norm_index IF NOT EXISTS
FOR (o:Organization) ON (o.name_norm);

CREATE INDEX drug_name_norm_index IF NOT EXISTS
FOR (d:Drug) ON (d.name_norm);
"""

# Node creation queries
MERGE_TRIAL = """
MERGE (t:Trial {nct_id: $nct_id})
SET t.title = $title,
    t.phase = $phase,
    t.status = $status,
    t.start_date = $start_date,
    t.completion_date = $completion_date,
    t.study_type = $study_type,
    t.route = $route,
    t.dosage_form = $dosage_form
"""

MERGE_ORGANIZATION = """
MERGE (o:Organization {org_id: $org_id})
SET o.name_norm = $name_norm,
    o.name_raw = $name_raw,
    o.agency_class = $agency_class
"""

MERGE_DRUG = """
MERGE (d:Drug {drug_id: $drug_id})
SET d.name_norm = $name_norm,
    d.name_raw = $name_raw
"""

# Relationship creation queries
MERGE_SPONSORED_BY = """
MATCH (t:Trial {nct_id: $nct_id})
MATCH (o:Organization {org_id: $org_id})
MERGE (t)-[:SPONSORED_BY]->(o)
"""

MERGE_COLLABORATES_WITH = """
MATCH (t:Trial {nct_id: $nct_id})
MATCH (o:Organization {org_id: $org_id})
MERGE (t)-[:COLLABORATES_WITH]->(o)
"""

MERGE_TESTS_DRUG = """
MATCH (t:Trial {nct_id: $nct_id})
MATCH (d:Drug {drug_id: $drug_id})
MERGE (t)-[:TESTS_DRUG]->(d)
"""

# Batch loading queries using UNWIND
LOAD_TRIALS_BATCH = """
UNWIND $trials AS trial
MERGE (t:Trial {nct_id: trial.nct_id})
SET t.title = trial.title,
    t.phase = trial.phase,
    t.status = trial.status,
    t.start_date = trial.start_date,
    t.completion_date = trial.completion_date,
    t.study_type = trial.study_type,
    t.route = trial.route,
    t.dosage_form = trial.dosage_form
"""

LOAD_ORGANIZATIONS_BATCH = """
UNWIND $organizations AS org
MERGE (o:Organization {org_id: org.org_id})
SET o.name_norm = org.name_norm,
    o.name_raw = org.name_raw,
    o.agency_class = org.agency_class
"""

LOAD_DRUGS_BATCH = """
UNWIND $drugs AS drug
MERGE (d:Drug {drug_id: drug.drug_id})
SET d.name_norm = drug.name_norm,
    d.name_raw = drug.name_raw
"""

LOAD_SPONSORED_BY_BATCH = """
UNWIND $edges AS edge
MATCH (t:Trial {nct_id: edge.nct_id})
MATCH (o:Organization {org_id: edge.org_id})
MERGE (t)-[:SPONSORED_BY]->(o)
"""

LOAD_COLLABORATES_WITH_BATCH = """
UNWIND $edges AS edge
MATCH (t:Trial {nct_id: edge.nct_id})
MATCH (o:Organization {org_id: edge.org_id})
MERGE (t)-[:COLLABORATES_WITH]->(o)
"""

LOAD_TESTS_DRUG_BATCH = """
UNWIND $edges AS edge
MATCH (t:Trial {nct_id: edge.nct_id})
MATCH (d:Drug {drug_id: edge.drug_id})
MERGE (t)-[:TESTS_DRUG]->(d)
"""


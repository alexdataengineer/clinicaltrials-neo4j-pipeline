// ============================================================================
// ClinicalTrials.gov → Neo4j Knowledge Graph
// Demo Cypher Queries
// ============================================================================

// ----------------------------------------------------------------------------
// Query 1: List trials for a given company/organization
// ----------------------------------------------------------------------------
// Parameter: company_name (e.g., "Pfizer", "Novartis", "National Cancer Institute")
// Returns: NCT ID, title, phase, status for all trials associated with the company

MATCH (o:Organization)-[:SPONSORED_BY|COLLABORATES_WITH]-(t:Trial)
WHERE o.name_norm CONTAINS toLower($company_name)
   OR o.name_raw CONTAINS $company_name
RETURN t.nct_id AS nct_id,
       t.title AS title,
       t.phase AS phase,
       t.status AS status,
       o.name_raw AS organization
ORDER BY t.nct_id
LIMIT 100;

// Example with specific company:
// MATCH (o:Organization)-[:SPONSORED_BY|COLLABORATES_WITH]-(t:Trial)
// WHERE o.name_norm CONTAINS 'pfizer'
// RETURN t.nct_id, t.title, t.phase, t.status, o.name_raw
// ORDER BY t.nct_id
// LIMIT 50;


// ----------------------------------------------------------------------------
// Query 2: Top companies by number of trials
// ----------------------------------------------------------------------------
// Returns: Organization name, count of trials, breakdown by relationship type

MATCH (o:Organization)-[r:SPONSORED_BY|COLLABORATES_WITH]-(t:Trial)
WITH o, type(r) AS rel_type, count(DISTINCT t) AS trial_count
WITH o, sum(trial_count) AS total_trials,
     collect({type: rel_type, count: trial_count}) AS breakdown
RETURN o.name_raw AS organization_name,
       o.name_norm AS organization_normalized,
       total_trials AS number_of_trials,
       breakdown AS relationship_breakdown
ORDER BY total_trials DESC
LIMIT 20;


// ----------------------------------------------------------------------------
// Query 3: Route and dosage form coverage statistics
// ----------------------------------------------------------------------------
// Returns: Coverage statistics and examples for route and dosage form

// Overall coverage
MATCH (t:Trial)
WITH count(t) AS total_trials,
     count(t.route) AS trials_with_route,
     count(t.dosage_form) AS trials_with_dosage_form
RETURN total_trials,
       trials_with_route,
       trials_with_dosage_form,
       round(100.0 * trials_with_route / total_trials, 2) AS pct_with_route,
       round(100.0 * trials_with_dosage_form / total_trials, 2) AS pct_with_dosage_form;

// Route distribution
MATCH (t:Trial)
WHERE t.route IS NOT NULL
WITH t.route AS route, count(*) AS count
RETURN route, count
ORDER BY count DESC;

// Dosage form distribution
MATCH (t:Trial)
WHERE t.dosage_form IS NOT NULL
WITH t.dosage_form AS dosage_form, count(*) AS count
RETURN dosage_form, count
ORDER BY count DESC;

// Examples: Trials with route and dosage form
MATCH (t:Trial)
WHERE t.route IS NOT NULL AND t.dosage_form IS NOT NULL
RETURN t.nct_id AS nct_id,
       t.title AS title,
       t.route AS route,
       t.dosage_form AS dosage_form,
       t.phase AS phase
ORDER BY t.nct_id
LIMIT 20;

// Examples: Trials with route but no dosage form
MATCH (t:Trial)
WHERE t.route IS NOT NULL AND t.dosage_form IS NULL
RETURN t.nct_id AS nct_id,
       t.title AS title,
       t.route AS route,
       t.phase AS phase
ORDER BY t.nct_id
LIMIT 10;

// Examples: Trials with dosage form but no route
MATCH (t:Trial)
WHERE t.dosage_form IS NOT NULL AND t.route IS NULL
RETURN t.nct_id AS nct_id,
       t.title AS title,
       t.dosage_form AS dosage_form,
       t.phase AS phase
ORDER BY t.nct_id
LIMIT 10;


// ----------------------------------------------------------------------------
// Bonus Queries
// ----------------------------------------------------------------------------

// Query 4: Find trials testing a specific drug
MATCH (d:Drug)-[:TESTS_DRUG]-(t:Trial)
WHERE d.name_norm CONTAINS toLower($drug_name)
   OR d.name_raw CONTAINS $drug_name
RETURN d.name_raw AS drug_name,
       t.nct_id AS nct_id,
       t.title AS title,
       t.phase AS phase,
       t.status AS status
ORDER BY t.nct_id
LIMIT 50;

// Query 5: Find organizations collaborating on trials with specific drugs
MATCH (o:Organization)-[:SPONSORED_BY|COLLABORATES_WITH]-(t:Trial)-[:TESTS_DRUG]-(d:Drug)
WHERE d.name_norm CONTAINS toLower($drug_name)
WITH o, d, count(DISTINCT t) AS trial_count
RETURN o.name_raw AS organization,
       d.name_raw AS drug,
       trial_count
ORDER BY trial_count DESC
LIMIT 20;

// Query 6: Phase distribution across all trials
MATCH (t:Trial)
WITH t.phase AS phase, count(*) AS count
RETURN phase, count
ORDER BY 
  CASE phase
    WHEN 'Phase 1' THEN 1
    WHEN 'Phase 2' THEN 2
    WHEN 'Phase 3' THEN 3
    WHEN 'Phase 4' THEN 4
    ELSE 5
  END;

// Query 7: Status distribution
MATCH (t:Trial)
WITH t.status AS status, count(*) AS count
RETURN status, count
ORDER BY count DESC;

// Query 8: Most tested drugs (top 20)
MATCH (d:Drug)-[:TESTS_DRUG]-(t:Trial)
WITH d, count(DISTINCT t) AS trial_count
RETURN d.name_raw AS drug_name,
       d.name_norm AS drug_normalized,
       trial_count
ORDER BY trial_count DESC
LIMIT 20;

// Query 9: Organizations and their drug portfolios
MATCH (o:Organization)-[:SPONSORED_BY|COLLABORATES_WITH]-(t:Trial)-[:TESTS_DRUG]-(d:Drug)
WITH o, d, count(DISTINCT t) AS trial_count
WHERE trial_count >= 5
RETURN o.name_raw AS organization,
       collect(DISTINCT d.name_raw) AS drugs,
       sum(trial_count) AS total_trials
ORDER BY total_trials DESC
LIMIT 20;

// Query 10: Route and dosage form combinations
MATCH (t:Trial)
WHERE t.route IS NOT NULL AND t.dosage_form IS NOT NULL
WITH t.route AS route, t.dosage_form AS dosage_form, count(*) AS count
RETURN route, dosage_form, count
ORDER BY count DESC
LIMIT 30;


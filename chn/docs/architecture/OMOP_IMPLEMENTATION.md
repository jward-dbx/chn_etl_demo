# OMOP Implementation Guide

## OMOP Common Data Model (CDM) v5.4

The OMOP CDM is a standardized data model for observational healthcare data, developed by the Observational Health Data Sciences and Informatics (OHDSI) community.

## Key Concepts

### 1. Standardized Vocabularies

OMOP uses standardized vocabularies to ensure consistent representation of clinical concepts:

- **Concept**: The fundamental unit representing a clinical entity
- **Concept_ID**: Unique identifier for each concept
- **Standard Concepts**: Preferred concepts for analysis
- **Source Concepts**: Original codes from source systems

### 2. Domain Tables

Clinical data is organized into domain-specific tables:

#### Person Domain
- Contains demographic information about patients
- One row per person
- Links to other domains via person_id

#### Visit Domain
- Captures healthcare encounters
- Includes inpatient, outpatient, ER visits
- Links to other events via visit_occurrence_id

#### Condition Domain
- Records diagnoses and conditions
- Maps to SNOMED CT standard concepts
- Includes start and end dates

#### Drug Domain
- Medication exposures and prescriptions
- Maps to RxNorm standard concepts
- Includes quantity, days supply, and route

#### Procedure Domain
- Medical procedures and interventions
- Maps to SNOMED CT or CPT4
- Links to visit occurrence

#### Measurement Domain
- Lab results and vital signs
- Maps to LOINC standard concepts
- Includes value, unit, and range

### 3. Standardization Process

```
Source Data → Source Concepts → Mapping → Standard Concepts → OMOP CDM
```

**Steps:**
1. **Extract**: Pull data from source systems
2. **Map**: Use CONCEPT_RELATIONSHIP to find standard concepts
3. **Transform**: Apply business rules and data quality checks
4. **Load**: Insert into OMOP CDM tables
5. **Validate**: Run OMOP constraint checks

## Implementation in This Project

### Bronze Layer: Source Data

```python
# Example: Raw EHR data
bronze_patient = {
    'patient_id': '12345',
    'birth_date': '1980-01-15',
    'gender': 'F',
    'zip_code': '02115'
}
```

### Silver Layer: Cleaned & Mapped

```python
# Cleaned and mapped to OMOP concepts
silver_patient = {
    'source_patient_id': '12345',
    'birth_datetime': datetime(1980, 1, 15),
    'gender_concept_id': 8532,  # FEMALE
    'race_concept_id': 0,  # Unknown
    'ethnicity_concept_id': 0,  # Unknown
    'location_id': lookup_location('02115')
}
```

### Gold Layer: OMOP CDM

```sql
-- PERSON table (OMOP CDM)
INSERT INTO gold_omop.person (
    person_id,
    gender_concept_id,
    year_of_birth,
    month_of_birth,
    day_of_birth,
    birth_datetime,
    race_concept_id,
    ethnicity_concept_id,
    location_id,
    person_source_value
)
SELECT
    generate_person_id(source_patient_id),
    gender_concept_id,
    YEAR(birth_datetime),
    MONTH(birth_datetime),
    DAY(birth_datetime),
    birth_datetime,
    race_concept_id,
    ethnicity_concept_id,
    location_id,
    source_patient_id
FROM silver_clean.patients;
```

## OMOP Table Relationships

```
PERSON (1) ←→ (N) OBSERVATION_PERIOD
    ↓
VISIT_OCCURRENCE (N) ←→ (1) PERSON
    ↓
CONDITION_OCCURRENCE (N) ←→ (1) VISIT_OCCURRENCE
DRUG_EXPOSURE (N) ←→ (1) VISIT_OCCURRENCE
PROCEDURE_OCCURRENCE (N) ←→ (1) VISIT_OCCURRENCE
MEASUREMENT (N) ←→ (1) VISIT_OCCURRENCE
OBSERVATION (N) ←→ (1) VISIT_OCCURRENCE
```

## Vocabulary Mapping Examples

### ICD-10-CM to SNOMED CT

```sql
-- Find standard concept for ICD-10-CM E11.9 (Type 2 diabetes mellitus)
SELECT
    c1.concept_code AS source_code,
    c1.concept_name AS source_name,
    c2.concept_id AS standard_concept_id,
    c2.concept_name AS standard_name
FROM concept c1
JOIN concept_relationship cr ON c1.concept_id = cr.concept_id_1
JOIN concept c2 ON cr.concept_id_2 = c2.concept_id
WHERE c1.concept_code = 'E11.9'
    AND c1.vocabulary_id = 'ICD10CM'
    AND cr.relationship_id = 'Maps to'
    AND c2.standard_concept = 'S';
```

### NDC to RxNorm

```sql
-- Find RxNorm standard concept for NDC drug code
SELECT
    c1.concept_code AS ndc_code,
    c1.concept_name AS drug_name,
    c2.concept_id AS rxnorm_concept_id,
    c2.concept_name AS rxnorm_name
FROM concept c1
JOIN concept_relationship cr ON c1.concept_id = cr.concept_id_1
JOIN concept c2 ON cr.concept_id_2 = c2.concept_id
WHERE c1.concept_code = '00071015523'
    AND c1.vocabulary_id = 'NDC'
    AND cr.relationship_id = 'Maps to'
    AND c2.vocabulary_id = 'RxNorm'
    AND c2.standard_concept = 'S';
```

## Data Quality Checks

### Required OMOP Constraints

1. **Person table must have valid gender_concept_id**
2. **Birth dates must be reasonable (not in future)**
3. **Visit start must be <= visit end**
4. **All concept_ids must exist in CONCEPT table**
5. **All foreign keys must have valid references**
6. **Dates must be within observation periods**

### Example Quality Check

```python
def validate_person_table(df):
    """Validate PERSON table against OMOP constraints."""
    errors = []
    
    # Check for nulls in required fields
    required_fields = ['person_id', 'gender_concept_id', 'year_of_birth']
    for field in required_fields:
        null_count = df[field].isna().sum()
        if null_count > 0:
            errors.append(f"{field} has {null_count} null values")
    
    # Check year of birth is reasonable
    current_year = datetime.now().year
    invalid_yob = df[
        (df['year_of_birth'] < 1900) | 
        (df['year_of_birth'] > current_year)
    ]
    if len(invalid_yob) > 0:
        errors.append(f"{len(invalid_yob)} invalid year_of_birth values")
    
    return errors
```

## Best Practices

1. **Always use standard concepts** for analysis
2. **Preserve source values** in _source_value fields
3. **Maintain data lineage** from source to OMOP
4. **Validate against OMOP constraints** before loading
5. **Document custom mappings** and extensions
6. **Use OHDSI tools** for validation (Achilles, Data Quality Dashboard)
7. **Keep vocabularies updated** regularly

## Resources

- [OMOP CDM Documentation](https://ohdsi.github.io/CommonDataModel/)
- [OHDSI Forums](https://forums.ohdsi.org/)
- [Athena Vocabulary Browser](https://athena.ohdsi.org/)
- [OHDSI GitHub](https://github.com/OHDSI)
- [Book of OHDSI](https://ohdsi.github.io/TheBookOfOhdsi/)

---

*Last updated: January 11, 2026*

# OMOP Semantic Project - Architecture Documentation

## Overview

This project implements the OMOP Common Data Model (CDM) v5.4 on Databricks, enabling standardized analysis of observational healthcare data from multiple sources.

## Architecture Principles

### 1. Medallion Architecture

We follow Databricks' Medallion Architecture pattern:

```
Source Systems → [Bronze Layer] → [Silver Layer] → [Gold Layer] → Analytics
                  Raw Data        Cleaned Data    OMOP CDM       Insights
```

#### Bronze Layer (Raw)
- Exact copy of source data
- Minimal transformations
- Preserves data lineage
- Format: Delta Lake with schema enforcement

#### Silver Layer (Cleaned)
- Validated and cleaned data
- Standardized formats
- Deduplication
- Business rules applied
- Reference data joins

#### Gold Layer (OMOP CDM)
- OMOP CDM v5.4 compliant tables
- Standardized vocabularies applied
- Ready for analysis
- Optimized for queries

### 2. Unity Catalog Structure

```
catalog: dev_omop / prod_omop
├── bronze_raw
│   ├── source_system_1
│   └── source_system_2
├── silver_clean
│   ├── standardized_data
│   └── reference_data
└── gold_omop
    ├── person
    ├── observation
    ├── measurement
    ├── condition_occurrence
    └── ... (other OMOP tables)
```

### 3. Data Flow

```
1. Ingestion (ETL Bronze)
   ↓
2. Cleansing & Validation (ETL Silver)
   ↓
3. OMOP Mapping & Standardization (ETL Gold)
   ↓
4. Quality Checks & Validation
   ↓
5. Analytics & Reporting
```

## OMOP CDM Implementation

### Core Clinical Tables
- **Person**: Patient demographics
- **Observation_Period**: Time periods of data availability
- **Visit_Occurrence**: Healthcare encounters
- **Condition_Occurrence**: Diagnoses
- **Procedure_Occurrence**: Medical procedures
- **Drug_Exposure**: Medication exposures
- **Measurement**: Lab results and vital signs
- **Observation**: Additional clinical observations

### Vocabulary Tables
- **Concept**: Standard concepts from all vocabularies
- **Concept_Relationship**: Relationships between concepts
- **Concept_Ancestor**: Hierarchical relationships
- **Vocabulary**: List of vocabularies (SNOMED, ICD-10, etc.)

### Standardized Vocabularies
- SNOMED CT (clinical terms)
- RxNorm (medications)
- LOINC (lab tests)
- ICD-10-CM (diagnoses)
- CPT4 (procedures)

## Technology Stack

- **Platform**: Databricks on AWS/Azure/GCP
- **Storage**: Delta Lake
- **Compute**: Databricks SQL Warehouses & Clusters
- **Orchestration**: Databricks Workflows
- **Governance**: Unity Catalog
- **Development**: Python, SQL, Spark
- **Testing**: pytest, Great Expectations
- **Deployment**: Databricks Asset Bundles (DABs)

## Data Quality Framework

### Validation Checks
1. **Schema Validation**: Column names, types, nullability
2. **Referential Integrity**: Foreign key relationships
3. **Value Ranges**: Valid date ranges, numeric bounds
4. **OMOP Constraints**: CDM-specific rules
5. **Completeness**: Required field population
6. **Uniqueness**: Primary key constraints

### Quality Metrics
- Data completeness %
- Standardization rate (mapped to standard concepts)
- Referential integrity violations
- Duplicate records
- Invalid values

## Security & Compliance

### HIPAA Compliance
- PHI data encrypted at rest and in transit
- Row-level security via Unity Catalog
- Audit logging enabled
- Access controls and data masking

### Data Governance
- Unity Catalog for centralized governance
- Data lineage tracking
- Data classification tags
- Access policies and permissions

## Performance Optimization

### Partitioning Strategy
- Partition by date columns (person_id for large tables)
- Z-ordering on frequently filtered columns
- Optimize file sizes (128MB-1GB)

### Query Optimization
- Use broadcast joins for small lookup tables
- Cache frequently accessed tables
- Use column pruning and predicate pushdown
- Implement incremental processing

## Monitoring & Observability

### Metrics to Track
- Pipeline execution time
- Data volume processed
- Quality check pass/fail rates
- Query performance
- Cost per workload

### Alerting
- Pipeline failures
- Data quality issues
- Performance degradation
- Schema changes

## Future Enhancements

1. Real-time streaming ingestion
2. ML/AI models for clinical predictions
3. Federated analytics across multiple sites
4. Patient cohort identification tools
5. Clinical decision support integration

## References

- [OMOP CDM Documentation](https://ohdsi.github.io/CommonDataModel/)
- [Databricks Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
- [Unity Catalog Best Practices](https://docs.databricks.com/data-governance/unity-catalog/best-practices.html)

---

*Last updated: January 11, 2026*

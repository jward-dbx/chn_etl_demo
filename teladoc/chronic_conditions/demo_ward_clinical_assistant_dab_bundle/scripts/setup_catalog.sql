-- Setup script to create catalog and schema
-- Run this via Databricks SQL or notebook before deploying the bundle

-- Create catalog (requires storage location or use default)
CREATE CATALOG IF NOT EXISTS ward_demo
COMMENT 'Catalog for clinical assistant demo';

-- Use the catalog
USE CATALOG ward_demo;

-- Create schema
CREATE SCHEMA IF NOT EXISTS justin_ward_demo_ward_clinical_assistant
COMMENT 'Schema for clinical assistant demo';

-- Grant permissions (adjust as needed)
-- GRANT USE CATALOG ON CATALOG ward_demo TO `account users`;
-- GRANT USE SCHEMA ON SCHEMA ward_demo.justin_ward_demo_ward_clinical_assistant TO `account users`;


#!/usr/bin/env python3
"""
Script to create catalog and schema for the clinical assistant demo.
Run this before deploying the bundle.
"""

from databricks.sdk import WorkspaceClient
import time

w = WorkspaceClient()

# Get warehouse ID
print("Finding warehouse...")
warehouses = w.warehouses.list()
warehouse_id = None
for wh in warehouses:
    if "Clinical Assistant" in wh.name:
        warehouse_id = wh.id
        print(f"✅ Found warehouse: {wh.name} (ID: {warehouse_id})")
        break

if not warehouse_id:
    print("❌ No warehouse found. Please create one first.")
    exit(1)

# Create catalog via SQL
print("\n" + "="*50)
print("Step 1: Creating catalog 'ward_demo'...")
print("="*50)

sql_create_catalog = "CREATE CATALOG IF NOT EXISTS ward_demo COMMENT 'Catalog for clinical assistant demo';"

try:
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql_create_catalog,
        wait_timeout="30s"
    )
    
    # Wait a bit for catalog to be available
    time.sleep(2)
    
    # Verify
    verify_sql = "SHOW CATALOGS LIKE 'ward_demo';"
    verify_result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=verify_sql,
        wait_timeout="10s"
    )
    
    print("✅ Catalog 'ward_demo' created successfully!")
    
except Exception as e:
    print(f"⚠️  SQL execution error: {e}")
    print("\nPlease create the catalog manually:")
    print("  1. Go to: https://fe-vm-vdm-serverless-exom73.cloud.databricks.com")
    print("  2. Click 'SQL' → 'SQL Editor'")
    print("  3. Run: CREATE CATALOG ward_demo;")
    print("\nThen run this script again to create the schema.")
    exit(1)

# Create schema
print("\n" + "="*50)
print("Step 2: Creating schema...")
print("="*50)

try:
    schema = w.schemas.create(
        name="justin_ward_demo_ward_clinical_assistant",
        catalog_name="ward_demo",
        comment="Schema for clinical assistant demo"
    )
    print("✅ Schema created successfully!")
except Exception as e:
    error_msg = str(e).lower()
    if "already exists" in error_msg or "duplicate" in error_msg:
        print("✅ Schema already exists")
    else:
        print(f"⚠️  Schema creation error: {e}")
        print("\nTrying via SQL...")
        try:
            sql_create_schema = """
            USE CATALOG ward_demo;
            CREATE SCHEMA IF NOT EXISTS justin_ward_demo_ward_clinical_assistant
            COMMENT 'Schema for clinical assistant demo';
            """
            result = w.statement_execution.execute_statement(
                warehouse_id=warehouse_id,
                statement=sql_create_schema,
                wait_timeout="30s"
            )
            print("✅ Schema created via SQL!")
        except Exception as e2:
            print(f"❌ SQL creation also failed: {e2}")
            print("\nPlease create manually:")
            print("  USE CATALOG ward_demo;")
            print("  CREATE SCHEMA justin_ward_demo_ward_clinical_assistant;")

print("\n" + "="*50)
print("✅ Setup Complete!")
print("="*50)
print("\nYou can now deploy the bundle:")
print("  databricks bundle deploy")
print("\nOr run data generation:")
print("  ./scripts/run_data_generation.sh")


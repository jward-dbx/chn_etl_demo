#!/usr/bin/env python3
"""
Schema Validation Script for Silver Layer Tables
-------------------------------------------------
Validates that silver layer tables conform to enterprise standards for:
- Column naming conventions
- Required metadata columns
- Data types
- SCD Type 2 structure

Usage:
    python validate_schema.py --env dev
    python validate_schema.py --env prod --table customers_silver
    python validate_schema.py --config config.yml
"""

import argparse
import sys
import json
from typing import Dict, List, Any
from pyspark.sql import SparkSession
from pyspark.sql.types import *
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SilverSchemaValidator:
    """Validates silver layer table schemas against enterprise standards."""
    
    def __init__(self, spark: SparkSession, catalog: str, schema: str):
        self.spark = spark
        self.catalog = catalog
        self.schema = schema
        
        # Required metadata columns for all silver tables
        self.required_metadata_columns = {
            "record_created_at": TimestampType(),
            "record_updated_at": TimestampType(),
            "source_system": StringType(),
            "load_id": StringType(),
            "is_current": BooleanType(),
            "is_deleted": BooleanType(),
        }
        
        # SCD Type 2 columns
        self.scd_type2_columns = {
            "effective_start_date": TimestampType(),
            "effective_end_date": TimestampType(),
        }
    
    def list_silver_tables(self) -> List[str]:
        """List all tables in the silver schema."""
        try:
            tables = self.spark.sql(f"SHOW TABLES IN {self.catalog}.{self.schema}").collect()
            return [row.tableName for row in tables]
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return []
    
    def validate_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        Validate a single table's schema.
        
        Returns:
            Dictionary with validation results
        """
        logger.info(f"Validating schema for: {self.catalog}.{self.schema}.{table_name}")
        
        issues = []
        warnings = []
        recommendations = []
        
        try:
            # Get table schema
            table_path = f"{self.catalog}.{self.schema}.{table_name}"
            df = self.spark.table(table_path)
            schema = df.schema
            
            # Get column info
            column_names = [field.name for field in schema.fields]
            column_types = {field.name: field.dataType for field in schema.fields}
            
            # Validation 1: Check for required metadata columns
            for col, expected_type in self.required_metadata_columns.items():
                if col not in column_names:
                    issues.append(f"Missing required metadata column: '{col}'")
                else:
                    actual_type = column_types[col]
                    if type(actual_type).__name__ != type(expected_type).__name__:
                        issues.append(
                            f"Column '{col}' has incorrect type. "
                            f"Expected: {type(expected_type).__name__}, "
                            f"Got: {type(actual_type).__name__}"
                        )
            
            # Validation 2: Check for SCD Type 2 columns
            has_scd_columns = all(col in column_names for col in self.scd_type2_columns.keys())
            if not has_scd_columns:
                warnings.append(
                    "Table does not include SCD Type 2 columns "
                    "(effective_start_date, effective_end_date). "
                    "This is acceptable for non-historical tables."
                )
            
            # Validation 3: Check column naming conventions
            for col in column_names:
                # Should be snake_case (all lowercase)
                if col != col.lower():
                    issues.append(f"Column '{col}' is not in snake_case (should be lowercase)")
                
                # Should not start with underscore
                if col.startswith('_'):
                    issues.append(f"Column '{col}' should not start with underscore")
                
                # Should not have consecutive underscores
                if '__' in col:
                    warnings.append(f"Column '{col}' has consecutive underscores")
            
            # Validation 4: Check boolean column naming
            for field in schema.fields:
                if isinstance(field.dataType, BooleanType):
                    if not (field.name.startswith('is_') or 
                           field.name.startswith('has_') or
                           field.name.startswith('needs_')):
                        warnings.append(
                            f"Boolean column '{field.name}' should start with "
                            "'is_', 'has_', or 'needs_'"
                        )
            
            # Validation 5: Check timestamp column naming
            for field in schema.fields:
                if isinstance(field.dataType, TimestampType):
                    if not (field.name.endswith('_at') or 
                           field.name.endswith('_date') or
                           field.name.endswith('_time')):
                        warnings.append(
                            f"Timestamp column '{field.name}' should end with "
                            "'_at', '_date', or '_time'"
                        )
            
            # Validation 6: Check amount columns use DecimalType
            for field in schema.fields:
                if field.name.endswith('_amount'):
                    if not isinstance(field.dataType, DecimalType):
                        recommendations.append(
                            f"Amount column '{field.name}' should use DecimalType, "
                            f"currently using {type(field.dataType).__name__}"
                        )
            
            # Validation 7: Check for business key(s)
            # Common business key patterns
            potential_keys = [col for col in column_names 
                            if col.endswith('_id') and not col.startswith('is_')]
            if not potential_keys:
                warnings.append("No business key column found (expected *_id column)")
            
            # Validation 8: Check table properties
            table_properties = self.spark.sql(
                f"SHOW TBLPROPERTIES {table_path}"
            ).collect()
            
            property_dict = {row.key: row.value for row in table_properties}
            
            # Recommend enabling change data feed
            if 'delta.enableChangeDataFeed' not in property_dict:
                recommendations.append(
                    "Consider enabling Change Data Feed: "
                    "ALTER TABLE SET TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')"
                )
            
            # Check for liquid clustering
            if 'clusteringColumns' not in property_dict:
                recommendations.append(
                    "Consider using liquid clustering for high-cardinality columns"
                )
            
            # Get table statistics
            row_count = df.count()
            column_count = len(column_names)
            
            # Calculate validation score
            total_checks = len(self.required_metadata_columns)
            passed_checks = total_checks - len([i for i in issues if 'Missing required' in i])
            validation_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            
            return {
                "table_name": table_name,
                "is_valid": len(issues) == 0,
                "validation_score": validation_score,
                "issues": issues,
                "warnings": warnings,
                "recommendations": recommendations,
                "statistics": {
                    "row_count": row_count,
                    "column_count": column_count,
                    "has_scd_type2": has_scd_columns,
                    "has_change_data_feed": 'delta.enableChangeDataFeed' in property_dict
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to validate table {table_name}: {e}")
            return {
                "table_name": table_name,
                "is_valid": False,
                "validation_score": 0,
                "issues": [f"Failed to validate: {str(e)}"],
                "warnings": [],
                "recommendations": [],
                "statistics": {}
            }
    
    def validate_all_tables(self) -> Dict[str, Any]:
        """Validate all tables in the silver schema."""
        logger.info(f"Validating all tables in {self.catalog}.{self.schema}")
        
        tables = self.list_silver_tables()
        if not tables:
            logger.warning("No tables found to validate")
            return {"tables": [], "summary": {}}
        
        logger.info(f"Found {len(tables)} tables to validate")
        
        results = []
        for table in tables:
            result = self.validate_table_schema(table)
            results.append(result)
        
        # Calculate summary statistics
        total_tables = len(results)
        valid_tables = len([r for r in results if r["is_valid"]])
        total_issues = sum(len(r["issues"]) for r in results)
        total_warnings = sum(len(r["warnings"]) for r in results)
        avg_score = sum(r["validation_score"] for r in results) / total_tables if total_tables > 0 else 0
        
        summary = {
            "total_tables": total_tables,
            "valid_tables": valid_tables,
            "invalid_tables": total_tables - valid_tables,
            "total_issues": total_issues,
            "total_warnings": total_warnings,
            "average_validation_score": round(avg_score, 2),
            "overall_status": "PASSED" if valid_tables == total_tables else "FAILED"
        }
        
        return {
            "catalog": self.catalog,
            "schema": self.schema,
            "tables": results,
            "summary": summary
        }
    
    def print_validation_report(self, results: Dict[str, Any]):
        """Print a formatted validation report."""
        summary = results["summary"]
        
        print("\n" + "=" * 80)
        print("SILVER LAYER SCHEMA VALIDATION REPORT")
        print("=" * 80)
        print(f"\nCatalog: {results['catalog']}")
        print(f"Schema: {results['schema']}")
        print(f"\nOverall Status: {summary['overall_status']}")
        print(f"Average Validation Score: {summary['average_validation_score']}%")
        print(f"\nTables Summary:")
        print(f"  Total: {summary['total_tables']}")
        print(f"  ✅ Valid: {summary['valid_tables']}")
        print(f"  ❌ Invalid: {summary['invalid_tables']}")
        print(f"\nIssues & Warnings:")
        print(f"  ❌ Issues: {summary['total_issues']}")
        print(f"  ⚠️  Warnings: {summary['total_warnings']}")
        
        print("\n" + "-" * 80)
        print("TABLE DETAILS")
        print("-" * 80)
        
        for table in results["tables"]:
            status = "✅ VALID" if table["is_valid"] else "❌ INVALID"
            print(f"\n📊 {table['table_name']} - {status} ({table['validation_score']:.0f}%)")
            
            if table["statistics"]:
                stats = table["statistics"]
                print(f"   Rows: {stats.get('row_count', 'N/A'):,}")
                print(f"   Columns: {stats.get('column_count', 'N/A')}")
                print(f"   SCD Type 2: {'Yes' if stats.get('has_scd_type2') else 'No'}")
                print(f"   Change Data Feed: {'Enabled' if stats.get('has_change_data_feed') else 'Disabled'}")
            
            if table["issues"]:
                print(f"\n   ❌ Issues ({len(table['issues'])}):")
                for issue in table["issues"]:
                    print(f"      • {issue}")
            
            if table["warnings"]:
                print(f"\n   ⚠️  Warnings ({len(table['warnings'])}):")
                for warning in table["warnings"]:
                    print(f"      • {warning}")
            
            if table["recommendations"]:
                print(f"\n   💡 Recommendations ({len(table['recommendations'])}):")
                for rec in table["recommendations"]:
                    print(f"      • {rec}")
        
        print("\n" + "=" * 80)
        
        # Save report to JSON
        report_file = f"schema_validation_report_{results['schema']}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nDetailed report saved to: {report_file}")
        print("=" * 80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate silver layer table schemas"
    )
    parser.add_argument(
        "--env",
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Environment to validate"
    )
    parser.add_argument(
        "--catalog",
        help="Unity Catalog name (overrides env default)"
    )
    parser.add_argument(
        "--schema",
        default="silver",
        help="Schema name (default: silver)"
    )
    parser.add_argument(
        "--table",
        help="Validate specific table only"
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit with error code if warnings are found"
    )
    
    args = parser.parse_args()
    
    # Determine catalog based on environment if not specified
    if args.catalog:
        catalog = args.catalog
    else:
        catalog_map = {
            "dev": "dev_catalog",
            "staging": "staging_catalog",
            "prod": "prod_catalog"
        }
        catalog = catalog_map.get(args.env, "dev_catalog")
    
    # Initialize Spark
    logger.info("Initializing Spark session...")
    spark = SparkSession.builder \
        .appName("SilverSchemaValidation") \
        .getOrCreate()
    
    # Create validator
    validator = SilverSchemaValidator(spark, catalog, args.schema)
    
    # Run validation
    if args.table:
        # Validate single table
        result = validator.validate_table_schema(args.table)
        results = {
            "catalog": catalog,
            "schema": args.schema,
            "tables": [result],
            "summary": {
                "total_tables": 1,
                "valid_tables": 1 if result["is_valid"] else 0,
                "invalid_tables": 0 if result["is_valid"] else 1,
                "total_issues": len(result["issues"]),
                "total_warnings": len(result["warnings"]),
                "average_validation_score": result["validation_score"],
                "overall_status": "PASSED" if result["is_valid"] else "FAILED"
            }
        }
    else:
        # Validate all tables
        results = validator.validate_all_tables()
    
    # Print report
    validator.print_validation_report(results)
    
    # Determine exit code
    has_issues = results["summary"]["total_issues"] > 0
    has_warnings = results["summary"]["total_warnings"] > 0
    
    if has_issues:
        logger.error("Validation failed with issues")
        sys.exit(1)
    elif has_warnings and args.fail_on_warning:
        logger.warning("Validation completed with warnings (treated as errors)")
        sys.exit(1)
    elif has_warnings:
        logger.warning("Validation completed with warnings")
        sys.exit(0)
    else:
        logger.info("Validation passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()

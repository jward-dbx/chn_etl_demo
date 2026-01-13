"""
Data Quality Rules Template for Silver Layer ETL
-------------------------------------------------
This template provides a comprehensive framework for implementing data quality
checks using Great Expectations and custom PySpark validation logic.

Usage:
    from data_quality_rules import DataQualityValidator
    
    validator = DataQualityValidator(spark, catalog, schema)
    results = validator.validate_table("customers_silver")
    
    if not results["is_valid"]:
        # Handle quality failures
        validator.log_quality_issues(results)
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import *
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataQualityRule:
    """Base class for defining data quality rules."""
    
    def __init__(self, rule_name: str, description: str, severity: str = "ERROR"):
        """
        Args:
            rule_name: Unique identifier for the rule
            description: Human-readable description
            severity: ERROR, WARNING, or INFO
        """
        self.rule_name = rule_name
        self.description = description
        self.severity = severity
        
    def validate(self, df: DataFrame) -> Dict[str, Any]:
        """
        Execute the validation rule.
        Returns dict with: {"passed": bool, "failure_count": int, "details": str}
        """
        raise NotImplementedError("Subclasses must implement validate()")


class CompletenessRule(DataQualityRule):
    """Check that required columns have no null values."""
    
    def __init__(self, columns: List[str], threshold: float = 1.0):
        """
        Args:
            columns: List of column names to check
            threshold: Minimum acceptable completeness (0.0 to 1.0)
        """
        super().__init__(
            rule_name=f"completeness_check_{'_'.join(columns)}",
            description=f"Check completeness of columns: {', '.join(columns)}",
            severity="ERROR" if threshold == 1.0 else "WARNING"
        )
        self.columns = columns
        self.threshold = threshold
    
    def validate(self, df: DataFrame) -> Dict[str, Any]:
        total_records = df.count()
        results = {}
        
        for col in self.columns:
            if col not in df.columns:
                results[col] = {
                    "passed": False,
                    "failure_count": total_records,
                    "details": f"Column '{col}' not found in dataframe"
                }
                continue
            
            null_count = df.filter(F.col(col).isNull()).count()
            completeness = (total_records - null_count) / total_records if total_records > 0 else 0
            
            results[col] = {
                "passed": completeness >= self.threshold,
                "failure_count": null_count,
                "completeness": completeness,
                "details": f"Completeness: {completeness:.2%}, Nulls: {null_count}/{total_records}"
            }
        
        all_passed = all(r["passed"] for r in results.values())
        total_failures = sum(r["failure_count"] for r in results.values())
        
        return {
            "passed": all_passed,
            "failure_count": total_failures,
            "details": results
        }


class UniquenessRule(DataQualityRule):
    """Check that specified columns have unique values."""
    
    def __init__(self, columns: List[str], allow_null: bool = False):
        super().__init__(
            rule_name=f"uniqueness_check_{'_'.join(columns)}",
            description=f"Check uniqueness of columns: {', '.join(columns)}",
            severity="ERROR"
        )
        self.columns = columns
        self.allow_null = allow_null
    
    def validate(self, df: DataFrame) -> Dict[str, Any]:
        if not self.allow_null:
            df_to_check = df.filter(F.col(self.columns[0]).isNotNull())
        else:
            df_to_check = df
        
        total_count = df_to_check.count()
        distinct_count = df_to_check.select(self.columns).distinct().count()
        duplicate_count = total_count - distinct_count
        
        passed = duplicate_count == 0
        
        return {
            "passed": passed,
            "failure_count": duplicate_count,
            "details": f"Total: {total_count}, Distinct: {distinct_count}, Duplicates: {duplicate_count}"
        }


class ValidityRule(DataQualityRule):
    """Check that values match expected patterns or ranges."""
    
    def __init__(self, column: str, condition: str, description: str = None):
        """
        Args:
            column: Column name to validate
            condition: SQL condition string (e.g., "col > 0", "col RLIKE '^[A-Z]+$'")
            description: Optional description
        """
        super().__init__(
            rule_name=f"validity_check_{column}",
            description=description or f"Validate {column} with condition: {condition}",
            severity="ERROR"
        )
        self.column = column
        self.condition = condition
    
    def validate(self, df: DataFrame) -> Dict[str, Any]:
        if self.column not in df.columns:
            return {
                "passed": False,
                "failure_count": df.count(),
                "details": f"Column '{self.column}' not found"
            }
        
        # Apply the condition
        invalid_df = df.filter(~F.expr(self.condition))
        invalid_count = invalid_df.count()
        total_count = df.count()
        
        passed = invalid_count == 0
        
        return {
            "passed": passed,
            "failure_count": invalid_count,
            "details": f"Invalid records: {invalid_count}/{total_count} ({invalid_count/total_count*100:.2f}%)"
        }


class ConsistencyRule(DataQualityRule):
    """Check cross-field consistency (e.g., start_date < end_date)."""
    
    def __init__(self, rule_name: str, condition: str, description: str):
        super().__init__(rule_name, description, severity="WARNING")
        self.condition = condition
    
    def validate(self, df: DataFrame) -> Dict[str, Any]:
        inconsistent_df = df.filter(~F.expr(self.condition))
        inconsistent_count = inconsistent_df.count()
        total_count = df.count()
        
        passed = inconsistent_count == 0
        
        return {
            "passed": passed,
            "failure_count": inconsistent_count,
            "details": f"Inconsistent records: {inconsistent_count}/{total_count}"
        }


class TimelinessRule(DataQualityRule):
    """Check data freshness and timeliness."""
    
    def __init__(self, timestamp_column: str, max_age_hours: int = 24):
        super().__init__(
            rule_name=f"timeliness_check_{timestamp_column}",
            description=f"Check that {timestamp_column} is within {max_age_hours} hours",
            severity="WARNING"
        )
        self.timestamp_column = timestamp_column
        self.max_age_hours = max_age_hours
    
    def validate(self, df: DataFrame) -> Dict[str, Any]:
        cutoff_time = F.current_timestamp() - F.expr(f"INTERVAL {self.max_age_hours} HOURS")
        
        stale_df = df.filter(F.col(self.timestamp_column) < cutoff_time)
        stale_count = stale_df.count()
        total_count = df.count()
        
        passed = stale_count == 0
        
        return {
            "passed": passed,
            "failure_count": stale_count,
            "details": f"Stale records: {stale_count}/{total_count}"
        }


class DataQualityValidator:
    """
    Main validator class that orchestrates all data quality checks.
    """
    
    def __init__(self, spark: SparkSession, catalog: str, schema: str):
        self.spark = spark
        self.catalog = catalog
        self.schema = schema
        self.rules: Dict[str, List[DataQualityRule]] = {}
        
        # Initialize with standard silver layer rules
        self._initialize_standard_rules()
    
    def _initialize_standard_rules(self):
        """Define standard quality rules for all silver tables."""
        
        # Standard metadata column rules (apply to all silver tables)
        metadata_rules = [
            CompletenessRule(
                columns=["record_created_at", "record_updated_at", "source_system", "load_id"],
                threshold=1.0
            ),
            ValidityRule(
                column="is_current",
                condition="is_current IS NOT NULL",
                description="is_current must not be null"
            ),
            ValidityRule(
                column="is_deleted",
                condition="is_deleted IS NOT NULL",
                description="is_deleted must not be null"
            )
        ]
        
        # Default rules for common tables
        self.rules["default"] = metadata_rules
    
    def add_rule(self, table_name: str, rule: DataQualityRule):
        """Add a custom rule for a specific table."""
        if table_name not in self.rules:
            self.rules[table_name] = []
        self.rules[table_name].append(rule)
    
    def add_table_rules(self, table_name: str):
        """Add table-specific validation rules."""
        
        if table_name == "customers_silver":
            self.rules[table_name] = self.rules.get("default", []) + [
                # Completeness checks
                CompletenessRule(columns=["customer_id", "customer_email"], threshold=1.0),
                
                # Uniqueness checks
                UniquenessRule(columns=["customer_id"]),
                
                # Validity checks
                ValidityRule(
                    column="customer_email",
                    condition="customer_email RLIKE '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,}$'",
                    description="Valid email format"
                ),
                ValidityRule(
                    column="customer_phone",
                    condition="LENGTH(customer_phone) >= 10",
                    description="Valid phone number length"
                ),
                ValidityRule(
                    column="customer_age",
                    condition="customer_age BETWEEN 0 AND 120",
                    description="Valid age range"
                ),
                
                # Consistency checks
                ConsistencyRule(
                    rule_name="customer_timestamps_consistent",
                    condition="customer_updated_at >= customer_created_at",
                    description="Updated timestamp should be >= created timestamp"
                ),
                
                # Timeliness checks
                TimelinessRule(timestamp_column="record_created_at", max_age_hours=48)
            ]
        
        elif table_name == "orders_silver":
            self.rules[table_name] = self.rules.get("default", []) + [
                # Completeness checks
                CompletenessRule(columns=["order_id", "customer_id", "order_date"], threshold=1.0),
                
                # Uniqueness checks
                UniquenessRule(columns=["order_id"]),
                
                # Validity checks
                ValidityRule(
                    column="order_total_amount",
                    condition="order_total_amount > 0",
                    description="Order total must be positive"
                ),
                ValidityRule(
                    column="order_status",
                    condition="order_status IN ('PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED')",
                    description="Valid order status"
                ),
                
                # Consistency checks
                ConsistencyRule(
                    rule_name="order_amounts_consistent",
                    condition="order_total_amount = order_subtotal_amount + order_tax_amount + order_shipping_amount - order_discount_amount",
                    description="Order total should equal sum of components"
                ),
                ConsistencyRule(
                    rule_name="order_dates_consistent",
                    condition="order_shipped_at IS NULL OR order_shipped_at >= order_created_at",
                    description="Ship date should be >= order date"
                )
            ]
    
    def validate_table(self, table_name: str) -> Dict[str, Any]:
        """
        Execute all validation rules for a table.
        
        Returns:
            Dictionary with validation results including:
            - is_valid: bool
            - rule_results: List of individual rule results
            - summary: Aggregated statistics
        """
        logger.info(f"Validating table: {self.catalog}.{self.schema}.{table_name}")
        
        # Load the table
        try:
            df = self.spark.table(f"{self.catalog}.{self.schema}.{table_name}")
        except Exception as e:
            logger.error(f"Failed to load table: {e}")
            return {
                "is_valid": False,
                "error": str(e),
                "rule_results": []
            }
        
        # Add table-specific rules if not already added
        if table_name not in self.rules:
            self.add_table_rules(table_name)
        
        # Get rules for this table
        table_rules = self.rules.get(table_name, self.rules.get("default", []))
        
        # Execute all rules
        rule_results = []
        for rule in table_rules:
            logger.info(f"Executing rule: {rule.rule_name}")
            try:
                result = rule.validate(df)
                rule_results.append({
                    "rule_name": rule.rule_name,
                    "description": rule.description,
                    "severity": rule.severity,
                    "passed": result["passed"],
                    "failure_count": result["failure_count"],
                    "details": result["details"]
                })
            except Exception as e:
                logger.error(f"Rule {rule.rule_name} failed with error: {e}")
                rule_results.append({
                    "rule_name": rule.rule_name,
                    "description": rule.description,
                    "severity": "ERROR",
                    "passed": False,
                    "failure_count": -1,
                    "details": f"Rule execution failed: {str(e)}"
                })
        
        # Calculate summary
        total_rules = len(rule_results)
        passed_rules = sum(1 for r in rule_results if r["passed"])
        failed_rules = total_rules - passed_rules
        
        # Determine overall validity
        errors = [r for r in rule_results if not r["passed"] and r["severity"] == "ERROR"]
        is_valid = len(errors) == 0
        
        summary = {
            "table_name": table_name,
            "validation_timestamp": datetime.now().isoformat(),
            "total_rules": total_rules,
            "passed_rules": passed_rules,
            "failed_rules": failed_rules,
            "error_count": len(errors),
            "warning_count": len([r for r in rule_results if not r["passed"] and r["severity"] == "WARNING"]),
            "is_valid": is_valid
        }
        
        return {
            "is_valid": is_valid,
            "rule_results": rule_results,
            "summary": summary
        }
    
    def log_quality_issues(self, validation_results: Dict[str, Any], 
                          quality_log_table: str = None):
        """
        Log quality issues to a Delta table for tracking and alerting.
        """
        if quality_log_table is None:
            quality_log_table = f"{self.catalog}.{self.schema}.data_quality_log"
        
        failed_rules = [r for r in validation_results["rule_results"] if not r["passed"]]
        
        if not failed_rules:
            logger.info("No quality issues to log")
            return
        
        # Create log records
        log_records = []
        for rule in failed_rules:
            log_records.append({
                "table_name": validation_results["summary"]["table_name"],
                "rule_name": rule["rule_name"],
                "severity": rule["severity"],
                "failure_count": rule["failure_count"],
                "details": json.dumps(rule["details"]),
                "logged_at": datetime.now()
            })
        
        # Convert to DataFrame and append to log table
        log_df = self.spark.createDataFrame(log_records)
        
        try:
            log_df.write.format("delta").mode("append").saveAsTable(quality_log_table)
            logger.info(f"Logged {len(log_records)} quality issues to {quality_log_table}")
        except Exception as e:
            logger.error(f"Failed to log quality issues: {e}")
    
    def generate_quality_report(self, validation_results: Dict[str, Any]) -> str:
        """Generate a human-readable quality report."""
        
        summary = validation_results["summary"]
        report = f"""
        ========================================
        DATA QUALITY VALIDATION REPORT
        ========================================
        
        Table: {summary['table_name']}
        Timestamp: {summary['validation_timestamp']}
        
        Overall Status: {'✅ PASSED' if summary['is_valid'] else '❌ FAILED'}
        
        Summary:
        - Total Rules: {summary['total_rules']}
        - Passed: {summary['passed_rules']}
        - Failed: {summary['failed_rules']}
        - Errors: {summary['error_count']}
        - Warnings: {summary['warning_count']}
        
        Failed Rules:
        """
        
        failed_rules = [r for r in validation_results["rule_results"] if not r["passed"]]
        
        if not failed_rules:
            report += "\n        None - All rules passed! 🎉\n"
        else:
            for rule in failed_rules:
                report += f"\n        [{rule['severity']}] {rule['rule_name']}\n"
                report += f"        Description: {rule['description']}\n"
                report += f"        Failures: {rule['failure_count']}\n"
                report += f"        Details: {rule['details']}\n"
        
        report += "\n        ========================================\n"
        
        return report


# Example usage
if __name__ == "__main__":
    # Initialize Spark
    spark = SparkSession.builder.appName("DataQualityValidation").getOrCreate()
    
    # Create validator
    validator = DataQualityValidator(
        spark=spark,
        catalog="dev_catalog",
        schema="silver"
    )
    
    # Validate a table
    results = validator.validate_table("customers_silver")
    
    # Print report
    print(validator.generate_quality_report(results))
    
    # Log issues if validation failed
    if not results["is_valid"]:
        validator.log_quality_issues(results)

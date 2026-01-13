#!/usr/bin/env python3
"""
Data Quality Report Generator for Silver Layer
----------------------------------------------
Generates comprehensive data quality reports for silver layer tables.

Usage:
    python generate_dq_report.py --env dev
    python generate_dq_report.py --table customers_silver --output html
"""

import argparse
import sys
import json
from datetime import datetime
from typing import Dict, List, Any
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataQualityReporter:
    """Generate data quality reports for silver layer tables."""
    
    def __init__(self, spark: SparkSession, catalog: str, schema: str):
        self.spark = spark
        self.catalog = catalog
        self.schema = schema
    
    def generate_table_report(self, table_name: str) -> Dict[str, Any]:
        """Generate data quality report for a single table."""
        logger.info(f"Generating DQ report for {self.catalog}.{self.schema}.{table_name}")
        
        table_path = f"{self.catalog}.{self.schema}.{table_name}"
        df = self.spark.table(table_path)
        
        report = {
            "table_name": table_name,
            "report_timestamp": datetime.now().isoformat(),
            "metrics": {}
        }
        
        # Basic metrics
        total_records = df.count()
        report["metrics"]["total_records"] = total_records
        report["metrics"]["column_count"] = len(df.columns)
        
        # Completeness metrics
        completeness = {}
        for col in df.columns:
            null_count = df.filter(F.col(col).isNull()).count()
            completeness[col] = {
                "null_count": null_count,
                "completeness_pct": round((total_records - null_count) / total_records * 100, 2) if total_records > 0 else 0
            }
        report["metrics"]["completeness"] = completeness
        
        # Uniqueness metrics (for ID columns)
        uniqueness = {}
        id_columns = [col for col in df.columns if col.endswith('_id')]
        for col in id_columns:
            distinct_count = df.select(col).distinct().count()
            uniqueness[col] = {
                "distinct_count": distinct_count,
                "uniqueness_pct": round(distinct_count / total_records * 100, 2) if total_records > 0 else 0,
                "duplicate_count": total_records - distinct_count
            }
        report["metrics"]["uniqueness"] = uniqueness
        
        # Quality score
        avg_completeness = sum(c["completeness_pct"] for c in completeness.values()) / len(completeness) if completeness else 0
        report["metrics"]["overall_quality_score"] = round(avg_completeness, 2)
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """Print formatted report to console."""
        print("\n" + "=" * 80)
        print(f"DATA QUALITY REPORT - {report['table_name']}")
        print("=" * 80)
        print(f"Generated: {report['report_timestamp']}")
        print(f"\n📊 Overall Quality Score: {report['metrics']['overall_quality_score']}%")
        print(f"📈 Total Records: {report['metrics']['total_records']:,}")
        print(f"📋 Columns: {report['metrics']['column_count']}")
        
        # Completeness
        print("\n" + "-" * 80)
        print("COMPLETENESS (Top 10 Issues)")
        print("-" * 80)
        completeness_sorted = sorted(
            report['metrics']['completeness'].items(),
            key=lambda x: x[1]['completeness_pct']
        )[:10]
        
        for col, metrics in completeness_sorted:
            status = "✅" if metrics['completeness_pct'] == 100 else "⚠️" if metrics['completeness_pct'] >= 95 else "❌"
            print(f"{status} {col}: {metrics['completeness_pct']}% ({metrics['null_count']:,} nulls)")
        
        # Uniqueness
        if report['metrics']['uniqueness']:
            print("\n" + "-" * 80)
            print("UNIQUENESS (ID Columns)")
            print("-" * 80)
            for col, metrics in report['metrics']['uniqueness'].items():
                status = "✅" if metrics['duplicate_count'] == 0 else "❌"
                print(f"{status} {col}: {metrics['uniqueness_pct']}% unique ({metrics['duplicate_count']:,} duplicates)")
        
        print("\n" + "=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Generate data quality reports")
    parser.add_argument("--env", choices=["dev", "staging", "prod"], default="dev")
    parser.add_argument("--catalog", help="Unity Catalog name")
    parser.add_argument("--schema", default="silver")
    parser.add_argument("--table", help="Specific table to report on")
    parser.add_argument("--output", choices=["console", "json", "html"], default="console")
    
    args = parser.parse_args()
    
    if args.catalog:
        catalog = args.catalog
    else:
        catalog_map = {"dev": "dev_catalog", "staging": "staging_catalog", "prod": "prod_catalog"}
        catalog = catalog_map.get(args.env, "dev_catalog")
    
    spark = SparkSession.builder.appName("DQReporter").getOrCreate()
    
    reporter = DataQualityReporter(spark, catalog, args.schema)
    
    if args.table:
        report = reporter.generate_table_report(args.table)
        reporter.print_report(report)
        
        if args.output == "json":
            filename = f"dq_report_{args.table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {filename}")
    
    sys.exit(0)


if __name__ == "__main__":
    main()

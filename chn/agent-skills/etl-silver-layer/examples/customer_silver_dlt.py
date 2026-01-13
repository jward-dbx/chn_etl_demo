# Databricks notebook source
# MAGIC %md
# MAGIC # Customer Silver Layer - Delta Live Tables
# MAGIC 
# MAGIC This notebook defines a Delta Live Tables (DLT) pipeline for transforming customer data
# MAGIC from bronze to silver layer with:
# MAGIC - Standardized column naming
# MAGIC - Data quality expectations
# MAGIC - SCD Type 2 tracking
# MAGIC - Comprehensive metadata

# COMMAND ----------

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import *

# COMMAND ----------

# Pipeline configuration from bundle
source_catalog = spark.conf.get("source.catalog", "dev_catalog")
source_schema = spark.conf.get("source.schema", "bronze")
environment = spark.conf.get("pipeline.environment", "dev")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze to Silver: Customer Data

# COMMAND ----------

@dlt.table(
    name="customers_silver",
    comment="Silver layer customer data with standardized transformations and data quality",
    table_properties={
        "quality": "silver",
        "layer": "silver",
        "domain": "customer",
        "pipelines.autoOptimize.managed": "true",
        "delta.enableChangeDataFeed": "true"
    },
    partition_cols=["customer_state"],
    # Data quality expectations
    expect_or_fail={
        "valid_customer_id": "customer_id IS NOT NULL",
        "valid_email_format": "customer_email RLIKE '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\\\.[a-zA-Z]{2,}$'"
    },
    expect_or_drop={
        "valid_phone_length": "LENGTH(customer_phone) >= 10"
    },
    expect={
        "has_name": "customer_first_name IS NOT NULL AND customer_last_name IS NOT NULL",
        "has_address": "customer_address_line1 IS NOT NULL"
    }
)
def customers_silver():
    """
    Transform bronze customer data to silver layer with standardized schema.
    
    Transformations:
    - Standardize column names to snake_case with entity prefix
    - Clean and format data (uppercase names, lowercase emails, clean phones)
    - Add derived columns (age, full name, boolean flags)
    - Add metadata columns (timestamps, source, lineage)
    - Implement SCD Type 2 tracking columns
    """
    return (
        dlt.read_stream(f"{source_catalog}.{source_schema}.customers")
        .select(
            # Business Key
            F.col("customer_id"),
            
            # Customer Name (standardized to uppercase, trimmed)
            F.trim(F.upper(F.col("first_name"))).alias("customer_first_name"),
            F.trim(F.upper(F.col("last_name"))).alias("customer_last_name"),
            F.concat_ws(" ", 
                F.trim(F.upper(F.col("first_name"))),
                F.trim(F.upper(F.col("last_name")))
            ).alias("customer_full_name"),
            
            # Contact Information (standardized formats)
            F.lower(F.trim(F.col("email"))).alias("customer_email"),
            F.regexp_replace(F.col("phone"), "[^0-9]", "").alias("customer_phone"),
            
            # Personal Information
            F.to_timestamp(F.col("date_of_birth"), "yyyy-MM-dd").alias("customer_date_of_birth"),
            (F.year(F.current_date()) - F.year(F.to_timestamp(F.col("date_of_birth"), "yyyy-MM-dd"))).alias("customer_age"),
            
            # Address Information (standardized)
            F.trim(F.col("address_line1")).alias("customer_address_line1"),
            F.trim(F.col("address_line2")).alias("customer_address_line2"),
            F.trim(F.col("city")).alias("customer_city"),
            F.upper(F.trim(F.col("state"))).alias("customer_state"),
            F.col("zip_code").alias("customer_zip_code"),
            F.upper(F.trim(F.col("country"))).alias("customer_country"),
            
            # Boolean Flags (following is_/has_ convention)
            F.col("active").cast("boolean").alias("is_active"),
            F.col("email_verified").cast("boolean").alias("is_email_verified"),
            F.when(F.col("address_line1").isNotNull(), True).otherwise(False).alias("has_address"),
            F.when(
                F.col("phone").isNotNull() & 
                (F.length(F.regexp_replace(F.col("phone"), "[^0-9]", "")) >= 10),
                True
            ).otherwise(False).alias("has_valid_phone"),
            
            # Business Timestamps
            F.to_timestamp(F.col("created_at")).alias("customer_created_at"),
            F.to_timestamp(F.col("updated_at")).alias("customer_updated_at"),
            
            # SCD Type 2 Columns
            F.current_timestamp().alias("effective_start_date"),
            F.lit(None).cast(TimestampType()).alias("effective_end_date"),
            
            # Standard Metadata Columns (REQUIRED for all silver tables)
            F.current_timestamp().alias("record_created_at"),
            F.current_timestamp().alias("record_updated_at"),
            F.lit("source_crm").alias("source_system"),
            F.lit(environment).alias("load_id"),
            F.lit(True).alias("is_current"),
            F.lit(False).alias("is_deleted")
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver to Silver: Customer Segmentation

# COMMAND ----------

@dlt.table(
    name="customers_silver_enriched",
    comment="Enriched customer data with segmentation and scoring",
    table_properties={
        "quality": "silver",
        "layer": "silver_enriched",
        "domain": "customer"
    }
)
def customers_silver_enriched():
    """
    Enrich silver customer data with additional business logic.
    
    Enrichments:
    - Customer lifetime value segment
    - Age group classification
    - Geographic region mapping
    - Contact quality score
    """
    return (
        dlt.read("customers_silver")
        .withColumn(
            "customer_age_group",
            F.when(F.col("customer_age") < 25, "18-24")
             .when(F.col("customer_age") < 35, "25-34")
             .when(F.col("customer_age") < 45, "35-44")
             .when(F.col("customer_age") < 55, "45-54")
             .when(F.col("customer_age") < 65, "55-64")
             .otherwise("65+")
        )
        .withColumn(
            "customer_region",
            F.when(F.col("customer_state").isin("CA", "OR", "WA"), "West")
             .when(F.col("customer_state").isin("NY", "NJ", "PA", "MA"), "Northeast")
             .when(F.col("customer_state").isin("TX", "FL", "GA", "NC"), "South")
             .otherwise("Midwest")
        )
        .withColumn(
            "customer_contact_quality_score",
            (F.when(F.col("is_email_verified"), 30).otherwise(0) +
             F.when(F.col("has_valid_phone"), 30).otherwise(0) +
             F.when(F.col("has_address"), 40).otherwise(0))
        )
        .withColumn(
            "customer_profile_completeness",
            F.when(F.col("customer_contact_quality_score") >= 90, "Complete")
             .when(F.col("customer_contact_quality_score") >= 60, "Partial")
             .otherwise("Incomplete")
        )
        .withColumn("record_updated_at", F.current_timestamp())
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Monitoring

# COMMAND ----------

@dlt.table(
    name="customers_silver_quality_metrics",
    comment="Data quality metrics and statistics for customer silver layer"
)
def customers_silver_quality_metrics():
    """
    Generate data quality metrics for monitoring and alerting.
    """
    customer_df = dlt.read("customers_silver")
    
    return customer_df.agg(
        F.lit("customers_silver").alias("table_name"),
        F.count("*").alias("total_records"),
        F.countDistinct("customer_id").alias("unique_customers"),
        F.sum(F.when(F.col("customer_email").isNull(), 1).otherwise(0)).alias("null_emails_count"),
        F.sum(F.when(F.col("customer_phone").isNull(), 1).otherwise(0)).alias("null_phones_count"),
        F.sum(F.when(F.col("is_active") == True, 1).otherwise(0)).alias("active_customers_count"),
        F.sum(F.when(F.col("is_email_verified") == True, 1).otherwise(0)).alias("verified_emails_count"),
        F.sum(F.when(F.col("has_address") == True, 1).otherwise(0)).alias("has_address_count"),
        F.avg("customer_age").alias("avg_customer_age"),
        F.current_timestamp().alias("metrics_generated_at")
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Apply SCD Type 2 Logic

# COMMAND ----------

dlt.create_streaming_table(
    name="customers_silver_changes",
    comment="Change data capture for customer silver layer"
)

dlt.apply_changes(
    target="customers_silver_changes",
    source="customers_silver",
    keys=["customer_id"],
    sequence_by=F.col("customer_updated_at"),
    stored_as_scd_type=2,
    track_history_column_list=[
        "customer_email",
        "customer_phone",
        "customer_address_line1",
        "customer_city",
        "customer_state",
        "customer_zip_code"
    ],
    track_history_except_column_list=["record_updated_at"]
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Usage Examples
# MAGIC 
# MAGIC ```python
# MAGIC # Query the silver table
# MAGIC customers = spark.table("customers_silver")
# MAGIC 
# MAGIC # Get only current records
# MAGIC current_customers = customers.filter("is_current = true AND is_deleted = false")
# MAGIC 
# MAGIC # Get historical changes for a customer
# MAGIC customer_history = customers.filter("customer_id = '12345'").orderBy("effective_start_date")
# MAGIC 
# MAGIC # Check data quality metrics
# MAGIC quality_metrics = spark.table("customers_silver_quality_metrics")
# MAGIC quality_metrics.display()
# MAGIC ```

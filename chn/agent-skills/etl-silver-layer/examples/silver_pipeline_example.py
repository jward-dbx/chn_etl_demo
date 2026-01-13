# Silver Layer Pipeline Example - PySpark Implementation
# This example demonstrates a complete silver layer transformation pipeline
# with standardized column naming, data quality checks, and SCD Type 2 logic

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, BooleanType, DecimalType, IntegerType
from delta.tables import DeltaTable
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SilverLayerTransformer:
    """
    Base class for silver layer transformations following enterprise standards.
    """
    
    def __init__(self, spark: SparkSession, source_catalog: str, source_schema: str, 
                 target_catalog: str, target_schema: str, load_id: str):
        self.spark = spark
        self.source_catalog = source_catalog
        self.source_schema = source_schema
        self.target_catalog = target_catalog
        self.target_schema = target_schema
        self.load_id = load_id
        self.current_timestamp = F.current_timestamp()
        
    def add_metadata_columns(self, df: DataFrame, source_system: str) -> DataFrame:
        """
        Add standard metadata columns to every silver layer table.
        These columns are REQUIRED for all silver tables.
        """
        return df.withColumn("record_created_at", self.current_timestamp) \
                 .withColumn("record_updated_at", self.current_timestamp) \
                 .withColumn("source_system", F.lit(source_system)) \
                 .withColumn("load_id", F.lit(self.load_id)) \
                 .withColumn("is_current", F.lit(True)) \
                 .withColumn("is_deleted", F.lit(False))
    
    def standardize_column_names(self, df: DataFrame) -> DataFrame:
        """
        Convert all column names to snake_case following silver layer standards.
        """
        for col in df.columns:
            # Convert camelCase or PascalCase to snake_case
            snake_case_col = ''.join(['_' + c.lower() if c.isupper() else c for c in col]).lstrip('_')
            df = df.withColumnRenamed(col, snake_case_col)
        return df
    
    def apply_data_quality_checks(self, df: DataFrame, table_name: str, 
                                  required_columns: list, unique_columns: list = None) -> DataFrame:
        """
        Apply standard data quality checks and log violations.
        """
        # Check for required columns
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in {table_name}")
        
        # Count nulls in required columns
        null_counts = df.select([F.sum(F.col(c).isNull().cast("int")).alias(c) for c in required_columns]).collect()[0]
        
        for col in required_columns:
            null_count = null_counts[col]
            if null_count > 0:
                logger.warning(f"Table {table_name}: {null_count} null values found in required column '{col}'")
        
        # Check for duplicates in unique columns
        if unique_columns:
            total_count = df.count()
            distinct_count = df.select(unique_columns).distinct().count()
            if total_count != distinct_count:
                duplicate_count = total_count - distinct_count
                logger.warning(f"Table {table_name}: {duplicate_count} duplicate records found on {unique_columns}")
        
        return df


class CustomerSilverTransformer(SilverLayerTransformer):
    """
    Transformer for customer data from bronze to silver layer.
    Implements standardized naming, SCD Type 2, and data quality checks.
    """
    
    def get_silver_schema(self) -> StructType:
        """
        Define the standardized silver layer schema for customers.
        All column names follow snake_case convention with entity prefix.
        """
        return StructType([
            # Business Keys
            StructField("customer_id", StringType(), False),
            
            # Customer Attributes
            StructField("customer_first_name", StringType(), True),
            StructField("customer_last_name", StringType(), True),
            StructField("customer_email", StringType(), True),
            StructField("customer_phone", StringType(), True),
            StructField("customer_date_of_birth", TimestampType(), True),
            
            # Address Information
            StructField("customer_address_line1", StringType(), True),
            StructField("customer_address_line2", StringType(), True),
            StructField("customer_city", StringType(), True),
            StructField("customer_state", StringType(), True),
            StructField("customer_zip_code", StringType(), True),
            StructField("customer_country", StringType(), True),
            
            # Status and Flags
            StructField("is_active", BooleanType(), True),
            StructField("is_email_verified", BooleanType(), True),
            StructField("has_address", BooleanType(), True),
            
            # Business Dates
            StructField("customer_created_at", TimestampType(), True),
            StructField("customer_updated_at", TimestampType(), True),
            
            # SCD Type 2 Columns
            StructField("effective_start_date", TimestampType(), False),
            StructField("effective_end_date", TimestampType(), True),
            
            # Standard Metadata Columns (REQUIRED)
            StructField("record_created_at", TimestampType(), False),
            StructField("record_updated_at", TimestampType(), False),
            StructField("source_system", StringType(), False),
            StructField("load_id", StringType(), False),
            StructField("is_current", BooleanType(), False),
            StructField("is_deleted", BooleanType(), False),
        ])
    
    def transform(self) -> DataFrame:
        """
        Main transformation logic from bronze to silver for customers.
        """
        logger.info(f"Starting customer silver transformation with load_id: {self.load_id}")
        
        # Read from bronze layer
        bronze_table = f"{self.source_catalog}.{self.source_schema}.customers"
        logger.info(f"Reading from bronze table: {bronze_table}")
        bronze_df = self.spark.table(bronze_table)
        
        # Step 1: Standardize column names
        df = self.standardize_column_names(bronze_df)
        
        # Step 2: Apply business transformations
        df = df.select(
            F.col("customer_id"),
            
            # Clean and standardize names
            F.trim(F.upper(F.col("first_name"))).alias("customer_first_name"),
            F.trim(F.upper(F.col("last_name"))).alias("customer_last_name"),
            
            # Standardize email to lowercase
            F.lower(F.trim(F.col("email"))).alias("customer_email"),
            
            # Standardize phone format (remove special characters)
            F.regexp_replace(F.col("phone"), "[^0-9]", "").alias("customer_phone"),
            
            # Parse date of birth
            F.to_timestamp(F.col("date_of_birth"), "yyyy-MM-dd").alias("customer_date_of_birth"),
            
            # Address fields
            F.trim(F.col("address_line1")).alias("customer_address_line1"),
            F.trim(F.col("address_line2")).alias("customer_address_line2"),
            F.trim(F.col("city")).alias("customer_city"),
            F.upper(F.trim(F.col("state"))).alias("customer_state"),
            F.col("zip_code").alias("customer_zip_code"),
            F.upper(F.trim(F.col("country"))).alias("customer_country"),
            
            # Boolean flags (standardized)
            F.col("active").cast("boolean").alias("is_active"),
            F.col("email_verified").cast("boolean").alias("is_email_verified"),
            F.when(F.col("address_line1").isNotNull(), True).otherwise(False).alias("has_address"),
            
            # Business timestamps
            F.to_timestamp(F.col("created_at")).alias("customer_created_at"),
            F.to_timestamp(F.col("updated_at")).alias("customer_updated_at"),
        )
        
        # Step 3: Add SCD Type 2 columns
        df = df.withColumn("effective_start_date", self.current_timestamp) \
               .withColumn("effective_end_date", F.lit(None).cast(TimestampType()))
        
        # Step 4: Add standard metadata columns
        df = self.add_metadata_columns(df, source_system="source_crm")
        
        # Step 5: Apply data quality checks
        required_columns = ["customer_id", "customer_email"]
        df = self.apply_data_quality_checks(df, "customers", required_columns, ["customer_id"])
        
        # Step 6: Filter out records that fail quality checks
        df = df.filter(
            F.col("customer_id").isNotNull() &
            F.col("customer_email").isNotNull() &
            F.col("customer_email").rlike("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")
        )
        
        logger.info(f"Transformation complete. Record count: {df.count()}")
        
        return df
    
    def upsert_to_silver(self, transformed_df: DataFrame):
        """
        Upsert data to silver layer using Delta merge with SCD Type 2 logic.
        """
        target_table = f"{self.target_catalog}.{self.target_schema}.customers"
        logger.info(f"Upserting to silver table: {target_table}")
        
        # Check if table exists
        if not self.spark.catalog.tableExists(target_table):
            logger.info(f"Creating new table: {target_table}")
            transformed_df.write.format("delta") \
                .mode("overwrite") \
                .option("delta.enableChangeDataFeed", "true") \
                .partitionBy("customer_state") \
                .saveAsTable(target_table)
            
            # Optimize table after creation
            self.spark.sql(f"OPTIMIZE {target_table} ZORDER BY (customer_id)")
            logger.info("Table created and optimized")
        else:
            # Perform SCD Type 2 merge
            delta_table = DeltaTable.forName(self.spark, target_table)
            
            # Merge logic: Update existing, insert new, handle deletes
            delta_table.alias("target").merge(
                transformed_df.alias("source"),
                "target.customer_id = source.customer_id AND target.is_current = true"
            ).whenMatchedUpdate(
                condition="target.customer_email != source.customer_email OR " +
                         "target.customer_phone != source.customer_phone OR " +
                         "target.customer_address_line1 != source.customer_address_line1",
                set={
                    "is_current": "false",
                    "effective_end_date": "source.effective_start_date",
                    "record_updated_at": "current_timestamp()"
                }
            ).whenNotMatchedInsert(
                values={
                    "customer_id": "source.customer_id",
                    "customer_first_name": "source.customer_first_name",
                    "customer_last_name": "source.customer_last_name",
                    "customer_email": "source.customer_email",
                    "customer_phone": "source.customer_phone",
                    "customer_date_of_birth": "source.customer_date_of_birth",
                    "customer_address_line1": "source.customer_address_line1",
                    "customer_address_line2": "source.customer_address_line2",
                    "customer_city": "source.customer_city",
                    "customer_state": "source.customer_state",
                    "customer_zip_code": "source.customer_zip_code",
                    "customer_country": "source.customer_country",
                    "is_active": "source.is_active",
                    "is_email_verified": "source.is_email_verified",
                    "has_address": "source.has_address",
                    "customer_created_at": "source.customer_created_at",
                    "customer_updated_at": "source.customer_updated_at",
                    "effective_start_date": "source.effective_start_date",
                    "effective_end_date": "source.effective_end_date",
                    "record_created_at": "source.record_created_at",
                    "record_updated_at": "source.record_updated_at",
                    "source_system": "source.source_system",
                    "load_id": "source.load_id",
                    "is_current": "source.is_current",
                    "is_deleted": "source.is_deleted"
                }
            ).execute()
            
            logger.info("Merge completed successfully")


def main():
    """
    Main entry point for the silver layer pipeline.
    """
    # Initialize Spark session
    spark = SparkSession.builder \
        .appName("Customer Silver Layer ETL") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()
    
    # Configuration (typically passed as arguments)
    source_catalog = "dev_catalog"
    source_schema = "bronze"
    target_catalog = "dev_catalog"
    target_schema = "silver"
    load_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Execute transformation
    transformer = CustomerSilverTransformer(
        spark, source_catalog, source_schema, target_catalog, target_schema, load_id
    )
    
    transformed_df = transformer.transform()
    transformer.upsert_to_silver(transformed_df)
    
    logger.info("Silver layer pipeline completed successfully")
    spark.stop()


if __name__ == "__main__":
    main()

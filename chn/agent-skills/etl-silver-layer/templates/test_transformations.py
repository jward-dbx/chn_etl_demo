"""
Unit Test Template for Silver Layer Transformations
---------------------------------------------------
This template provides comprehensive unit testing patterns for silver layer ETL pipelines
using pytest and pytest-spark.

Installation:
    pip install pytest pytest-spark chispa

Usage:
    pytest test_transformations.py -v
    pytest test_transformations.py::TestCustomerTransformations -v
"""

import pytest
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import *
from datetime import datetime, date
from decimal import Decimal
from chispa.dataframe_comparer import assert_df_equality
from typing import List


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def spark():
    """Create a Spark session for testing."""
    spark = SparkSession.builder \
        .appName("SilverLayerUnitTests") \
        .master("local[2]") \
        .config("spark.sql.shuffle.partitions", "2") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()
    
    yield spark
    
    spark.stop()


@pytest.fixture
def sample_bronze_customers(spark):
    """Create sample bronze customer data for testing."""
    schema = StructType([
        StructField("customer_id", StringType(), True),
        StructField("first_name", StringType(), True),
        StructField("last_name", StringType(), True),
        StructField("email", StringType(), True),
        StructField("phone", StringType(), True),
        StructField("date_of_birth", StringType(), True),
        StructField("address_line1", StringType(), True),
        StructField("address_line2", StringType(), True),
        StructField("city", StringType(), True),
        StructField("state", StringType(), True),
        StructField("zip_code", StringType(), True),
        StructField("country", StringType(), True),
        StructField("active", BooleanType(), True),
        StructField("email_verified", BooleanType(), True),
        StructField("created_at", StringType(), True),
        StructField("updated_at", StringType(), True),
    ])
    
    data = [
        ("C001", "john", "doe", "JOHN.DOE@EXAMPLE.COM", "(555) 123-4567", "1985-03-15",
         "123 Main St", "Apt 4B", "New York", "ny", "10001", "usa", True, True,
         "2023-01-15 10:00:00", "2023-06-20 14:30:00"),
        ("C002", "  Jane  ", "  Smith  ", "jane.smith@example.com  ", "555-987-6543", "1990-07-22",
         "456 Oak Ave", None, "Los Angeles", "CA", "90001", "USA", True, False,
         "2023-02-20 11:00:00", "2023-06-21 09:15:00"),
        ("C003", "Bob", "Johnson", "bob@example.com", "5559876543", "1978-11-30",
         None, None, "Chicago", "IL", "60601", "USA", False, True,
         "2023-03-10 08:00:00", "2023-03-10 08:00:00"),
    ]
    
    return spark.createDataFrame(data, schema)


@pytest.fixture
def expected_silver_customers_schema():
    """Define the expected silver layer schema for customers."""
    return StructType([
        StructField("customer_id", StringType(), False),
        StructField("customer_first_name", StringType(), True),
        StructField("customer_last_name", StringType(), True),
        StructField("customer_full_name", StringType(), True),
        StructField("customer_email", StringType(), True),
        StructField("customer_phone", StringType(), True),
        StructField("customer_date_of_birth", TimestampType(), True),
        StructField("customer_age", IntegerType(), True),
        StructField("customer_address_line1", StringType(), True),
        StructField("customer_address_line2", StringType(), True),
        StructField("customer_city", StringType(), True),
        StructField("customer_state", StringType(), True),
        StructField("customer_zip_code", StringType(), True),
        StructField("customer_country", StringType(), True),
        StructField("is_active", BooleanType(), True),
        StructField("is_email_verified", BooleanType(), True),
        StructField("has_address", BooleanType(), True),
        StructField("has_valid_phone", BooleanType(), True),
        StructField("customer_created_at", TimestampType(), True),
        StructField("customer_updated_at", TimestampType(), True),
        StructField("effective_start_date", TimestampType(), False),
        StructField("effective_end_date", TimestampType(), True),
        StructField("record_created_at", TimestampType(), False),
        StructField("record_updated_at", TimestampType(), False),
        StructField("source_system", StringType(), False),
        StructField("load_id", StringType(), False),
        StructField("is_current", BooleanType(), False),
        StructField("is_deleted", BooleanType(), False),
    ])


# ============================================================================
# Transformation Functions (these would typically be imported)
# ============================================================================

def standardize_column_names(df: DataFrame) -> DataFrame:
    """Convert all column names to snake_case."""
    for col in df.columns:
        snake_case_col = ''.join(['_' + c.lower() if c.isupper() else c for c in col]).lstrip('_')
        df = df.withColumnRenamed(col, snake_case_col)
    return df


def transform_customer_to_silver(df: DataFrame, load_id: str) -> DataFrame:
    """Transform bronze customer data to silver layer."""
    return df.select(
        F.col("customer_id"),
        
        # Standardize names
        F.trim(F.upper(F.col("first_name"))).alias("customer_first_name"),
        F.trim(F.upper(F.col("last_name"))).alias("customer_last_name"),
        F.concat_ws(" ", 
            F.trim(F.upper(F.col("first_name"))),
            F.trim(F.upper(F.col("last_name")))
        ).alias("customer_full_name"),
        
        # Standardize contact info
        F.lower(F.trim(F.col("email"))).alias("customer_email"),
        F.regexp_replace(F.col("phone"), "[^0-9]", "").alias("customer_phone"),
        
        # Parse dates
        F.to_timestamp(F.col("date_of_birth"), "yyyy-MM-dd").alias("customer_date_of_birth"),
        (F.year(F.current_date()) - F.year(F.to_timestamp(F.col("date_of_birth"), "yyyy-MM-dd"))).alias("customer_age"),
        
        # Standardize address
        F.trim(F.col("address_line1")).alias("customer_address_line1"),
        F.trim(F.col("address_line2")).alias("customer_address_line2"),
        F.trim(F.col("city")).alias("customer_city"),
        F.upper(F.trim(F.col("state"))).alias("customer_state"),
        F.col("zip_code").alias("customer_zip_code"),
        F.upper(F.trim(F.col("country"))).alias("customer_country"),
        
        # Boolean flags
        F.col("active").cast("boolean").alias("is_active"),
        F.col("email_verified").cast("boolean").alias("is_email_verified"),
        F.when(F.col("address_line1").isNotNull(), True).otherwise(False).alias("has_address"),
        F.when(
            F.col("phone").isNotNull() & 
            (F.length(F.regexp_replace(F.col("phone"), "[^0-9]", "")) >= 10),
            True
        ).otherwise(False).alias("has_valid_phone"),
        
        # Business timestamps
        F.to_timestamp(F.col("created_at")).alias("customer_created_at"),
        F.to_timestamp(F.col("updated_at")).alias("customer_updated_at"),
        
        # SCD Type 2 columns
        F.current_timestamp().alias("effective_start_date"),
        F.lit(None).cast(TimestampType()).alias("effective_end_date"),
        
        # Metadata columns
        F.current_timestamp().alias("record_created_at"),
        F.current_timestamp().alias("record_updated_at"),
        F.lit("source_crm").alias("source_system"),
        F.lit(load_id).alias("load_id"),
        F.lit(True).alias("is_current"),
        F.lit(False).alias("is_deleted")
    )


# ============================================================================
# Test Classes
# ============================================================================

class TestColumnNamingStandards:
    """Test that column naming conventions are enforced."""
    
    def test_column_names_are_snake_case(self, spark, sample_bronze_customers):
        """All column names should be in snake_case format."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        for col in df.columns:
            # Check that column name contains no uppercase letters
            assert col == col.lower(), f"Column '{col}' is not in snake_case"
            
            # Check that column name doesn't start with underscore
            assert not col.startswith('_'), f"Column '{col}' starts with underscore"
    
    def test_customer_columns_have_entity_prefix(self, spark, sample_bronze_customers):
        """Customer entity columns should have 'customer_' prefix."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        entity_columns = [
            "customer_first_name", "customer_last_name", "customer_email", 
            "customer_phone", "customer_age", "customer_address_line1"
        ]
        
        for col in entity_columns:
            assert col in df.columns, f"Expected column '{col}' not found"
    
    def test_boolean_columns_have_correct_prefix(self, spark, sample_bronze_customers):
        """Boolean columns should start with 'is_' or 'has_'."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        boolean_columns = [col for col, dtype in df.dtypes if dtype == "boolean"]
        
        for col in boolean_columns:
            assert col.startswith('is_') or col.startswith('has_'), \
                f"Boolean column '{col}' should start with 'is_' or 'has_'"


class TestDataStandardization:
    """Test data standardization transformations."""
    
    def test_names_are_uppercase_and_trimmed(self, spark, sample_bronze_customers):
        """Names should be converted to uppercase and trimmed."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        result = df.select("customer_first_name", "customer_last_name").collect()
        
        assert result[0]["customer_first_name"] == "JOHN"
        assert result[1]["customer_first_name"] == "JANE"  # Should trim spaces
        assert result[1]["customer_last_name"] == "SMITH"  # Should trim spaces
    
    def test_email_is_lowercase_and_trimmed(self, spark, sample_bronze_customers):
        """Email addresses should be lowercase and trimmed."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        result = df.select("customer_email").collect()
        
        assert result[0]["customer_email"] == "john.doe@example.com"
        assert result[1]["customer_email"] == "jane.smith@example.com"  # Should trim
    
    def test_phone_numbers_contain_only_digits(self, spark, sample_bronze_customers):
        """Phone numbers should contain only numeric digits."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        result = df.select("customer_phone").collect()
        
        for row in result:
            phone = row["customer_phone"]
            if phone:
                assert phone.isdigit(), f"Phone '{phone}' contains non-digit characters"
                assert len(phone) == 10, f"Phone '{phone}' should have 10 digits"
    
    def test_state_codes_are_uppercase(self, spark, sample_bronze_customers):
        """State codes should be uppercase."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        result = df.select("customer_state").collect()
        
        assert result[0]["customer_state"] == "NY"  # Should convert 'ny' to 'NY'
        assert result[1]["customer_state"] == "CA"


class TestDerivedColumns:
    """Test derived column calculations."""
    
    def test_full_name_concatenation(self, spark, sample_bronze_customers):
        """Full name should be concatenation of first and last name."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        result = df.select("customer_first_name", "customer_last_name", "customer_full_name").collect()
        
        for row in result:
            expected_full_name = f"{row['customer_first_name']} {row['customer_last_name']}"
            assert row["customer_full_name"] == expected_full_name
    
    def test_age_calculation(self, spark, sample_bronze_customers):
        """Age should be calculated correctly from date of birth."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        result = df.select("customer_date_of_birth", "customer_age").collect()
        
        current_year = datetime.now().year
        
        for row in result:
            if row["customer_date_of_birth"]:
                birth_year = row["customer_date_of_birth"].year
                expected_age = current_year - birth_year
                assert row["customer_age"] == expected_age
    
    def test_has_address_flag(self, spark, sample_bronze_customers):
        """has_address should be True only when address_line1 is not null."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        result = df.select("customer_address_line1", "has_address").collect()
        
        assert result[0]["has_address"] == True  # Has address
        assert result[1]["has_address"] == True  # Has address
        assert result[2]["has_address"] == False  # No address (null)
    
    def test_has_valid_phone_flag(self, spark, sample_bronze_customers):
        """has_valid_phone should be True only when phone has 10+ digits."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        result = df.select("customer_phone", "has_valid_phone").collect()
        
        for row in result:
            if row["customer_phone"] and len(row["customer_phone"]) >= 10:
                assert row["has_valid_phone"] == True
            else:
                assert row["has_valid_phone"] == False


class TestMetadataColumns:
    """Test that required metadata columns are present and valid."""
    
    def test_all_required_metadata_columns_present(self, spark, sample_bronze_customers):
        """All required metadata columns must be present."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        required_columns = [
            "record_created_at", "record_updated_at", "source_system",
            "load_id", "is_current", "is_deleted"
        ]
        
        for col in required_columns:
            assert col in df.columns, f"Required metadata column '{col}' is missing"
    
    def test_metadata_columns_have_no_nulls(self, spark, sample_bronze_customers):
        """Metadata columns should never contain null values."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        metadata_columns = [
            "record_created_at", "record_updated_at", "source_system",
            "load_id", "is_current", "is_deleted"
        ]
        
        for col in metadata_columns:
            null_count = df.filter(F.col(col).isNull()).count()
            assert null_count == 0, f"Metadata column '{col}' has {null_count} null values"
    
    def test_load_id_is_consistent(self, spark, sample_bronze_customers):
        """All records in a batch should have the same load_id."""
        load_id = "test_load_001"
        df = transform_customer_to_silver(sample_bronze_customers, load_id)
        
        distinct_load_ids = df.select("load_id").distinct().collect()
        assert len(distinct_load_ids) == 1
        assert distinct_load_ids[0]["load_id"] == load_id
    
    def test_is_current_default_value(self, spark, sample_bronze_customers):
        """is_current should default to True for new records."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        result = df.select("is_current").collect()
        for row in result:
            assert row["is_current"] == True
    
    def test_is_deleted_default_value(self, spark, sample_bronze_customers):
        """is_deleted should default to False for new records."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        result = df.select("is_deleted").collect()
        for row in result:
            assert row["is_deleted"] == False


class TestDataQuality:
    """Test data quality validations."""
    
    def test_no_null_customer_ids(self, spark, sample_bronze_customers):
        """Customer IDs should never be null in silver layer."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        null_count = df.filter(F.col("customer_id").isNull()).count()
        assert null_count == 0, f"Found {null_count} null customer IDs"
    
    def test_customer_ids_are_unique(self, spark, sample_bronze_customers):
        """Customer IDs should be unique within a load."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        total_count = df.count()
        unique_count = df.select("customer_id").distinct().count()
        
        assert total_count == unique_count, \
            f"Found duplicate customer IDs: {total_count} total, {unique_count} unique"
    
    def test_email_format_validation(self, spark):
        """Email addresses should follow valid format."""
        # Create test data with invalid emails
        data = [
            ("C001", "john@example.com"),  # Valid
            ("C002", "invalid-email"),      # Invalid
            ("C003", "jane@test.com"),      # Valid
        ]
        
        df = spark.createDataFrame(data, ["customer_id", "email"])
        
        # Apply email validation
        validated_df = df.filter(
            F.col("email").rlike("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")
        )
        
        # Should only have 2 valid emails
        assert validated_df.count() == 2


class TestSCDType2:
    """Test SCD Type 2 functionality."""
    
    def test_effective_dates_present(self, spark, sample_bronze_customers):
        """SCD Type 2 effective dates should be present."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        assert "effective_start_date" in df.columns
        assert "effective_end_date" in df.columns
    
    def test_effective_start_date_not_null(self, spark, sample_bronze_customers):
        """effective_start_date should never be null."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        null_count = df.filter(F.col("effective_start_date").isNull()).count()
        assert null_count == 0
    
    def test_effective_end_date_null_for_current_records(self, spark, sample_bronze_customers):
        """effective_end_date should be null for current records."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        current_records = df.filter(F.col("is_current") == True)
        null_end_dates = current_records.filter(F.col("effective_end_date").isNull()).count()
        
        assert null_end_dates == current_records.count(), \
            "Current records should have null effective_end_date"


class TestSchemaCompliance:
    """Test schema compliance and data types."""
    
    def test_schema_matches_expected(self, spark, sample_bronze_customers, expected_silver_customers_schema):
        """Transformed data should match expected schema."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        # Check that all expected columns are present
        expected_columns = set(expected_silver_customers_schema.fieldNames())
        actual_columns = set(df.columns)
        
        missing_columns = expected_columns - actual_columns
        extra_columns = actual_columns - expected_columns
        
        assert len(missing_columns) == 0, f"Missing columns: {missing_columns}"
        assert len(extra_columns) == 0, f"Extra columns: {extra_columns}"
    
    def test_timestamp_columns_have_correct_type(self, spark, sample_bronze_customers):
        """Timestamp columns should have TimestampType."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        timestamp_columns = [
            "customer_date_of_birth", "customer_created_at", "customer_updated_at",
            "effective_start_date", "effective_end_date", "record_created_at", "record_updated_at"
        ]
        
        schema_dict = {field.name: field.dataType for field in df.schema.fields}
        
        for col in timestamp_columns:
            assert isinstance(schema_dict[col], TimestampType), \
                f"Column '{col}' should be TimestampType, got {schema_dict[col]}"
    
    def test_boolean_columns_have_correct_type(self, spark, sample_bronze_customers):
        """Boolean columns should have BooleanType."""
        df = transform_customer_to_silver(sample_bronze_customers, "test_load_001")
        
        boolean_columns = [
            "is_active", "is_email_verified", "has_address", 
            "has_valid_phone", "is_current", "is_deleted"
        ]
        
        schema_dict = {field.name: field.dataType for field in df.schema.fields}
        
        for col in boolean_columns:
            assert isinstance(schema_dict[col], BooleanType), \
                f"Column '{col}' should be BooleanType, got {schema_dict[col]}"


# ============================================================================
# Integration Tests
# ============================================================================

class TestEndToEndTransformation:
    """Integration tests for complete transformation pipeline."""
    
    def test_complete_transformation_pipeline(self, spark, sample_bronze_customers):
        """Test complete transformation from bronze to silver."""
        # Transform
        silver_df = transform_customer_to_silver(sample_bronze_customers, "integration_test_001")
        
        # Verify record count
        assert silver_df.count() == 3
        
        # Verify no critical nulls
        critical_columns = ["customer_id", "customer_email"]
        for col in critical_columns:
            null_count = silver_df.filter(F.col(col).isNull()).count()
            assert null_count == 0, f"Critical column '{col}' has null values"
        
        # Verify data quality
        emails_with_at = silver_df.filter(F.col("customer_email").contains("@")).count()
        assert emails_with_at == silver_df.count(), "All emails should contain '@'"
    
    def test_transformation_is_idempotent(self, spark, sample_bronze_customers):
        """Transformation should produce same results when run multiple times."""
        # Run transformation twice
        result1 = transform_customer_to_silver(sample_bronze_customers, "test_001")
        result2 = transform_customer_to_silver(sample_bronze_customers, "test_001")
        
        # Exclude timestamp columns that will differ
        columns_to_compare = [col for col in result1.columns 
                            if not col.endswith('_at') and col != 'effective_start_date']
        
        # Compare results (should be identical)
        assert_df_equality(
            result1.select(*columns_to_compare),
            result2.select(*columns_to_compare),
            ignore_row_order=True
        )

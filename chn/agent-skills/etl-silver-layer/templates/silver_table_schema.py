"""
Silver Layer Table Schema Templates
------------------------------------
Reusable schema definitions for common silver layer tables following
enterprise standards for column naming, data types, and metadata.

Usage:
    from silver_table_schema import SilverSchemaBuilder
    
    schema = SilverSchemaBuilder() \
        .add_business_key("customer_id", StringType(), nullable=False) \
        .add_attribute("customer_first_name", StringType()) \
        .add_metadata_columns() \
        .build()
"""

from pyspark.sql.types import *
from typing import List, Optional


class SilverSchemaBuilder:
    """
    Builder class for creating standardized silver layer table schemas.
    Enforces naming conventions and required metadata columns.
    """
    
    def __init__(self):
        self.fields: List[StructField] = []
        self._has_metadata = False
        self._has_scd_columns = False
    
    def add_business_key(self, name: str, data_type: DataType, nullable: bool = False) -> 'SilverSchemaBuilder':
        """Add a business key column (typically non-nullable)."""
        self.fields.append(StructField(name, data_type, nullable))
        return self
    
    def add_attribute(self, name: str, data_type: DataType, nullable: bool = True) -> 'SilverSchemaBuilder':
        """Add a general attribute column."""
        self.fields.append(StructField(name, data_type, nullable))
        return self
    
    def add_boolean_flag(self, name: str, nullable: bool = False) -> 'SilverSchemaBuilder':
        """Add a boolean flag column (is_*, has_*)."""
        assert name.startswith('is_') or name.startswith('has_'), \
            f"Boolean column '{name}' should start with 'is_' or 'has_'"
        self.fields.append(StructField(name, BooleanType(), nullable))
        return self
    
    def add_amount(self, name: str, precision: int = 18, scale: int = 2, 
                   nullable: bool = True) -> 'SilverSchemaBuilder':
        """Add a monetary amount column (*_amount)."""
        assert name.endswith('_amount'), f"Amount column '{name}' should end with '_amount'"
        self.fields.append(StructField(name, DecimalType(precision, scale), nullable))
        return self
    
    def add_count(self, name: str, nullable: bool = True) -> 'SilverSchemaBuilder':
        """Add a count column (*_count)."""
        assert name.endswith('_count'), f"Count column '{name}' should end with '_count'"
        self.fields.append(StructField(name, IntegerType(), nullable))
        return self
    
    def add_rate(self, name: str, precision: int = 10, scale: int = 4,
                 nullable: bool = True) -> 'SilverSchemaBuilder':
        """Add a rate/percentage column (*_rate)."""
        assert name.endswith('_rate'), f"Rate column '{name}' should end with '_rate'"
        self.fields.append(StructField(name, DecimalType(precision, scale), nullable))
        return self
    
    def add_timestamp(self, name: str, nullable: bool = True) -> 'SilverSchemaBuilder':
        """Add a timestamp column (*_at)."""
        assert name.endswith('_at') or name.endswith('_date'), \
            f"Timestamp column '{name}' should end with '_at' or '_date'"
        self.fields.append(StructField(name, TimestampType(), nullable))
        return self
    
    def add_scd_type2_columns(self) -> 'SilverSchemaBuilder':
        """Add SCD Type 2 tracking columns."""
        self.fields.extend([
            StructField("effective_start_date", TimestampType(), False),
            StructField("effective_end_date", TimestampType(), True),
        ])
        self._has_scd_columns = True
        return self
    
    def add_metadata_columns(self, include_scd: bool = True) -> 'SilverSchemaBuilder':
        """
        Add required metadata columns for all silver layer tables.
        These columns are MANDATORY.
        """
        if include_scd and not self._has_scd_columns:
            self.add_scd_type2_columns()
        
        self.fields.extend([
            StructField("record_created_at", TimestampType(), False),
            StructField("record_updated_at", TimestampType(), False),
            StructField("source_system", StringType(), False),
            StructField("load_id", StringType(), False),
            StructField("is_current", BooleanType(), False),
            StructField("is_deleted", BooleanType(), False),
        ])
        self._has_metadata = True
        return self
    
    def build(self) -> StructType:
        """Build and return the schema."""
        if not self._has_metadata:
            raise ValueError("Schema must include metadata columns. Call add_metadata_columns().")
        
        return StructType(self.fields)


# ============================================================================
# Pre-built Schema Templates
# ============================================================================

def get_customer_silver_schema() -> StructType:
    """Standard schema for customer silver layer table."""
    return SilverSchemaBuilder() \
        .add_business_key("customer_id", StringType(), nullable=False) \
        .add_attribute("customer_first_name", StringType()) \
        .add_attribute("customer_last_name", StringType()) \
        .add_attribute("customer_full_name", StringType()) \
        .add_attribute("customer_email", StringType()) \
        .add_attribute("customer_phone", StringType()) \
        .add_timestamp("customer_date_of_birth") \
        .add_count("customer_age") \
        .add_attribute("customer_address_line1", StringType()) \
        .add_attribute("customer_address_line2", StringType()) \
        .add_attribute("customer_city", StringType()) \
        .add_attribute("customer_state", StringType()) \
        .add_attribute("customer_zip_code", StringType()) \
        .add_attribute("customer_country", StringType()) \
        .add_boolean_flag("is_active") \
        .add_boolean_flag("is_email_verified") \
        .add_boolean_flag("has_address") \
        .add_boolean_flag("has_valid_phone") \
        .add_timestamp("customer_created_at") \
        .add_timestamp("customer_updated_at") \
        .add_metadata_columns() \
        .build()


def get_orders_silver_schema() -> StructType:
    """Standard schema for orders silver layer table."""
    return SilverSchemaBuilder() \
        .add_business_key("order_id", StringType(), nullable=False) \
        .add_business_key("customer_id", StringType(), nullable=False) \
        .add_timestamp("order_date", nullable=False) \
        .add_count("order_year", nullable=False) \
        .add_count("order_month", nullable=False) \
        .add_amount("order_subtotal_amount") \
        .add_amount("order_tax_amount") \
        .add_amount("order_shipping_amount") \
        .add_amount("order_discount_amount") \
        .add_amount("order_total_amount") \
        .add_amount("order_net_amount") \
        .add_rate("order_tax_rate") \
        .add_attribute("order_status", StringType()) \
        .add_attribute("order_payment_method", StringType()) \
        .add_attribute("order_shipping_method", StringType()) \
        .add_boolean_flag("is_completed") \
        .add_boolean_flag("is_cancelled") \
        .add_boolean_flag("has_discount") \
        .add_attribute("order_shipping_address_line1", StringType()) \
        .add_attribute("order_shipping_address_line2", StringType()) \
        .add_attribute("order_shipping_city", StringType()) \
        .add_attribute("order_shipping_state", StringType()) \
        .add_attribute("order_shipping_zip_code", StringType()) \
        .add_timestamp("order_created_at") \
        .add_timestamp("order_updated_at") \
        .add_timestamp("order_shipped_at") \
        .add_timestamp("order_delivered_at") \
        .add_metadata_columns() \
        .build()


def get_products_silver_schema() -> StructType:
    """Standard schema for products silver layer table."""
    return SilverSchemaBuilder() \
        .add_business_key("product_id", StringType(), nullable=False) \
        .add_attribute("product_name", StringType(), nullable=False) \
        .add_attribute("product_sku", StringType()) \
        .add_attribute("product_description", StringType()) \
        .add_attribute("product_category", StringType()) \
        .add_attribute("product_subcategory", StringType()) \
        .add_attribute("product_brand", StringType()) \
        .add_amount("product_cost_amount") \
        .add_amount("product_list_price_amount") \
        .add_amount("product_margin_amount") \
        .add_rate("product_margin_rate") \
        .add_amount("product_weight_amount", precision=10, scale=2) \
        .add_attribute("product_weight_unit", StringType()) \
        .add_count("product_quantity_in_stock_count") \
        .add_count("product_reorder_level_count") \
        .add_boolean_flag("is_active") \
        .add_boolean_flag("is_featured") \
        .add_boolean_flag("is_in_stock") \
        .add_boolean_flag("needs_reorder") \
        .add_timestamp("product_created_at") \
        .add_timestamp("product_updated_at") \
        .add_timestamp("product_discontinued_at") \
        .add_metadata_columns() \
        .build()


def get_order_items_silver_schema() -> StructType:
    """Standard schema for order items silver layer table."""
    return SilverSchemaBuilder() \
        .add_business_key("order_item_id", StringType(), nullable=False) \
        .add_business_key("order_id", StringType(), nullable=False) \
        .add_business_key("product_id", StringType(), nullable=False) \
        .add_count("order_item_quantity", nullable=False) \
        .add_amount("order_item_unit_price", nullable=False) \
        .add_amount("order_item_discount_amount") \
        .add_amount("order_item_tax_amount") \
        .add_amount("order_item_subtotal_amount") \
        .add_amount("order_item_total_amount") \
        .add_attribute("product_name", StringType()) \
        .add_attribute("product_category", StringType()) \
        .add_attribute("product_subcategory", StringType()) \
        .add_attribute("product_brand", StringType()) \
        .add_attribute("product_sku", StringType()) \
        .add_amount("product_cost_amount") \
        .add_amount("product_list_price_amount") \
        .add_rate("order_item_margin_rate") \
        .add_amount("order_item_margin_amount") \
        .add_boolean_flag("has_discount") \
        .add_boolean_flag("is_discounted_from_list") \
        .add_metadata_columns(include_scd=False) \
        .build()


# ============================================================================
# Schema Validation Utilities
# ============================================================================

def validate_silver_schema(schema: StructType) -> dict:
    """
    Validate that a schema meets silver layer standards.
    
    Returns:
        Dictionary with validation results
    """
    issues = []
    warnings = []
    
    # Check for required metadata columns
    required_metadata = [
        "record_created_at", "record_updated_at", "source_system",
        "load_id", "is_current", "is_deleted"
    ]
    
    column_names = [field.name for field in schema.fields]
    
    for col in required_metadata:
        if col not in column_names:
            issues.append(f"Missing required metadata column: {col}")
    
    # Check column naming conventions
    for field in schema.fields:
        col = field.name
        
        # Should be snake_case
        if col != col.lower():
            issues.append(f"Column '{col}' is not in snake_case")
        
        # Should not start with underscore
        if col.startswith('_'):
            issues.append(f"Column '{col}' should not start with underscore")
        
        # Boolean columns should have is_/has_ prefix
        if isinstance(field.dataType, BooleanType):
            if not (col.startswith('is_') or col.startswith('has_')):
                warnings.append(f"Boolean column '{col}' should start with 'is_' or 'has_'")
        
        # Timestamp columns should end with _at or _date
        if isinstance(field.dataType, TimestampType):
            if not (col.endswith('_at') or col.endswith('_date')):
                warnings.append(f"Timestamp column '{col}' should end with '_at' or '_date'")
        
        # Amount columns should use DecimalType
        if col.endswith('_amount'):
            if not isinstance(field.dataType, DecimalType):
                warnings.append(f"Amount column '{col}' should use DecimalType")
    
    # Check for SCD Type 2 columns
    scd_columns = ["effective_start_date", "effective_end_date"]
    has_scd = all(col in column_names for col in scd_columns)
    
    if not has_scd:
        warnings.append("Schema does not include SCD Type 2 columns (effective_start_date, effective_end_date)")
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "has_scd_type2": has_scd,
        "column_count": len(schema.fields)
    }


def print_schema_validation_report(validation_result: dict):
    """Print a formatted validation report."""
    print("=" * 60)
    print("SCHEMA VALIDATION REPORT")
    print("=" * 60)
    print(f"\nStatus: {'✅ VALID' if validation_result['is_valid'] else '❌ INVALID'}")
    print(f"Total Columns: {validation_result['column_count']}")
    print(f"SCD Type 2: {'Yes' if validation_result['has_scd_type2'] else 'No'}")
    
    if validation_result['issues']:
        print(f"\n❌ Issues ({len(validation_result['issues'])}):")
        for issue in validation_result['issues']:
            print(f"  - {issue}")
    else:
        print("\n✅ No issues found")
    
    if validation_result['warnings']:
        print(f"\n⚠️  Warnings ({len(validation_result['warnings'])}):")
        for warning in validation_result['warnings']:
            print(f"  - {warning}")
    else:
        print("\n✅ No warnings")
    
    print("=" * 60)


# Example usage
if __name__ == "__main__":
    # Create a custom schema
    custom_schema = SilverSchemaBuilder() \
        .add_business_key("account_id", StringType(), nullable=False) \
        .add_attribute("account_name", StringType()) \
        .add_amount("account_balance_amount") \
        .add_boolean_flag("is_active") \
        .add_timestamp("account_created_at") \
        .add_metadata_columns() \
        .build()
    
    print("Custom Schema:")
    custom_schema.printTreeString()
    
    # Validate the schema
    validation = validate_silver_schema(custom_schema)
    print_schema_validation_report(validation)
    
    print("\n" + "=" * 60 + "\n")
    
    # Get and validate a pre-built schema
    customer_schema = get_customer_silver_schema()
    print("Customer Silver Schema:")
    customer_schema.printTreeString()
    
    validation = validate_silver_schema(customer_schema)
    print_schema_validation_report(validation)

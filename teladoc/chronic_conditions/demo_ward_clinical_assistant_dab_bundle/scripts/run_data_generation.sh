#!/bin/bash
# Script to run data generation workflow
# This will generate synthetic data and run SQL transformations

set -e

echo "=========================================="
echo "Running Data Generation Workflow"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "databricks.yml" ]; then
    echo "❌ Error: databricks.yml not found. Please run this from the bundle root directory."
    exit 1
fi

# Check if bundle is deployed
echo "Checking bundle status..."
if ! databricks bundle validate > /dev/null 2>&1; then
    echo "⚠️  Bundle validation failed. Deploying bundle first..."
    databricks bundle deploy
fi

echo ""
echo "Running data generation workflow..."
echo "This will:"
echo "  1. Generate synthetic patient data"
echo "  2. Run SQL transformations (bronze → silver → gold)"
echo "  3. Deploy agent bricks"
echo ""

# Run the workflow
databricks bundle run demo_workflow

echo ""
echo "=========================================="
echo "✅ Data generation workflow completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  - Check the Databricks UI for generated tables"
echo "  - View the dashboard: Chronic Care Ops & Risk Monitoring"
echo "  - Access the app: Clinical Assistant"
echo ""


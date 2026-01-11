#!/bin/bash
# Patient Readmission DAB - Deployment Script
# Prerequisites: Databricks CLI installed and configured

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BUNDLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-dev}"  # Default to dev if not specified

echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}Patient Readmission DAB Deployment${NC}"
echo -e "${GREEN}Target Environment: ${TARGET}${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Databricks CLI
if ! command -v databricks &> /dev/null; then
    echo -e "${RED}✗ Databricks CLI not found${NC}"
    echo "Install with: pip install databricks-cli"
    exit 1
fi
echo -e "${GREEN}✓ Databricks CLI installed${NC}"

# Check authentication
if ! databricks current-user me &> /dev/null; then
    echo -e "${RED}✗ Databricks CLI not authenticated${NC}"
    echo "Configure with: databricks configure"
    exit 1
fi
CURRENT_USER=$(databricks current-user me --output json | python3 -c "import sys, json; print(json.load(sys.stdin)['userName'])")
echo -e "${GREEN}✓ Authenticated as: ${CURRENT_USER}${NC}"
echo ""

# Step 1: Validate bundle
echo -e "${YELLOW}Step 1: Validating bundle configuration...${NC}"
cd "$BUNDLE_DIR"

if databricks bundle validate -t "$TARGET"; then
    echo -e "${GREEN}✓ Bundle configuration valid${NC}"
else
    echo -e "${RED}✗ Bundle validation failed${NC}"
    exit 1
fi
echo ""

# Step 2: Create catalog if needed
echo -e "${YELLOW}Step 2: Ensuring catalog exists...${NC}"
cat <<EOF | databricks sql --catalog chn_etl_demo_catalog || true
CREATE CATALOG IF NOT EXISTS chn_etl_demo_catalog
COMMENT 'CHN ETL Demo - Main catalog for all projects';
EOF
echo -e "${GREEN}✓ Catalog verified${NC}"
echo ""

# Step 3: Deploy bundle
echo -e "${YELLOW}Step 3: Deploying bundle resources...${NC}"
if databricks bundle deploy -t "$TARGET" --force-lock; then
    echo -e "${GREEN}✓ Bundle deployed successfully${NC}"
else
    echo -e "${RED}✗ Bundle deployment failed${NC}"
    exit 1
fi
echo ""

# Step 4: Get job information
echo -e "${YELLOW}Step 4: Retrieving job information...${NC}"
JOB_INFO=$(databricks bundle run patient_readmission_pipeline -t "$TARGET" --no-wait --output json)
JOB_ID=$(echo "$JOB_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', 'N/A'))")
RUN_ID=$(echo "$JOB_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('run_id', 'N/A'))")

echo -e "${GREEN}✓ Job submitted${NC}"
echo "  Job ID: $JOB_ID"
echo "  Run ID: $RUN_ID"
echo ""

# Step 5: Deployment summary
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""
echo "Resources created:"
echo "  • Catalog: chn_etl_demo_catalog"
echo "  • Schema: patient_readmission_${TARGET}"
echo "  • Volume: raw_data"
echo "  • Job: [${TARGET}] Patient Readmission Pipeline (ID: $JOB_ID)"
echo "  • Dashboard: [${TARGET}] ER Staffing, Access, Quality & Financial Risk"
echo ""
echo "Next steps:"
echo "  1. Monitor job execution:"
echo "     databricks jobs get-run --run-id $RUN_ID"
echo ""
echo "  2. View workspace:"
echo "     https://fe-sandbox-chn-etl-demo.cloud.databricks.com"
echo ""
echo "  3. Query data:"
echo "     SELECT * FROM chn_etl_demo_catalog.patient_readmission_${TARGET}.gold_er_quality_daily LIMIT 10;"
echo ""
echo "  4. See deployment guide:"
echo "     cat ${BUNDLE_DIR}/DEPLOYMENT.md"
echo ""

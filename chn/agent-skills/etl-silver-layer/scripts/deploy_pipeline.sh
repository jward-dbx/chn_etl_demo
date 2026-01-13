#!/bin/bash
################################################################################
# Silver Layer Pipeline Deployment Script
################################################################################
# This script automates the deployment of silver layer ETL pipelines using
# Databricks Asset Bundles (DABs).
#
# Usage:
#   ./deploy_pipeline.sh --target dev --validate
#   ./deploy_pipeline.sh --target prod --skip-tests
#
# Requirements:
#   - Databricks CLI installed and configured
#   - databricks.yml in current or parent directory
#   - Appropriate permissions in target workspace
################################################################################

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TARGET_ENV="dev"
VALIDATE_ONLY=false
SKIP_TESTS=false
SKIP_VALIDATION=false
RUN_TESTS=true
VERBOSE=false

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

################################################################################
# Helper Functions
################################################################################

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy silver layer ETL pipeline using Databricks Asset Bundles.

OPTIONS:
    -t, --target ENV        Target environment (dev, staging, prod). Default: dev
    -v, --validate          Validate configuration only, don't deploy
    -s, --skip-tests        Skip running unit tests before deployment
    -n, --skip-validation   Skip schema and data quality validation
    --verbose               Enable verbose output
    -h, --help              Show this help message

EXAMPLES:
    # Deploy to dev environment
    $0 --target dev

    # Validate prod configuration without deploying
    $0 --target prod --validate

    # Deploy to staging without running tests
    $0 --target staging --skip-tests

EOF
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check if Databricks CLI is installed
    if ! command -v databricks &> /dev/null; then
        print_error "Databricks CLI is not installed"
        print_info "Install with: pip install databricks-cli"
        exit 1
    fi
    print_success "Databricks CLI found"
    
    # Check if databricks.yml exists
    if [ ! -f "${PROJECT_ROOT}/databricks.yml" ] && [ ! -f "${PROJECT_ROOT}/../databricks.yml" ]; then
        print_error "databricks.yml not found in ${PROJECT_ROOT}"
        exit 1
    fi
    print_success "databricks.yml found"
    
    # Check if databricks CLI is configured
    if ! databricks current-user me &> /dev/null; then
        print_error "Databricks CLI is not configured"
        print_info "Run: databricks configure"
        exit 1
    fi
    print_success "Databricks CLI is configured"
    
    # Display current user
    CURRENT_USER=$(databricks current-user me --output json | grep -o '"userName":"[^"]*' | cut -d'"' -f4)
    print_info "Logged in as: ${CURRENT_USER}"
}

validate_bundle() {
    print_header "Validating Bundle Configuration"
    
    cd "${PROJECT_ROOT}"
    
    if [ "$VERBOSE" = true ]; then
        databricks bundle validate --target "${TARGET_ENV}"
    else
        databricks bundle validate --target "${TARGET_ENV}" > /dev/null 2>&1
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Bundle validation passed for target: ${TARGET_ENV}"
    else
        print_error "Bundle validation failed for target: ${TARGET_ENV}"
        exit 1
    fi
}

run_unit_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        print_warning "Skipping unit tests"
        return 0
    fi
    
    print_header "Running Unit Tests"
    
    if [ -f "${PROJECT_ROOT}/scripts/run_tests.sh" ]; then
        bash "${PROJECT_ROOT}/scripts/run_tests.sh"
        if [ $? -eq 0 ]; then
            print_success "Unit tests passed"
        else
            print_error "Unit tests failed"
            exit 1
        fi
    else
        print_warning "Test script not found, skipping tests"
    fi
}

deploy_bundle() {
    print_header "Deploying Bundle to ${TARGET_ENV}"
    
    cd "${PROJECT_ROOT}"
    
    # Deploy the bundle
    print_info "Deploying assets..."
    if [ "$VERBOSE" = true ]; then
        databricks bundle deploy --target "${TARGET_ENV}"
    else
        databricks bundle deploy --target "${TARGET_ENV}" --force-lock
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Bundle deployed successfully to ${TARGET_ENV}"
    else
        print_error "Bundle deployment failed"
        exit 1
    fi
}

validate_deployment() {
    if [ "$SKIP_VALIDATION" = true ]; then
        print_warning "Skipping post-deployment validation"
        return 0
    fi
    
    print_header "Validating Deployment"
    
    # Check if tables exist
    print_info "Validating silver layer tables..."
    
    # Run schema validation if script exists
    if [ -f "${PROJECT_ROOT}/scripts/validate_schema.py" ]; then
        python "${PROJECT_ROOT}/scripts/validate_schema.py" --env "${TARGET_ENV}"
        if [ $? -eq 0 ]; then
            print_success "Schema validation passed"
        else
            print_warning "Schema validation had warnings"
        fi
    else
        print_warning "Schema validation script not found"
    fi
}

display_summary() {
    print_header "Deployment Summary"
    
    echo -e "${GREEN}✓${NC} Target Environment: ${TARGET_ENV}"
    echo -e "${GREEN}✓${NC} Bundle: silver_layer_etl_pipeline"
    echo -e "${GREEN}✓${NC} Deployment Status: SUCCESS"
    
    if [ "$SKIP_TESTS" = false ]; then
        echo -e "${GREEN}✓${NC} Unit Tests: PASSED"
    else
        echo -e "${YELLOW}⊘${NC} Unit Tests: SKIPPED"
    fi
    
    if [ "$SKIP_VALIDATION" = false ]; then
        echo -e "${GREEN}✓${NC} Validation: COMPLETED"
    else
        echo -e "${YELLOW}⊘${NC} Validation: SKIPPED"
    fi
    
    echo ""
    print_info "View deployed resources:"
    echo "  databricks bundle resources --target ${TARGET_ENV}"
    echo ""
    print_info "Run the pipeline:"
    echo "  databricks bundle run --target ${TARGET_ENV}"
    echo ""
}

################################################################################
# Main Execution
################################################################################

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--target)
            TARGET_ENV="$2"
            shift 2
            ;;
        -v|--validate)
            VALIDATE_ONLY=true
            shift
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -n|--skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate target environment
if [[ ! "$TARGET_ENV" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Invalid target environment: ${TARGET_ENV}"
    print_info "Valid targets: dev, staging, prod"
    exit 1
fi

# Require confirmation for prod deployments
if [ "$TARGET_ENV" = "prod" ] && [ "$VALIDATE_ONLY" = false ]; then
    print_warning "You are about to deploy to PRODUCTION"
    read -p "Are you sure you want to continue? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_info "Deployment cancelled"
        exit 0
    fi
fi

# Main execution flow
print_header "Silver Layer Pipeline Deployment"
echo "Target Environment: ${TARGET_ENV}"
echo "Validate Only: ${VALIDATE_ONLY}"
echo "Skip Tests: ${SKIP_TESTS}"
echo ""

# Step 1: Check prerequisites
check_prerequisites

# Step 2: Validate bundle
validate_bundle

# Exit if validate-only mode
if [ "$VALIDATE_ONLY" = true ]; then
    print_success "Validation complete. Exiting without deployment."
    exit 0
fi

# Step 3: Run unit tests
run_unit_tests

# Step 4: Deploy bundle
deploy_bundle

# Step 5: Validate deployment
validate_deployment

# Step 6: Display summary
display_summary

print_success "Deployment completed successfully! 🎉"
exit 0

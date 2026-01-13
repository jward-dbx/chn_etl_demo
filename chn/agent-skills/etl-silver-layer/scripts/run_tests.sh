#!/bin/bash
################################################################################
# Silver Layer Unit Test Runner
################################################################################
# This script runs unit tests for silver layer transformations using pytest.
#
# Usage:
#   ./run_tests.sh
#   ./run_tests.sh --coverage
#   ./run_tests.sh --verbose --specific tests/test_customers.py
################################################################################

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
COVERAGE=false
VERBOSE=false
SPECIFIC_TEST=""
COVERAGE_THRESHOLD=80
HTML_REPORT=false

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TEST_DIR="${PROJECT_ROOT}/tests"

################################################################################
# Helper Functions
################################################################################

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
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

Run unit tests for silver layer ETL transformations.

OPTIONS:
    -c, --coverage          Generate coverage report
    -t, --threshold PCT     Coverage threshold percentage (default: 80)
    -s, --specific PATH     Run specific test file or directory
    -v, --verbose           Enable verbose output
    -h, --html-report       Generate HTML coverage report
    --help                  Show this help message

EXAMPLES:
    # Run all tests
    $0

    # Run with coverage report
    $0 --coverage

    # Run specific test file
    $0 --specific tests/test_customers.py

    # Run with verbose output and HTML report
    $0 --verbose --coverage --html-report

EOF
}

check_dependencies() {
    print_header "Checking Dependencies"
    
    # Check if pytest is installed
    if ! python -c "import pytest" 2>/dev/null; then
        print_error "pytest is not installed"
        print_info "Install with: pip install pytest pytest-spark chispa"
        exit 1
    fi
    print_success "pytest found"
    
    # Check if pytest-spark is installed
    if ! python -c "import pytest_spark" 2>/dev/null; then
        print_warning "pytest-spark not installed (recommended)"
        print_info "Install with: pip install pytest-spark"
    else
        print_success "pytest-spark found"
    fi
    
    # Check if coverage is needed and installed
    if [ "$COVERAGE" = true ]; then
        if ! python -c "import coverage" 2>/dev/null; then
            print_error "coverage is not installed"
            print_info "Install with: pip install pytest-cov"
            exit 1
        fi
        print_success "pytest-cov found"
    fi
}

setup_test_environment() {
    print_header "Setting Up Test Environment"
    
    # Set PYTHONPATH to include project root
    export PYTHONPATH="${PROJECT_ROOT}/src:${PROJECT_ROOT}:${PYTHONPATH:-}"
    print_info "PYTHONPATH set to include project source"
    
    # Set Spark environment variables for testing
    export SPARK_LOCAL_IP=127.0.0.1
    export PYSPARK_PYTHON=python
    export PYSPARK_DRIVER_PYTHON=python
    
    # Create test output directory if it doesn't exist
    mkdir -p "${PROJECT_ROOT}/test-results"
    mkdir -p "${PROJECT_ROOT}/coverage-reports"
}

run_tests() {
    print_header "Running Unit Tests"
    
    cd "${PROJECT_ROOT}"
    
    # Build pytest command
    PYTEST_CMD="python -m pytest"
    
    # Add test directory or specific test
    if [ -n "$SPECIFIC_TEST" ]; then
        PYTEST_CMD="${PYTEST_CMD} ${SPECIFIC_TEST}"
    elif [ -d "$TEST_DIR" ]; then
        PYTEST_CMD="${PYTEST_CMD} ${TEST_DIR}"
    else
        print_warning "Test directory not found, using templates for demonstration"
        PYTEST_CMD="${PYTEST_CMD} templates/test_transformations.py"
    fi
    
    # Add verbose flag
    if [ "$VERBOSE" = true ]; then
        PYTEST_CMD="${PYTEST_CMD} -v"
    fi
    
    # Add coverage options
    if [ "$COVERAGE" = true ]; then
        PYTEST_CMD="${PYTEST_CMD} --cov=src --cov-report=term-missing"
        PYTEST_CMD="${PYTEST_CMD} --cov-report=xml:coverage-reports/coverage.xml"
        
        if [ "$HTML_REPORT" = true ]; then
            PYTEST_CMD="${PYTEST_CMD} --cov-report=html:coverage-reports/html"
        fi
        
        PYTEST_CMD="${PYTEST_CMD} --cov-fail-under=${COVERAGE_THRESHOLD}"
    fi
    
    # Add JUnit XML output for CI/CD
    PYTEST_CMD="${PYTEST_CMD} --junitxml=test-results/junit.xml"
    
    # Add color output
    PYTEST_CMD="${PYTEST_CMD} --color=yes"
    
    # Run the tests
    print_info "Executing: ${PYTEST_CMD}"
    echo ""
    
    if eval "${PYTEST_CMD}"; then
        TEST_RESULT=0
        print_success "All tests passed! ✅"
    else
        TEST_RESULT=1
        print_error "Some tests failed ❌"
    fi
    
    return $TEST_RESULT
}

display_coverage_report() {
    if [ "$COVERAGE" = false ]; then
        return 0
    fi
    
    print_header "Coverage Report"
    
    if [ -f "coverage-reports/coverage.xml" ]; then
        print_info "Coverage report saved to: coverage-reports/coverage.xml"
    fi
    
    if [ "$HTML_REPORT" = true ] && [ -d "coverage-reports/html" ]; then
        print_info "HTML coverage report saved to: coverage-reports/html/index.html"
        print_info "Open in browser with:"
        echo "  open coverage-reports/html/index.html  # macOS"
        echo "  xdg-open coverage-reports/html/index.html  # Linux"
    fi
}

display_test_summary() {
    print_header "Test Summary"
    
    if [ -f "test-results/junit.xml" ]; then
        # Parse JUnit XML for summary (basic parsing)
        TOTAL_TESTS=$(grep -o 'tests="[0-9]*"' test-results/junit.xml | head -1 | grep -o '[0-9]*')
        FAILURES=$(grep -o 'failures="[0-9]*"' test-results/junit.xml | head -1 | grep -o '[0-9]*')
        ERRORS=$(grep -o 'errors="[0-9]*"' test-results/junit.xml | head -1 | grep -o '[0-9]*')
        
        if [ -n "$TOTAL_TESTS" ]; then
            echo -e "Total Tests: ${BLUE}${TOTAL_TESTS}${NC}"
            echo -e "Passed: ${GREEN}$((TOTAL_TESTS - FAILURES - ERRORS))${NC}"
            echo -e "Failed: ${RED}${FAILURES}${NC}"
            echo -e "Errors: ${RED}${ERRORS}${NC}"
        fi
    fi
    
    echo ""
    print_info "Test results saved to: test-results/junit.xml"
}

################################################################################
# Main Execution
################################################################################

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -t|--threshold)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        -s|--specific)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--html-report)
            HTML_REPORT=true
            shift
            ;;
        --help)
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

# Main execution flow
print_header "Silver Layer Unit Test Runner"

# Check dependencies
check_dependencies

# Setup environment
setup_test_environment

# Run tests
if run_tests; then
    # Display reports
    display_coverage_report
    display_test_summary
    
    print_success "Testing completed successfully! 🎉"
    exit 0
else
    display_test_summary
    print_error "Testing failed!"
    exit 1
fi

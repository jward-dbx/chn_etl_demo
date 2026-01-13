"""
Pre-process configuration files to substitute environment variables.
This script replaces ${catalog} and ${schema} placeholders with actual values.
"""
import os
import json
import re
from pathlib import Path

def substitute_vars(content: str) -> str:
    """Replace ${var} placeholders with environment variables."""
    catalog = os.getenv('CATALOG', 'chn_etl_demo_catalog')
    schema = os.getenv('SCHEMA', 'patient_readmission_dev')
    
    # Replace placeholders
    content = content.replace('${catalog}', catalog)
    content = content.replace('${schema}', schema)
    
    return content

def process_sql_file(sql_path: Path) -> str:
    """Process SQL file and return substituted content."""
    with open(sql_path, 'r') as f:
        content = f.read()
    return substitute_vars(content)

def process_json_file(json_path: Path) -> dict:
    """Process JSON file and return substituted content."""
    with open(json_path, 'r') as f:
        content = f.read()
    substituted = substitute_vars(content)
    return json.loads(substituted)

if __name__ == '__main__':
    # Get current working directory
    cwd = Path(os.getcwd())
    
    print(f"Processing configuration files in {cwd}")
    print(f"CATALOG: {os.getenv('CATALOG', 'chn_etl_demo_catalog')}")
    print(f"SCHEMA: {os.getenv('SCHEMA', 'patient_readmission_dev')}")
    
    # Process bricks_conf.json
    bricks_conf_path = cwd / 'bricks_conf.json'
    if bricks_conf_path.exists():
        processed_conf = process_json_file(bricks_conf_path)
        with open(bricks_conf_path.with_suffix('.processed.json'), 'w') as f:
            json.dump(processed_conf, f, indent=2)
        print(f"✓ Processed {bricks_conf_path}")
    
    print("Configuration preprocessing complete")

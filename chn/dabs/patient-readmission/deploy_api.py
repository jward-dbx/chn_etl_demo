#!/usr/bin/env python3
"""
Deploy Patient Readmission Pipeline to Databricks via REST API
This script deploys the bundle without requiring the Databricks CLI
"""

import json
import requests
import time
import os
from pathlib import Path

# Configuration - use environment variables for secrets
WORKSPACE_URL = os.getenv("DATABRICKS_HOST", "https://adb-7405607609261208.8.azuredatabricks.net")
TOKEN = os.getenv("DATABRICKS_TOKEN")
CATALOG = os.getenv("CATALOG", "dbx_chn_ward_demo")
SCHEMA = os.getenv("SCHEMA", "patient_readmission_dev")
WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "fbd528ca6ed5f79c")  # cursor warehouse (running)

if not TOKEN:
    raise ValueError("DATABRICKS_TOKEN environment variable must be set")

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def api_request(method, endpoint, data=None):
    """Make API request to Databricks"""
    url = f"{WORKSPACE_URL}/api/2.0{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        
        response.raise_for_status()
        return response.json() if response.text else {}
    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}")
        print(f"Response: {e.response.text}")
        return None

def create_workspace_folder(path):
    """Create workspace folder"""
    data = {"path": path}
    result = api_request("POST", "/workspace/mkdirs", data)
    return result is not None

def upload_file_to_workspace(local_path, workspace_path):
    """Upload a file to Databricks workspace"""
    with open(local_path, 'rb') as f:
        content = f.read()
    
    import base64
    content_b64 = base64.b64encode(content).decode('utf-8')
    
    data = {
        "path": workspace_path,
        "content": content_b64,
        "overwrite": True,
        "format": "AUTO"
    }
    
    result = api_request("POST", "/workspace/import", data)
    return result is not None

def create_job(name, tasks):
    """Create a Databricks job"""
    job_config = {
        "name": name,
        "tasks": tasks,
        "format": "MULTI_TASK",
        "max_concurrent_runs": 1
    }
    
    result = api_request("POST", "/jobs/create", job_config)
    if result and 'job_id' in result:
        print(f"✓ Created job: {name} (ID: {result['job_id']})")
        return result['job_id']
    return None

def run_job(job_id):
    """Trigger a job run"""
    data = {"job_id": job_id}
    result = api_request("POST", "/jobs/run-now", data)
    if result and 'run_id' in result:
        print(f"✓ Started job run (Run ID: {result['run_id']})")
        return result['run_id']
    return None

def main():
    print("=" * 60)
    print("Patient Readmission Pipeline - REST API Deployment")
    print("=" * 60)
    print()
    
    # Step 1: Create workspace folder
    print("Step 1: Creating workspace folder...")
    workspace_base = "/Users/justin.ward@databricks.com/chn_etl_demo/patient_readmission"
    if create_workspace_folder(workspace_base):
        print(f"  ✓ Created folder: {workspace_base}")
    print()
    
    # Step 2: Upload source files
    print("Step 2: Uploading source files to workspace...")
    src_dir = Path("/Users/justin.ward/chn/dabs/patient-readmission/src")
    
    files_to_upload = [
        "generate_data.py",
        "transformations.sql",
        "deploy_resources.py",
        "agent_bricks_service.py",
        "utils.py",
        "bricks_conf.json"
    ]
    
    for filename in files_to_upload:
        local_file = src_dir / filename
        workspace_file = f"{workspace_base}/{filename}"
        if upload_file_to_workspace(local_file, workspace_file):
            print(f"  ✓ Uploaded {filename}")
        else:
            print(f"  ✗ Failed to upload {filename}")
    
    print()
    
    # Step 3: Create job
    print("Step 3: Creating workflow job...")
    
    tasks = [
        {
            "task_key": "generate_data",
            "description": "Generate synthetic ER visit data",
            "spark_python_task": {
                "python_file": f"{workspace_base}/generate_data.py",
                "source": "WORKSPACE",
                "parameters": [
                    "--catalog", CATALOG,
                    "--schema", SCHEMA
                ]
            },
            "timeout_seconds": 3600,
            "environment_key": "default"
        },
        {
            "task_key": "sql_transformations",
            "description": "Execute medallion architecture transformations",
            "depends_on": [{"task_key": "generate_data"}],
            "sql_task": {
                "file": {
                    "path": f"{workspace_base}/transformations.sql"
                },
                "warehouse_id": WAREHOUSE_ID
            },
            "timeout_seconds": 1800
        },
        {
            "task_key": "deploy_resources",
            "description": "Deploy Genie spaces and dashboards",
            "depends_on": [{"task_key": "sql_transformations"}],
            "spark_python_task": {
                "python_file": f"{workspace_base}/deploy_resources.py",
                "source": "WORKSPACE",
                "parameters": [
                    "--catalog", CATALOG,
                    "--schema", SCHEMA
                ]
            },
            "timeout_seconds": 1800,
            "environment_key": "default"
        }
    ]
    
    job_config = {
        "name": "[dev] Patient Readmission Pipeline - API",
        "tasks": tasks,
        "environments": [
            {
                "environment_key": "default",
                "spec": {
                    "client": "1",
                    "dependencies": [
                        "faker>=19.0.0",
                        "pandas>=2.0.0",
                        "numpy>=1.24.0",
                        "databricks-sdk>=0.18.0"
                    ]
                }
            }
        ],
        "format": "MULTI_TASK",
        "max_concurrent_runs": 1
    }
    
    result = api_request("POST", "/jobs/create", job_config)
    if result and 'job_id' in result:
        job_id = result['job_id']
        print(f"✓ Created job: [dev] Patient Readmission Pipeline - API (ID: {job_id})")
    else:
        print("✗ Failed to create job")
        return
    
    print()
    
    # Step 4: Run job
    print("Step 4: Starting pipeline execution...")
    run_id = run_job(job_id)
    
    if run_id:
        print()
        print("=" * 60)
        print("Deployment Complete!")
        print("=" * 60)
        print()
        print(f"Job ID: {job_id}")
        print(f"Run ID: {run_id}")
        print()
        print("Monitor progress at:")
        print(f"{WORKSPACE_URL}/#job/{job_id}/run/{run_id}")
        print()
        print("Expected completion: 10-16 minutes")
    else:
        print("✗ Failed to start job")

if __name__ == "__main__":
    main()

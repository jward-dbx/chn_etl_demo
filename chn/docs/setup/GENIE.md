# 🧞 GENIE SPACE DEPLOYMENT GUIDE

## Project Context

This guide is part of the **OMOP Semantic Layer** project for deploying Genie Spaces that enable natural language querying of OMOP CDM healthcare data.

**Current Implementation:**
- **Workspace**: `fe-sandbox-serverless-rde85f` (vending machine)
- **Source Space**: `omop-semanticlayer` (ID: `01f0e4ce153d10029169af35dcd82266`)
- **Metric Views**: 7 OMOP semantic layer views in `serverless_rde85f_catalog.semantic_omop`
- **Deployment Script**: `resources/genie/deploy_genie_space.py`
- **Exported Configs**: `resources/genie/omop_semantic_layer_*.json`

## OBJECTIVE
This guide walks you through reading an existing Genie space configuration from one Databricks workspace and deploying it to a new workspace. Use this for migrating Genie spaces across environments (dev → prod) or workspaces.

---

## OVERVIEW

**What You'll Learn:**
1. How to retrieve complete Genie space configuration via API
2. Understanding the `serialized_space` structure
3. How to create a new Genie space in a target workspace
4. How to update an existing Genie space

**Prerequisites:**
- Databricks Personal Access Token (PAT) for both source and target workspaces
- Workspace URLs for source and target
- SQL Warehouse ID in target workspace
- Unity Catalog and schema already created in target workspace

---

## PART 1: READING AN EXISTING GENIE SPACE

### Step 1: List All Genie Spaces

**API Endpoint:** `GET /api/2.0/genie/spaces`

**Purpose:** Get a list of all Genie spaces in a workspace to find the space_id you want to migrate.

**Request:**
```bash
curl -X GET \
  "https://[YOUR_SOURCE_WORKSPACE]/api/2.0/genie/spaces" \
  -H "Authorization: Bearer [YOUR_SOURCE_TOKEN]" \
  -H "Content-Type: application/json"
```

**Python Example:**
```python
import requests

source_workspace = "https://your-source-workspace.cloud.databricks.com"
source_token = "dapi..."

url = f"{source_workspace}/api/2.0/genie/spaces"
headers = {
    "Authorization": f"Bearer {source_token}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
response.raise_for_status()

spaces = response.json().get("spaces", [])

# Print all spaces
for space in spaces:
    print(f"Name: {space['display_name']}")
    print(f"ID: {space['space_id']}")
    print(f"Description: {space.get('description', 'N/A')}")
    print()
```

**Response Structure:**
```json
{
  "spaces": [
    {
      "space_id": "01f0ed61506e1f7c9b993c728155babc",
      "display_name": "Glucosphere Genie",
      "description": "Comprehensive analytics for CGM devices...",
      "warehouse_id": "ae4205f7fb0adc98",
      "created_timestamp": 1736467200000,
      "last_updated_timestamp": 1736553600000
    }
  ]
}
```

---

### Step 2: Get Detailed Space Configuration

**API Endpoint:** `GET /api/2.0/genie/spaces/{space_id}`

**Purpose:** Retrieve the complete configuration including the critical `serialized_space` field.

**Request:**
```bash
curl -X GET \
  "https://[YOUR_SOURCE_WORKSPACE]/api/2.0/genie/spaces/[SPACE_ID]" \
  -H "Authorization: Bearer [YOUR_SOURCE_TOKEN]" \
  -H "Content-Type: application/json"
```

**Python Example:**
```python
import requests
import json

space_id = "01f0ed61506e1f7c9b993c728155babc"

url = f"{source_workspace}/api/2.0/genie/spaces/{space_id}"
headers = {
    "Authorization": f"Bearer {source_token}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
response.raise_for_status()

space_config = response.json()

# Save to file for inspection
with open("genie_space_export.json", "w") as f:
    json.dump(space_config, f, indent=2)

print("✓ Genie space configuration exported")
```

**Response Structure:**
```json
{
  "space_id": "01f0ed61506e1f7c9b993c728155babc",
  "display_name": "Glucosphere Genie",
  "description": "Comprehensive analytics for CGM devices...",
  "warehouse_id": "ae4205f7fb0adc98",
  "serialized_space": "{\"version\":1,\"config\":{...},\"data_sources\":{...},\"instructions\":{...}}",
  "created_timestamp": 1736467200000,
  "last_updated_timestamp": 1736553600000,
  "user_id": "1234567890",
  "folder_node_internal_name": "/Workspace/..."
}
```

---

### Step 3: Parse the `serialized_space` Field

**CRITICAL:** The `serialized_space` field contains a **JSON string** (not an object). You must parse it to work with it.

**Python Example:**
```python
import json

# Extract and parse serialized_space
serialized_space_str = space_config.get("serialized_space", "{}")
serialized_space = json.loads(serialized_space_str)

# Now you have the structured configuration
print(f"Version: {serialized_space['version']}")
print(f"Tables: {len(serialized_space['data_sources']['tables'])}")
print(f"Sample Questions: {len(serialized_space['config']['sample_questions'])}")
print(f"Example SQLs: {len(serialized_space['instructions']['example_question_sqls'])}")
print(f"Measures: {len(serialized_space['instructions']['sql_snippets']['measures'])}")
print(f"Dimensions: {len(serialized_space['instructions']['sql_snippets']['dimensions'])}")
```

---

## PART 2: UNDERSTANDING `serialized_space` STRUCTURE

The `serialized_space` is the heart of a Genie space. It defines all the AI behavior.

### Complete Structure

```json
{
  "version": 1,
  "config": {
    "sample_questions": [
      {
        "id": "32_character_hex_uuid_no_hyphens",
        "question": ["What is the average glucose level?"]
      }
    ]
  },
  "data_sources": {
    "tables": [
      {
        "identifier": "catalog.schema.table_name",
        "column_configs": [
          {
            "column_name": "column1",
            "get_example_values": true,
            "build_value_dictionary": false
          }
        ]
      }
    ]
  },
  "instructions": {
    "text_instructions": [
      {
        "id": "32_character_hex_uuid",
        "content": [
          "## Instructions Title\n",
          "Instruction text...\n"
        ]
      }
    ],
    "example_question_sqls": [
      {
        "id": "32_character_hex_uuid",
        "question": ["Question text"],
        "sql": ["SELECT * FROM table\n"]
      }
    ],
    "sql_snippets": {
      "measures": [
        {
          "id": "32_character_hex_uuid",
          "alias": "avg_value",
          "sql": ["AVG(column)"],
          "display_name": "Average Value",
          "instruction": ["WHEN_TO_USE: Calculate average"]
        }
      ],
      "dimensions": [
        {
          "id": "32_character_hex_uuid",
          "alias": "year",
          "sql": ["YEAR(date_column)"],
          "display_name": "Year",
          "instruction": ["WHEN_TO_USE: Extract year from date"]
        }
      ]
    }
  }
}
```

### Key Components Explained

#### 1. **version** (integer)
- Always `1` for current Genie spaces
- Indicates the schema version

#### 2. **config.sample_questions** (array)
- Questions shown to users as suggestions
- Each has a unique UUID and question text array
- **Must be sorted by `id`**

#### 3. **data_sources.tables** (array)
- Tables included in the Genie space
- **Must be sorted alphabetically by `identifier`**
- Each table has column configurations:
  - `column_name`: Name of the column
  - `get_example_values`: Whether to show examples (boolean)
  - `build_value_dictionary`: Build unique value list for categorical columns (boolean)
- **Column configs must be sorted alphabetically by `column_name`**

#### 4. **instructions.text_instructions** (array)
- Free-form text guidance for the AI
- Markdown formatted
- Use for: data definitions, business rules, best practices

#### 5. **instructions.example_question_sqls** (array)
- Example SQL queries that answer specific questions
- Helps AI understand query patterns
- **Must be sorted by `id`**

#### 6. **instructions.sql_snippets.measures** (array)
- Reusable aggregation expressions (AVG, SUM, COUNT, etc.)
- Each has alias, SQL, display name, and usage instructions
- **Must be sorted by `id`**

#### 7. **instructions.sql_snippets.dimensions** (array)
- Reusable calculated columns (YEAR(date), CONCAT(), etc.)
- Same structure as measures
- **Must be sorted by `id`**

---

## PART 3: MODIFYING FOR TARGET WORKSPACE

### Step 1: Update Catalog and Schema References

**CRITICAL:** Replace all catalog.schema references in the `serialized_space` to match your target workspace.

**Python Example:**
```python
import json

# Load exported config
with open("genie_space_export.json", "r") as f:
    space_config = json.load(f)

# Parse serialized_space
serialized_space = json.loads(space_config["serialized_space"])

# Define source and target
source_catalog = "hls_glucosphere"
source_schema = "cgm"
target_catalog = "prod_catalog"
target_schema = "analytics"

# Convert to JSON string for replacement
serialized_str = json.dumps(serialized_space)

# Replace all references
serialized_str = serialized_str.replace(
    f"{source_catalog}.{source_schema}",
    f"{target_catalog}.{target_schema}"
)

# Parse back to object
updated_serialized_space = json.loads(serialized_str)

print("✓ Catalog/schema references updated")
```

### Step 2: Verify Table Existence

Before deploying, verify that all tables exist in the target workspace:

```python
# Extract table identifiers
tables = updated_serialized_space["data_sources"]["tables"]
table_identifiers = [t["identifier"] for t in tables]

print("Tables referenced in Genie space:")
for table_id in table_identifiers:
    print(f"  - {table_id}")

print("\n⚠️  Verify these tables exist in your target workspace!")
```

---

## PART 4: DEPLOYING TO TARGET WORKSPACE

### Option A: Create New Genie Space

**API Endpoint:** `POST /api/2.0/genie/spaces`

**Purpose:** Create a brand new Genie space in the target workspace.

**Request:**
```bash
curl -X POST \
  "https://[TARGET_WORKSPACE]/api/2.0/genie/spaces" \
  -H "Authorization: Bearer [TARGET_TOKEN]" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Glucosphere Genie",
    "description": "Comprehensive analytics for CGM devices...",
    "warehouse_id": "[TARGET_WAREHOUSE_ID]",
    "serialized_space": "{\"version\":1,...}"
  }'
```

**Python Example:**
```python
import requests
import json

target_workspace = "https://your-target-workspace.cloud.databricks.com"
target_token = "dapi..."
target_warehouse_id = "your-warehouse-id"

url = f"{target_workspace}/api/2.0/genie/spaces"
headers = {
    "Authorization": f"Bearer {target_token}",
    "Content-Type": "application/json"
}

# Prepare payload
payload = {
    "display_name": space_config["display_name"],
    "description": space_config.get("description", ""),
    "warehouse_id": target_warehouse_id,
    "serialized_space": json.dumps(updated_serialized_space)  # Must be string!
}

response = requests.post(url, headers=headers, json=payload)
response.raise_for_status()

result = response.json()
new_space_id = result.get("space_id")

print(f"✅ Genie space created successfully!")
print(f"Space ID: {new_space_id}")
print(f"URL: {target_workspace}/genie/rooms/{new_space_id}")
```

**Required Fields:**
- `display_name` (string): Name of the Genie space
- `description` (string): Description text
- `warehouse_id` (string): SQL warehouse ID in target workspace
- `serialized_space` (string): JSON string of the configuration

**Response:**
```json
{
  "space_id": "new_space_id_here"
}
```

---

### Option B: Update Existing Genie Space

**API Endpoint:** `PATCH /api/2.0/genie/spaces/{space_id}`

**Purpose:** Update an existing Genie space (useful for iterative updates).

**Request:**
```bash
curl -X PATCH \
  "https://[TARGET_WORKSPACE]/api/2.0/genie/spaces/[EXISTING_SPACE_ID]" \
  -H "Authorization: Bearer [TARGET_TOKEN]" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Glucosphere Genie",
    "description": "Updated description...",
    "warehouse_id": "[TARGET_WAREHOUSE_ID]",
    "serialized_space": "{\"version\":1,...}"
  }'
```

**Python Example:**
```python
import requests
import json

existing_space_id = "space_id_to_update"

url = f"{target_workspace}/api/2.0/genie/spaces/{existing_space_id}"
headers = {
    "Authorization": f"Bearer {target_token}",
    "Content-Type": "application/json"
}

# Prepare payload (note: uses "title" not "display_name" for updates)
payload = {
    "title": space_config["display_name"],
    "description": space_config.get("description", ""),
    "warehouse_id": target_warehouse_id,
    "serialized_space": json.dumps(updated_serialized_space)
}

response = requests.patch(url, headers=headers, json=payload)
response.raise_for_status()

print(f"✅ Genie space updated successfully!")
print(f"Space ID: {existing_space_id}")
print(f"URL: {target_workspace}/genie/rooms/{existing_space_id}")
```

**Note:** Update uses `title` field instead of `display_name`.

---

## PART 5: COMPLETE MIGRATION SCRIPT

Here's a complete Python script to migrate a Genie space from source to target:

```python
#!/usr/bin/env python3
"""
Genie Space Migration Script
Migrates a Genie space from source workspace to target workspace.
"""
import requests
import json
import argparse


def get_genie_space(workspace_url, token, space_id):
    """Retrieve Genie space configuration."""
    url = f"{workspace_url}/api/2.0/genie/spaces/{space_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()


def update_catalog_references(serialized_space, source_catalog, source_schema, 
                               target_catalog, target_schema):
    """Update catalog and schema references in serialized_space."""
    # Convert to string for replacement
    serialized_str = json.dumps(serialized_space)
    
    # Replace references
    serialized_str = serialized_str.replace(
        f"{source_catalog}.{source_schema}",
        f"{target_catalog}.{target_schema}"
    )
    
    # Parse back to object
    return json.loads(serialized_str)


def create_genie_space(workspace_url, token, display_name, description, 
                       warehouse_id, serialized_space):
    """Create a new Genie space."""
    url = f"{workspace_url}/api/2.0/genie/spaces"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "display_name": display_name,
        "description": description,
        "warehouse_id": warehouse_id,
        "serialized_space": json.dumps(serialized_space)
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    return response.json()


def migrate_genie_space(source_workspace, source_token, source_space_id,
                        target_workspace, target_token, target_warehouse_id,
                        source_catalog, source_schema, 
                        target_catalog, target_schema):
    """
    Complete migration workflow.
    
    Args:
        source_workspace: Source workspace URL
        source_token: Source Databricks token
        source_space_id: Source Genie space ID
        target_workspace: Target workspace URL
        target_token: Target Databricks token
        target_warehouse_id: Target SQL warehouse ID
        source_catalog: Source catalog name
        source_schema: Source schema name
        target_catalog: Target catalog name
        target_schema: Target schema name
    """
    print("=" * 70)
    print("GENIE SPACE MIGRATION")
    print("=" * 70)
    
    # Step 1: Get source space
    print("\n[1/4] Retrieving source Genie space...")
    space_config = get_genie_space(source_workspace, source_token, source_space_id)
    print(f"  ✓ Retrieved: {space_config['display_name']}")
    
    # Step 2: Parse serialized_space
    print("\n[2/4] Parsing configuration...")
    serialized_space = json.loads(space_config["serialized_space"])
    
    tables = serialized_space["data_sources"]["tables"]
    questions = serialized_space["config"]["sample_questions"]
    measures = serialized_space["instructions"]["sql_snippets"]["measures"]
    
    print(f"  ✓ Tables: {len(tables)}")
    print(f"  ✓ Sample Questions: {len(questions)}")
    print(f"  ✓ Measures: {len(measures)}")
    
    # Step 3: Update references
    print("\n[3/4] Updating catalog/schema references...")
    print(f"  Source: {source_catalog}.{source_schema}")
    print(f"  Target: {target_catalog}.{target_schema}")
    
    updated_serialized_space = update_catalog_references(
        serialized_space,
        source_catalog, source_schema,
        target_catalog, target_schema
    )
    print("  ✓ References updated")
    
    # Step 4: Create in target
    print("\n[4/4] Creating Genie space in target workspace...")
    result = create_genie_space(
        target_workspace, target_token,
        space_config["display_name"],
        space_config.get("description", ""),
        target_warehouse_id,
        updated_serialized_space
    )
    
    new_space_id = result.get("space_id")
    
    print("\n" + "=" * 70)
    print("✅ MIGRATION SUCCESSFUL!")
    print("=" * 70)
    print(f"New Space ID: {new_space_id}")
    print(f"URL: {target_workspace}/genie/rooms/{new_space_id}")
    print("=" * 70)
    
    return new_space_id


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate Genie Space")
    
    # Source workspace
    parser.add_argument("--source-workspace", required=True, 
                        help="Source workspace URL")
    parser.add_argument("--source-token", required=True, 
                        help="Source Databricks token")
    parser.add_argument("--source-space-id", required=True, 
                        help="Source Genie space ID")
    parser.add_argument("--source-catalog", required=True, 
                        help="Source catalog name")
    parser.add_argument("--source-schema", required=True, 
                        help="Source schema name")
    
    # Target workspace
    parser.add_argument("--target-workspace", required=True, 
                        help="Target workspace URL")
    parser.add_argument("--target-token", required=True, 
                        help="Target Databricks token")
    parser.add_argument("--target-warehouse-id", required=True, 
                        help="Target SQL warehouse ID")
    parser.add_argument("--target-catalog", required=True, 
                        help="Target catalog name")
    parser.add_argument("--target-schema", required=True, 
                        help="Target schema name")
    
    args = parser.parse_args()
    
    migrate_genie_space(
        args.source_workspace, args.source_token, args.source_space_id,
        args.target_workspace, args.target_token, args.target_warehouse_id,
        args.source_catalog, args.source_schema,
        args.target_catalog, args.target_schema
    )
```

### Usage Example

```bash
python migrate_genie_space.py \
  --source-workspace "https://source-workspace.cloud.databricks.com" \
  --source-token "dapi_source_token" \
  --source-space-id "01f0ed61506e1f7c9b993c728155babc" \
  --source-catalog "hls_glucosphere" \
  --source-schema "cgm" \
  --target-workspace "https://target-workspace.cloud.databricks.com" \
  --target-token "dapi_target_token" \
  --target-warehouse-id "target_warehouse_id" \
  --target-catalog "prod_catalog" \
  --target-schema "analytics"
```

---

## PART 6: DELETING A GENIE SPACE

**API Endpoint:** `DELETE /api/2.0/genie/spaces/{space_id}`

**Purpose:** Remove a Genie space (useful for cleanup or recreation).

**Request:**
```bash
curl -X DELETE \
  "https://[WORKSPACE_URL]/api/2.0/genie/spaces/[SPACE_ID]" \
  -H "Authorization: Bearer [TOKEN]"
```

**Python Example:**
```python
def delete_genie_space(workspace_url, token, space_id):
    """Delete a Genie space."""
    url = f"{workspace_url}/api/2.0/genie/spaces/{space_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.delete(url, headers=headers)
    
    if response.status_code == 200:
        print(f"✓ Genie space {space_id} deleted")
        return True
    else:
        print(f"✗ Failed to delete: {response.status_code}")
        return False
```

---

## PART 7: VALIDATION & TROUBLESHOOTING

### Pre-Deployment Checklist

Before deploying to target workspace:

- [ ] All referenced tables exist in target catalog/schema
- [ ] Target SQL warehouse is running and accessible
- [ ] Target workspace has Unity Catalog enabled
- [ ] User has CREATE permissions on target workspace
- [ ] Catalog and schema references are correctly updated
- [ ] Token has not expired

### Testing After Deployment

1. **Access the Genie Space:**
   ```
   https://[TARGET_WORKSPACE]/genie/rooms/[NEW_SPACE_ID]
   ```

2. **Test with a Sample Question:**
   - Click one of the sample questions
   - Verify it generates correct SQL
   - Check that results are returned

3. **Test Custom Query:**
   - Ask a natural language question
   - Verify AI understands the data
   - Check SQL is referencing correct tables

### Common Errors

#### Error: "Table does not exist"
**Cause:** Referenced tables not present in target workspace
**Solution:** 
- Verify table names with `SHOW TABLES IN catalog.schema`
- Update `serialized_space` with correct table identifiers
- Ensure data migration is complete

#### Error: "Warehouse not found"
**Cause:** Invalid warehouse_id
**Solution:**
- List warehouses: `GET /api/2.0/sql/warehouses`
- Use correct warehouse ID from target workspace

#### Error: "Invalid serialized_space format"
**Cause:** JSON structure is incorrect or not stringified
**Solution:**
- Ensure `serialized_space` is passed as a **JSON string**, not an object
- Use `json.dumps(serialized_space)` before sending

#### Error: "UUIDs must be sorted"
**Cause:** Lists not sorted by ID field
**Solution:**
- Sort all arrays by `id`: `items.sort(key=lambda x: x["id"])`
- This applies to: sample_questions, example_sqls, measures, dimensions

#### Error: "Tables must be sorted by identifier"
**Cause:** Tables array not alphabetically sorted
**Solution:**
- Sort tables: `tables.sort(key=lambda x: x["identifier"])`

#### Error: "Column configs must be sorted"
**Cause:** Column configs not sorted within each table
**Solution:**
- Sort each table's columns: `table["column_configs"].sort(key=lambda x: x["column_name"])`

---

## PART 8: ADVANCED TOPICS

### Querying a Genie Space

After deployment, you can programmatically query the Genie space:

**API Endpoint:** `POST /api/2.0/genie/spaces/{space_id}/start-conversation`

```python
def query_genie_space(workspace_url, token, space_id, question):
    """Send a natural language question to a Genie space."""
    url = f"{workspace_url}/api/2.0/genie/spaces/{space_id}/start-conversation"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {"content": question}
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    return response.json()

# Example usage
result = query_genie_space(
    workspace_url,
    token,
    space_id,
    "What is the average glucose level by device model?"
)

print(f"SQL Generated: {result['sql']}")
print(f"Results: {result['results']}")
```

### Partial Updates

You can update specific parts of a Genie space without replacing everything:

```python
# Only update sample questions
minimal_update = {
    "version": 1,
    "config": {
        "sample_questions": [
            {"id": generate_uuid(), "question": ["New question?"]}
        ]
    }
}

# Send update
payload = {
    "serialized_space": json.dumps(minimal_update)
}

response = requests.patch(
    f"{workspace_url}/api/2.0/genie/spaces/{space_id}",
    headers=headers,
    json=payload
)
```

---

## PART 9: API REFERENCE SUMMARY

### All Genie Space Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/2.0/genie/spaces` | List all Genie spaces |
| GET | `/api/2.0/genie/spaces/{space_id}` | Get specific space details |
| POST | `/api/2.0/genie/spaces` | Create new Genie space |
| PATCH | `/api/2.0/genie/spaces/{space_id}` | Update existing space |
| DELETE | `/api/2.0/genie/spaces/{space_id}` | Delete a space |
| POST | `/api/2.0/genie/spaces/{space_id}/start-conversation` | Query the space |

### Required Headers (All Requests)

```python
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}
```

### Create vs Update: Field Differences

| Field | Create (POST) | Update (PATCH) |
|-------|---------------|----------------|
| Name | `display_name` | `title` |
| Description | `description` | `description` |
| Warehouse | `warehouse_id` | `warehouse_id` |
| Config | `serialized_space` | `serialized_space` |

---

## ✅ CHECKLIST FOR SUCCESSFUL MIGRATION

### Pre-Migration
- [ ] Identified source Genie space ID
- [ ] Have access tokens for both workspaces
- [ ] Noted source catalog and schema names
- [ ] Created target catalog and schema
- [ ] Migrated/verified all required tables exist in target
- [ ] Have target SQL warehouse ID

### During Migration
- [ ] Successfully retrieved source space config
- [ ] Parsed `serialized_space` JSON string
- [ ] Updated all catalog/schema references
- [ ] Verified all table identifiers are correct
- [ ] Ensured all arrays are properly sorted
- [ ] Stringified `serialized_space` before sending

### Post-Migration
- [ ] New space created with returned space_id
- [ ] Can access space URL in browser
- [ ] Sample questions display correctly
- [ ] Test query returns results
- [ ] SQL references correct catalog/schema
- [ ] All tables are accessible

---

## 📚 ADDITIONAL RESOURCES

- [Databricks Genie API Documentation](https://docs.databricks.com/api/workspace/genie)
- [Unity Catalog Documentation](https://docs.databricks.com/unity-catalog/)
- [SQL Warehouses Documentation](https://docs.databricks.com/sql/admin/sql-warehouses.html)

---

**END OF GUIDE**

This comprehensive guide covers everything needed to read, understand, modify, and deploy Genie spaces across Databricks workspaces. Follow the steps sequentially for a successful migration!
